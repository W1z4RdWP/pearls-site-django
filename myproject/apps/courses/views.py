from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.db.models import Max
from django.views.generic import DetailView, ListView, TemplateView, View, CreateView
from django.contrib.auth.models import User
from django.db import transaction, models
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.decorators.http import require_POST, require_http_methods
from django.http import JsonResponse, HttpResponse, HttpRequest, HttpResponseForbidden
from django.template.loader import render_to_string
from weasyprint import HTML
from datetime import datetime
from .forms import CourseForm, CourseModalForm, LessonForm, MetricsForm
from .models import Course, Lesson, UserLessonTrajectory, Trajectory, UserCourseTrajectory, TrajectoryCourse, Certificate
from myapp.models import UserProgress, UserCourse, QuizResult
from myapp.views import is_admin, is_author_or_admin
import logging
from builder.models import CategoryName
from django.contrib.auth import get_user_model
from django.utils.decorators import method_decorator
from gamification.utils import award_dascoin_points, award_course_badge, award_trajectory_badge, award_first_lesson_badge
from .utils import issue_certificate, get_user_certificates
from quizzes.models import Quiz




logger = logging.getLogger(__name__)
audit_logger = logging.getLogger('audit')




def auto_unlock_quiz_if_lessons_completed(user, course):
    """
    Автоматически разблокирует финальный тест курса, если пользователь завершил все уроки
    после того как тест был заблокирован.
    """
    if not course.final_quiz:
        return False
    
    from quizzes.models import QuizLock
    quiz_lock = QuizLock.objects.filter(user=user, quiz=course.final_quiz).first()
    
    if quiz_lock and quiz_lock.is_locked:
        quiz_lock.is_locked = False
        quiz_lock.locked_at = None
        quiz_lock.save()
        return True
    
    return False




@method_decorator(login_required, name='dispatch')
class UserCourseTrajectoryDetailView(DetailView):
    """
    Деталка по траектории пользователя: показывает прогресс по курсам в траектории.
    """
    model = UserCourseTrajectory
    template_name = 'courses/user_course_trajectory_detail.html'
    context_object_name = 'user_trajectory'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_trajectory: UserCourseTrajectory = self.object
        trajectory_courses = TrajectoryCourse.objects.filter(trajectory=user_trajectory.trajectory).order_by('order')
        user_courses = {uc.course_id: uc for uc in user_trajectory.user.started_courses.all()}
        progress = []
        all_completed = True
        next_available_course = None
        
        for tc in trajectory_courses:
            uc = user_courses.get(tc.course_id)
            if not (uc and uc.status == 'completed'):
                all_completed = False
            progress.append({
                'course': tc.course,
                'order': tc.order,
                'user_course': uc,
                'available': self._is_course_available(user_trajectory, tc, user_courses)
            })
            
            # Находим первый доступный курс
            if next_available_course is None and self._is_course_available(user_trajectory, tc, user_courses):
                if not uc or uc.status != 'completed':
                    next_available_course = tc.course
        
        # --- автоапдейт статуса и опыта ---
        if all_completed and not user_trajectory.completed:
            user_trajectory.completed = True
            user_trajectory.save(update_fields=['completed'])
            
            # Начисляем DASCOIN за завершение траектории
            award_dascoin_points(user_trajectory.user, 100, f"Завершение траектории {user_trajectory.trajectory.name}")
            
            # Выдаем бейдж за траекторию
            award_trajectory_badge(user_trajectory.user, user_trajectory.trajectory.name)
            
            # Выдаем сертификат за траекторию (если настроено)
            issue_certificate(user_trajectory.user, trajectory=user_trajectory.trajectory)
            
            # Логируем завершение траектории
            audit_logger.info(
                f'Завершил траекторию {user_trajectory.trajectory.name}', 
                extra={'user': user_trajectory.user.username}
            )
        
        context['trajectory_progress'] = progress
        context['next_available_course'] = next_available_course
        return context

    def _is_course_available(self, user_trajectory, tc, user_courses):
        """
        Курс доступен, если он первый в траектории или предыдущий завершён.
        """
        if tc.order == 1:
            return True
        prev_tc = TrajectoryCourse.objects.filter(trajectory=tc.trajectory, order=tc.order-1).first()
        if not prev_tc:
            return True
        prev_uc = user_courses.get(prev_tc.course_id)
        return prev_uc and prev_uc.status == 'completed'




class CourseDetailView(DetailView):
    model = Course
    slug_url_kwarg = 'slug'
    template_name = 'courses/course_detail.html'
    context_object_name = 'course'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        user = request.user
        
        if user.is_authenticated:
            # Проверяем доступ через менеджер
            available_courses = Course.objects.available_for_user(user)
            if self.object not in available_courses:
                return render(request, 'courses/course_access_denied.html', {
                    'course': self.object, 
                    'reason': 'У вас нет доступа к этому курсу.'
                })
            
            # --- Блокировка доступа к курсу вне очереди траектории ---
            user_trajectories = UserCourseTrajectory.objects.filter(user=user, trajectory__courses=self.object)
            for ut in user_trajectories:
                tc = TrajectoryCourse.objects.filter(trajectory=ut.trajectory, course=self.object).first()
                if tc and tc.order > 1:
                    prev_tc = TrajectoryCourse.objects.filter(trajectory=ut.trajectory, order=tc.order-1).first()
                    if prev_tc:
                        from myapp.models import UserCourse
                        prev_uc = UserCourse.objects.filter(user=user, course=prev_tc.course).first()
                        if not prev_uc or prev_uc.status != 'completed':
                            return render(request, 'courses/course_access_denied.html', {'course': self.object, 'reason': 'Курс недоступен. Сначала завершите предыдущий курс в траектории.'})
        return self.render_to_response(self.get_context_data())

    def post(self, request, *args, **kwargs):
        """Обработка начала курса"""
        course = self.get_object()
        user = request.user
        
        if not user.is_authenticated:
            return redirect('users:login')
        
        # Получаем или создаем запись курса
        user_course, created = UserCourse.objects.get_or_create(
            user=user,
            course=course,
            defaults={'status': 'available'}
        )
        
        # Обновляем статус при нажатии кнопки
        if 'start_course' in request.POST and user_course.status == 'available':
            user_course.status = 'started'
            user_course.save()
        
        return redirect('courses:course_detail', slug=course.slug)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request = self.request
        course = self.object
        user = request.user
        
        # Инициализация переменных
        user_course = None
        progress = 0
        completed_lessons = 0
        completed_quizzes = 0
        total_lessons = course.lessons.count()
        total_quizzes = course.quizzes.count()
        total_materials = total_lessons + total_quizzes
        next_lesson = None
        all_completed = False
        completed_lessons_ids = None
        completed_quizzes_ids = None
        trajectory = None
        show_final_quiz = False
        show_completion_animation = False
        
        # Аудит
        audit_logger.info(
            f'Перешёл к курсу {course.title}', 
            extra={'user': user.username if user.is_authenticated else 'Anonymous'}
        )

        if user.is_authenticated:
            user_course = UserCourse.objects.filter(user=user, course=course).first()

            # Если курс начат или завершен
            if user_course and user_course.status in ['started', 'completed']:
                trajectory = UserLessonTrajectory.objects.filter(user=user, course=course).first()
                
                if trajectory:
                    lessons = trajectory.lessons.all()
                    total_lessons = lessons.count()
                    lesson_ids = lessons.values_list('id', flat=True)
                    
                    completed_lessons = UserProgress.objects.filter(
                        user=user,
                        course=course,
                        completed=True,
                        lesson_id__in=lesson_ids
                    ).count()

                    completed_lessons_ids = list(
                        UserProgress.objects.filter(
                            user=user,
                            course=course,
                            completed=True,
                            lesson_id__in=lesson_ids
                        ).values_list('lesson_id', flat=True)
                    )
                    
                    # Получаем пройденные тесты в рамках этого курса
                    completed_quizzes_ids = list(
                        QuizResult.objects.filter(
                            user=user,
                            course=course,
                            quiz_title__in=[quiz.name for quiz in course.quizzes],
                            passed=True
                        ).values_list('quiz_title', flat=True)
                    )
                    completed_quizzes = len(completed_quizzes_ids)

                    max_completed_order = UserProgress.objects.filter(
                        user=user,
                        course=course,
                        completed=True,
                        lesson_id__in=lesson_ids
                    ).select_related('lesson').aggregate(max_order=Max('lesson__order'))['max_order'] or 0

                    next_lesson = Lesson.objects.filter(
                        id__in=lesson_ids,
                        order__gt=max_completed_order
                    ).order_by('order').first() or lessons.first()
                    
                else:
                    lessons = course.lessons.all()
                    completed_lessons = UserProgress.objects.filter(
                        user=user,
                        course=course,
                        completed=True
                    ).count()

                    completed_lessons_ids = list(
                        UserProgress.objects.filter(
                            user=user,
                            course=course,
                            completed=True
                        ).values_list('lesson_id', flat=True)
                    )
                    
                    # Получаем пройденные тесты в рамках этого курса
                    completed_quizzes_ids = list(
                        QuizResult.objects.filter(
                            user=user,
                            course=course,
                            quiz_title__in=[quiz.name for quiz in course.quizzes],
                            passed=True
                        ).values_list('quiz_title', flat=True)
                    )
                    completed_quizzes = len(completed_quizzes_ids)

                    max_completed_order = UserProgress.objects.filter(
                        user=user,
                        course=course,
                        completed=True
                    ).select_related('lesson').aggregate(max_order=Max('lesson__order'))['max_order'] or 0

                    next_lesson = Lesson.objects.filter(
                        courses=course,
                        order__gt=max_completed_order
                    ).order_by('order').first() or course.lessons.first()
                
                # Вычисляем прогресс с учетом уроков и тестов
                completed_materials = completed_lessons + completed_quizzes
                progress = int((completed_materials / total_materials) * 100) if total_materials > 0 else 0
                all_completed = completed_lessons >= total_lessons and completed_quizzes >= total_quizzes

                # Автоматическое завершение курса при выполнении условий
                if user_course.status == 'started' and all_completed:
                    # Если есть финальный тест, проверяем его прохождение в рамках этого курса
                    if course.final_quiz:
                        quiz_passed = QuizResult.objects.filter(
                            user=user,
                            course=course,
                            quiz_title=course.final_quiz.name,
                            passed=True
                        ).exists()
                        if quiz_passed:
                            # Проверяем, был ли курс уже завершен ранее
                            was_completed_before = user_course.status == 'completed'
                            if not was_completed_before:
                                user_course.status = 'completed'
                                user_course.save()
                                
                                # Начисляем очки только если курс только что завершен
                                award_dascoin_points(user, course.points, f"Завершение курса {course.title}")
                                award_course_badge(user, course)
                                # Выдаем сертификат за курс (если настроено)
                                issue_certificate(user, course=course)
                            else:
                                # Курс уже был завершен, просто обновляем статус
                                user_course.status = 'completed'
                                user_course.save()
                        else:
                            # Тест не пройден, но все уроки завершены - автоматически разблокируем тест
                            auto_unlock_quiz_if_lessons_completed(user, course)
                    else:
                        # Если теста нет - завершаем автоматически
                        # Проверяем, был ли курс уже завершен ранее
                        was_completed_before = user_course.status == 'completed'
                        if not was_completed_before:
                            user_course.status = 'completed'
                            user_course.save()
                            
                            # Начисляем очки только если курс только что завершен
                            award_dascoin_points(user, course.points, f"Завершение курса {course.title}")
                            award_course_badge(user, course)
                        else:
                            # Курс уже был завершен, просто обновляем статус
                            user_course.status = 'completed'
                            user_course.save()

                # Проверка для отображения финального теста
                if course.final_quiz:
                    quiz_passed = QuizResult.objects.filter(
                        user=user,
                        course=course,
                        quiz_title=course.final_quiz.name,
                        passed=True
                    ).exists()
                    if quiz_passed:
                        show_final_quiz = True
                    
                    # Получаем информацию о попытках для финального теста в рамках этого курса
                    failed_attempts = QuizResult.objects.filter(
                        user=user,
                        course=course,
                        quiz_title=course.final_quiz.name,
                        passed=False
                    ).count()
                    
                    # Проверяем реальное состояние блокировки теста
                    from quizzes.models import QuizLock
                    quiz_lock = QuizLock.objects.filter(user=user, quiz=course.final_quiz).first()
                    is_actually_locked = quiz_lock.is_locked if quiz_lock else False
                    
                    quiz_attempts_info = {
                        'failed_attempts': failed_attempts,
                        'attempt_limit': course.final_quiz.attempt_limit,
                        'attempts_left': course.final_quiz.attempt_limit - failed_attempts if course.final_quiz.attempt_limit > 0 else None,
                        'is_locked': is_actually_locked
                    }
                elif all_completed:
                    show_final_quiz = True

                # Логика анимации завершения
                if user_course.status == 'completed' and not user_course.course_complete_animation_shown:
                    show_completion_animation = True
                    user_course.course_complete_animation_shown = True
                    user_course.save(update_fields=['course_complete_animation_shown'])
            else:
                # Для статуса 'available' используем все уроки курса
                lessons = course.lessons.all()
        else:
            # Для неаутентифицированных пользователей
            lessons = course.lessons.all()

        # Получение информации о следующем курсе в траектории
        next_course_in_trajectory = None
        user_trajectories_info = []
        if user.is_authenticated:
            # Ищем траектории, в которых есть этот курс
            user_trajectories = UserCourseTrajectory.objects.filter(
                user=user, 
                trajectory__courses=course
            )
            
            for user_trajectory in user_trajectories:
                # Получаем текущий курс в траектории
                current_tc = TrajectoryCourse.objects.filter(
                    trajectory=user_trajectory.trajectory, 
                    course=course
                ).first()
                
                if current_tc:
                    trajectory_info = {
                        'trajectory': user_trajectory.trajectory,
                        'user_trajectory': user_trajectory,
                        'order': current_tc.order,
                        'total_courses': TrajectoryCourse.objects.filter(trajectory=user_trajectory.trajectory).count()
                    }
                    user_trajectories_info.append(trajectory_info)
                    
                    # Ищем следующий курс в траектории только если текущий завершен
                    if user_course and user_course.status == 'completed':
                        next_tc = TrajectoryCourse.objects.filter(
                            trajectory=user_trajectory.trajectory,
                            order=current_tc.order + 1
                        ).first()
                        
                        if next_tc:
                            next_course_in_trajectory = next_tc.course
                            break

        # Формирование контекста
        context.update({
            'course_author': course.author.username,
            'user_course': user_course,
            'progress': progress,
            'completed_lessons': completed_lessons,
            'completed_quizzes': completed_quizzes,
            'completed_lessons_ids': completed_lessons_ids or [],
            'completed_quizzes_ids': completed_quizzes_ids or [],
            'total_lessons': total_lessons,
            'total_quizzes': total_quizzes,
            'total_materials': total_materials,
            'next_lesson': next_lesson,
            'all_completed': all_completed,
            'show_completion_animation': show_completion_animation,
            'lessons': lessons,
            'show_final_quiz': show_final_quiz,
            'next_course_in_trajectory': next_course_in_trajectory,
            'user_trajectories_info': user_trajectories_info,
            'quiz_attempts_info': locals().get('quiz_attempts_info'),
            'quiz_passed': locals().get('quiz_passed', False),
        })
        
        return context



class CourseListView(ListView):
    """
    Отображает все курсы (траектории) доступные пользователю в шаблоне all_courses_list.html.
    Передает в данный шаблон 2 списка с курсами:
    1. Доступные (не пройденные) - статусы 'available' и 'started'
    2. Пройденные (завершенные) - статус 'completed'
    """
    template_name = 'courses/all_courses_list.html'
    context_object_name = 'courses'

    def get_queryset(self):
        # Пустой queryset, так как мы будем использовать get_context_data
        return UserCourse.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        if user.is_authenticated:
            if user.is_staff or user.is_superuser:
                # staff/superuser видят все курсы как доступные
                all_courses = Course.objects.all()
                available_courses = list(all_courses)
                completed_courses_list = [uc.course for uc in UserCourse.objects.filter(user=user, status='completed')]
                # Исключаем завершённые из доступных
                available_courses = [c for c in available_courses if c not in completed_courses_list]
            else:
                # Используем менеджер для получения всех доступных курсов
                all_available_courses = Course.objects.available_for_user(user)
                
                # Получаем статусы курсов пользователя
                user_courses = UserCourse.objects.filter(user=user).select_related('course')
                user_course_statuses = {uc.course_id: uc.status for uc in user_courses}
                
                # Разделяем на доступные и завершенные
                available_courses = []
                completed_courses_list = []
                
                for course in all_available_courses:
                    status = user_course_statuses.get(course.id, 'available')
                    if status == 'completed':
                        completed_courses_list.append(course)
                    else:
                        available_courses.append(course)
        else:
            available_courses = []
            completed_courses_list = []
        
        context.update({
            'available_courses': available_courses,
            'completed_courses_list': completed_courses_list,
        })
        return context



def lesson_detail(request, course_slug, lesson_id):
    if not request.user.is_authenticated:
        return redirect('users:login')

    course = get_object_or_404(Course, slug=course_slug)
    lesson = get_object_or_404(Lesson, id=lesson_id, courses=course)
    previous_lesson = lesson.get_previous_lesson(course)
    next_lesson = lesson.get_next_lesson(course)

    # Проверка доступа к курсу через менеджер
    available_courses = Course.objects.available_for_user(request.user)
    if course not in available_courses:
        return redirect('courses:course_detail', slug=course.slug)
    
    # Получаем UserCourse для проверки статуса
    user_course = UserCourse.objects.filter(user=request.user, course=course).first()
    if not user_course:
        # Создаем UserCourse если его нет (для курсов из траекторий)
        user_course = UserCourse.objects.create(user=request.user, course=course, status='available')

    # Блокируем доступ к уроку, если курс не начат
    if user_course.status not in ['started', 'completed']:
        return render(request, 'courses/lesson_start_required.html', {'course': course, 'lesson': lesson})

    # Проверка траектории
    trajectory = UserLessonTrajectory.objects.filter(user=request.user, course=course).first()
    if trajectory:
        lessons_in_trajectory = trajectory.lessons.all()
        if lesson not in lessons_in_trajectory:
            return render(request, 'courses/lesson_access_denied.html', {'course': course, 'lesson': lesson})
    if trajectory:
        trajectory_lessons = trajectory.lessons.all().order_by('order')
        previous_lesson = trajectory_lessons.filter(
            order__lt=lesson.order
        ).order_by('-order').first()
        next_lesson = trajectory_lessons.filter(
            order__gt=lesson.order
        ).order_by('order').first()
    else:
        previous_lesson = lesson.get_previous_lesson(course)
        next_lesson = lesson.get_next_lesson(course)

    # Помечаем урок как просмотренный (но не завершенный)
    UserProgress.objects.get_or_create(
        user=request.user,
        lesson=lesson,
        defaults={'course': course}
    )

    context = {
        'course': course,
        'lesson': lesson,
        'previous_lesson': previous_lesson,
        'next_lesson': next_lesson,
    }

    if request.GET.get('ajax') == '1':
        from django.template.loader import render_to_string
        html = render_to_string('builder/includes/_lesson_detail_block.html', context, request=request)
        from django.http import HttpResponse
        return HttpResponse(html)
    return render(request, 'courses/lesson_detail.html', context)




@login_required
@user_passes_test(is_admin, login_url='/')
def create_course(request):
    if request.method == 'POST':
        # Проверяем, является ли это AJAX запросом
        is_ajax = (request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 
                  request.headers.get('Accept') == 'application/json')
        
        # Используем разные формы в зависимости от типа запроса
        if is_ajax:
            form = CourseModalForm(request.POST, request.FILES)
        else:
            form = CourseForm(request.POST, request.FILES)
            
        if form.is_valid():
            course = form.save(commit=False)
            course.author = request.user
            course.save()
            form.save_m2m()
            # --- назначаем курс всем staff/superuser ---
            User = get_user_model()
            staff_users = User.objects.filter(is_active=True).filter(models.Q(is_staff=True) | models.Q(is_superuser=True)).distinct()
            from myapp.models import UserCourse
            for user in staff_users:
                UserCourse.objects.get_or_create(user=user, course=course, defaults={'status': 'available'})
            # ---
            if is_ajax:
                return JsonResponse({'success': True, 'id': course.id, 'title': course.title, 'slug': course.slug})
            else:
                return redirect('courses:course_detail', slug=course.slug)
    else:
        # Используем CourseForm для обычных GET запросов
        form = CourseForm()
    return render(request, 'courses/create_course.html', {'form': form})




@login_required
def create_lesson(request, course_slug):
    course = get_object_or_404(Course, slug=course_slug)
    max_order = course.lessons.aggregate(models.Max('order'))['order__max'] or 0
    if request.method == 'POST':
        form = LessonForm(request.POST, initial={'order': max_order + 1, 'courses': [course]}, hide_order=True)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.order = max_order + 1
            lesson.save()
            form.save_m2m()  # Сохраняем связь many-to-many с курсами
            return redirect('courses:course_detail', course_slug)
    else:
        form = LessonForm(initial={'order': max_order + 1, 'courses': [course]}, hide_order=True)
    return render(request, 'courses/create_lesson.html', {'form': form, 'course': course})




def get_category_full_path(category):
    path = [category.name]
    parent = category.parent
    while parent:
        path.append(parent.name)
        parent = parent.parent
    return '/'.join(reversed(path))



@login_required
@user_passes_test(is_admin, login_url='/')
def add_lesson(request, course_slug):
    course = get_object_or_404(Course, slug=course_slug)
    
    # Получаем все категории с их подкатегориями и уроками
    def get_categories_with_lessons():
        categories = CategoryName.objects.filter(parent=None).prefetch_related(
            'subcategories', 'lessons', 'mirrored_lessons__lesson'
        ).order_by('order', 'name')
        
        def process_category(cat):
            # Получаем все уроки категории (включая зеркала)
            lessons = list(cat.lessons.all())
            for mirror in cat.mirrored_lessons.all():
                if mirror.lesson not in lessons:
                    lessons.append(mirror.lesson)
            
            # Обрабатываем подкатегории
            subcategories = []
            for subcat in cat.subcategories.all():
                subcategories.append(process_category(subcat))
            
            return {
                'id': cat.id,
                'name': cat.name,
                'lessons': lessons,
                'subcategories': subcategories
            }
        
        return [process_category(cat) for cat in categories]
    
    # Функция для получения всех уроков категории (включая подкатегории)
    def get_all_lessons_in_category(category_id):
        category = CategoryName.objects.get(id=category_id)
        lessons = set()
        
        # Добавляем уроки текущей категории
        lessons.update(category.lessons.all())
        lessons.update([mirror.lesson for mirror in category.mirrored_lessons.all()])
        
        # Рекурсивно добавляем уроки подкатегорий
        for subcat in category.subcategories.all():
            lessons.update(get_all_lessons_in_category(subcat.id))
        
        return list(lessons)
    
    if request.method == 'POST':
        if 'add_selected' in request.POST:
            selected_items_str = request.POST.get('selected_items', '')
            selected_items = [item.strip() for item in selected_items_str.split(',') if item.strip()]
            max_order = course.lessons.aggregate(Max('order'))['order__max'] or 0
            current_order = max_order + 1
            
            for item_id in selected_items:
                if item_id.startswith('category_'):
                    # Добавляем все уроки из категории (включая подкатегории)
                    category_id = item_id.replace('category_', '')
                    lessons = get_all_lessons_in_category(category_id)
                    
                    for lesson in lessons:
                        # Проверяем, что урок еще не добавлен в курс
                        if course not in lesson.courses.all():
                            lesson.courses.add(course)
                            # Обновляем порядок урока в контексте курса
                            lesson.order = current_order
                            lesson.save()
                            current_order += 1
                            
                elif item_id.startswith('lesson_'):
                    # Добавляем отдельный урок
                    lesson_id = item_id.replace('lesson_', '')
                    lesson = get_object_or_404(Lesson, id=lesson_id)
                    
                    # Проверяем, что урок еще не добавлен в курс
                    if course not in lesson.courses.all():
                        lesson.courses.add(course)
                        # Обновляем порядок урока в контексте курса
                        lesson.order = current_order
                        lesson.save()
                        current_order += 1
                        
                elif item_id.startswith('uncategorized_'):
                    # Добавляем урок без категории
                    lesson_id = item_id.replace('uncategorized_', '')
                    lesson = get_object_or_404(Lesson, id=lesson_id)
                    
                    # Проверяем, что урок еще не добавлен в курс
                    if course not in lesson.courses.all():
                        lesson.courses.add(course)
                        # Обновляем порядок урока в контексте курса
                        lesson.order = current_order
                        lesson.save()
                        current_order += 1
                        
                elif item_id.startswith('quiz_'):
                    # Добавляем тест
                    quiz_id = item_id.replace('quiz_', '')
                    quiz = get_object_or_404(Quiz, id=quiz_id)
                    
                    # Проверяем, что тест еще не добавлен в курс
                    if course not in quiz.courses.all():
                        quiz.courses.add(course)
                        # Устанавливаем порядок теста
                        quiz.order = current_order
                        quiz.save()
                        current_order += 1
            
            return redirect('courses:course_detail', slug=course.slug)
        elif 'create_new' in request.POST:
            return redirect('courses:create_lesson', course_slug=course.slug)
    
    categories_data = get_categories_with_lessons()
    
    # Получаем уроки без категории
    uncategorized_lessons = Lesson.objects.filter(category__isnull=True).order_by('order', 'title')
    
    # Получаем все тесты
    all_quizzes = Quiz.objects.all().order_by('name')
    
    return render(request, 'courses/add_lesson.html', {
        'course': course,
        'categories_data': categories_data,
        'uncategorized_lessons': uncategorized_lessons,
        'all_quizzes': all_quizzes,
    })




@login_required
@user_passes_test(is_admin, login_url='/')
def reorder_materials(request, course_slug):
    """Страница для изменения порядка материалов курса (уроков и тестов)"""
    course = get_object_or_404(Course, slug=course_slug)
    
    if request.method == 'POST':
        # Обработка AJAX запроса для сохранения нового порядка
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            import json
            try:
                data = json.loads(request.body)
                materials_order = data.get('materials_order', [])
                
                # Обновляем порядок для каждого материала
                for index, material_data in enumerate(materials_order):
                    material_type = material_data['type']
                    material_id = material_data['id']
                    new_order = index + 1
                    
                    if material_type == 'lesson':
                        lesson = Lesson.objects.get(id=material_id)
                        lesson.order = new_order
                        lesson.save()
                    elif material_type == 'quiz':
                        quiz = Quiz.objects.get(id=material_id)
                        quiz.order = new_order
                        quiz.save()
                
                return JsonResponse({'success': True})
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
        else:
            # Обычная форма - редирект обратно к курсу
            return redirect('courses:course_detail', slug=course.slug)
    
    # GET запрос - показываем страницу с интерфейсом
    materials = course.get_course_materials()
    
    return render(request, 'courses/reorder_materials.html', {
        'course': course,
        'materials': materials,
    })




@login_required
@user_passes_test(is_admin, login_url='/')
def delete_course(request, slug):
    course = get_object_or_404(Course, slug=slug)
    if request.method == 'POST':
        course.delete()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        return redirect('home')
    return redirect('courses:course_detail', slug=slug)




@login_required
@user_passes_test(is_admin, login_url='/')
def delete_lesson(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    # Получаем первый курс для редиректа (или можно изменить логику)
    course = lesson.courses.first()
    if course and request.method == 'POST':
        # Удаляем связь с курсом, а не сам урок
        lesson.courses.remove(course)
        return redirect('courses:course_detail', course_slug=course.slug)
    elif course:
        return redirect('courses:course_detail', course_slug=course.slug)
    else:
        # Если урок не связан ни с одним курсом, редиректим на главную
        return redirect('home')




@login_required
@user_passes_test(lambda u: is_author_or_admin(u, Course), login_url='/')
def edit_course(request, slug):
    course = get_object_or_404(Course, slug=slug)
    
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            form.save()
            return redirect('courses:course_detail', slug=course.slug)
    else:
        form = CourseForm(instance=course)
    
    return render(request, 'courses/edit_course.html', {
        'form': form,
        'course': course
    })




@login_required
@user_passes_test(is_admin, login_url='/')
def edit_lesson(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    # Получаем первый курс для контекста (или можно изменить логику)
    course = lesson.courses.first()
    
    if request.method == 'POST':
        form = LessonForm(request.POST, instance=lesson)
        if form.is_valid():
            form.save()
            if course:
                return redirect('courses:lesson_detail', course_slug=course.slug, lesson_id=lesson.id)
            else:
                return redirect('home')
    else:
        form = LessonForm(instance=lesson)
    
    return render(request, 'courses/edit_lesson.html', {
        'form': form,
        'course': course,
        'lesson': lesson
    })




@require_http_methods(["GET", "POST"])
def redir_to_quiz(request, course_slug):
    course = get_object_or_404(Course, slug=course_slug)

    if request.method == 'POST':
        # Проверяем, какую кнопку нажал пользователь
        action = request.POST.get('action')
        if action == 'start_quiz':
            request.session['course_slug'] = course.slug
            return redirect('quizzes:quiz_start', quiz_id=course.final_quiz.id)
        else:
            return redirect('users:profile')

    # GET-запрос - показываем страницу с подтверждением
    return render(request, 'courses/redir_to_quiz.html', {'course': course})




@require_POST
def complete_lesson(request, course_slug, lesson_id):
    """Отмечает урок как завершенный и начисляет пользователю опыт"""
    if not request.user.is_authenticated:
        return redirect('users:login')
    
    course = get_object_or_404(Course, slug=course_slug)
    lesson = get_object_or_404(Lesson, id=lesson_id, courses=course)
    user = request.user
    
    # Проверка доступа через менеджер
    available_courses = Course.objects.available_for_user(user)
    if course not in available_courses:
        return redirect('courses:course_detail', slug=course.slug)
    
    # Получаем UserCourse
    user_course = UserCourse.objects.filter(user=user, course=course).first()
    if not user_course:
        user_course = UserCourse.objects.create(user=user, course=course, status='available')
    
    # Получаем траекторию пользователя
    trajectory = UserLessonTrajectory.objects.filter(user=user, course=course).first()
    
    # Проверяем, что урок входит в траекторию пользователя (если траектория задана)
    if trajectory and lesson not in trajectory.lessons.all():
        return redirect('courses:course_detail', slug=course.slug)

    # Проверяем, был ли урок уже завершен ранее
    progress, created = UserProgress.objects.get_or_create(
        user=user,
        lesson=lesson,
        defaults={'completed': False, 'course': course}
    )
    
    # Проверяем, получал ли пользователь уже баллы за этот урок в рамках данного курса
    from gamification.models import DascoinTransaction
    lesson_reward_reason = f"Завершение урока {lesson.title}"
    already_rewarded = DascoinTransaction.objects.filter(
        user=user,
        reason=lesson_reward_reason,
        transaction_type='award'
    ).exists()
    
    # Начисляем очки только если урок завершается впервые И баллы не были начислены ранее
    if not progress.completed and not already_rewarded:
        award_dascoin_points(user, lesson.points, lesson_reward_reason)
    
    # Создаем или обновляем прогресс
    UserProgress.objects.update_or_create(
        user=user,
        lesson=lesson,
        defaults={'completed': True, 'course': course}
    )
    
    # Проверяем и выдаем бейдж "Первый шаг" за первый урок после регистрации
    award_first_lesson_badge(user)

    # Получаем общее количество материалов для пользователя
    if trajectory:
        total_lessons = trajectory.lessons.count()
        lesson_ids = trajectory.lessons.values_list('id', flat=True)
    else:
        total_lessons = course.lessons.count()
        lesson_ids = course.lessons.values_list('id', flat=True)
    
    total_quizzes = course.quizzes.count()

    # Считаем пройденные уроки
    completed_lessons = UserProgress.objects.filter(
        user=user,
        course=course,
        completed=True,
        lesson_id__in=lesson_ids
    ).count()
    
    # Считаем пройденные тесты в рамках этого курса
    completed_quizzes = QuizResult.objects.filter(
        user=user,
        course=course,
        quiz_title__in=[quiz.name for quiz in course.quizzes],
        passed=True
    ).count()

    # Курс завершен только если пройдены ВСЕ уроки И ВСЕ тесты
    all_completed = completed_lessons >= total_lessons and completed_quizzes >= total_quizzes

    user_course = UserCourse.objects.get(user=user, course=course)
    
    if all_completed:
        if course.final_quiz:
            # Автоматически разблокируем финальный тест, если пользователь повторно завершил все уроки
            unlocked = auto_unlock_quiz_if_lessons_completed(user, course)
            if unlocked:
                # Добавляем сообщение о разблокировке
                from django.contrib import messages
                messages.success(
                    request, 
                    f'Отлично! Вы повторно завершили все уроки курса. '
                    f'Финальный тест "{course.final_quiz.name}" разблокирован! Можете пересдать его.'
                )
            
            return redirect('courses:redir_to_quiz', course_slug=course_slug)
        else:
            # Проверяем, был ли курс уже завершен ранее
            was_completed_before = user_course.status == 'completed'
            if not was_completed_before:
                user_course.status = 'completed'
                user_course.save()
                award_dascoin_points(user, course.points, f"Завершение курса {course.title}")
                award_course_badge(user, course)
                # Выдаем сертификат за курс (если настроено)
                issue_certificate(user, course=course)
            else:
                # Курс уже был завершен, просто обновляем статус
                user_course.status = 'completed'
                user_course.save()
    return redirect('courses:course_detail', slug=course.slug)




def complete_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    user_course = UserCourse.objects.get(user=request.user, course=course)
    user = request.user
    
    if course.final_quiz:
        quiz_result = QuizResult.objects.filter(
            user=request.user,
            quiz=course.final_quiz,
            passed=True
        ).exists()
        
        if quiz_result:
            # Проверяем, был ли курс уже завершен ранее
            was_completed_before = user_course.status == 'completed'
            if not was_completed_before:
                user_course.status = 'completed'
                user_course.save()
                award_dascoin_points(user, course.points, f"Завершение курса {course.title}") 
                award_course_badge(user, course)
                # Выдаем сертификат за курс (если настроено)
                issue_certificate(user, course=course)
            else:
                # Курс уже был завершен, просто обновляем статус
                user_course.status = 'completed'
                user_course.save()
            return redirect('courses:course_detail', slug=course.slug)
        else:
            return redirect('quizzes:quiz_start', quiz_id=course.final_quiz.id)
    else:
        # Проверяем, был ли курс уже завершен ранее
        was_completed_before = user_course.status == 'completed'
        if not was_completed_before:
            user_course.status = 'completed'
            user_course.save()
            award_dascoin_points(user, course.points, f"Завершение курса {course.title}") 
            award_course_badge(user, course)
            # Выдаем сертификат за курс (если настроено)
            issue_certificate(user, course=course)
        else:
            # Курс уже был завершен, просто обновляем статус
            user_course.status = 'completed'
            user_course.save()
        return redirect('courses:course_detail', slug=course.slug)
    



@method_decorator(login_required, name='dispatch')
class UserCourseTrajectoryListView(ListView):
    """
    Список всех траекторий пользователя и прогресс по курсам.
    """
    model = UserCourseTrajectory
    template_name = 'courses/user_course_trajectory_list.html'
    context_object_name = 'user_trajectories'

    def get_queryset(self):
        return UserCourseTrajectory.objects.filter(user=self.request.user).select_related('trajectory')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        
        # Получаем прогресс по курсам
        user = self.request.user
        available_courses = Course.objects.available_for_user(user)
        
        # Получаем UserCourse для каждого доступного курса
        user_courses = []
        for course in available_courses:
            user_course = UserCourse.objects.filter(user=user, course=course).first()
            if user_course:
                user_courses.append(user_course)
            else:
                # Создаем UserCourse если его нет (для курсов из траекторий)
                user_course = UserCourse.objects.create(user=user, course=course, status='available')
                user_courses.append(user_course)
        
        # Подготавливаем данные для каждого курса
        courses_data = []
        for user_course in user_courses:
            course = user_course.course
            
            # Подсчет завершенных уроков
            completed_lessons = UserProgress.objects.filter(
                user=user,
                course=course,
                completed=True
            ).count()

            trajectory = UserLessonTrajectory.objects.filter(user=user, course=course).first()
            total_lessons = trajectory.lessons.count() if trajectory else course.lessons.count()
            
            # Подсчет завершенных тестов в рамках этого курса
            completed_quizzes = QuizResult.objects.filter(
                user=user,
                course=course,
                quiz_title__in=[quiz.name for quiz in course.quizzes.all()],
                passed=True
            ).count()
            total_quizzes = course.quizzes.count()
            
            # Общий подсчет материалов
            completed_materials = completed_lessons + completed_quizzes
            total_materials = total_lessons + total_quizzes
            
            # Если у курса нет материалов, считаем его доступным
            if total_materials == 0:
                percent = 0
            else:
                percent = int((completed_materials / total_materials) * 100)

            # Определяем статус курса
            if course.final_quiz:
                quiz_passed = QuizResult.objects.filter(
                    user=user,
                    course=course,
                    quiz_title=course.final_quiz.name,
                    passed=True
                ).exists()
                
                # Курс считается завершенным только если все материалы пройдены И финальный тест пройден
                if total_materials > 0 and completed_materials >= total_materials and quiz_passed:
                    status = 'completed'
                elif completed_materials > 0 or user_course.status in ['started', 'in_progress']:
                    status = 'in_progress'
                else:
                    status = 'available'
            else:
                # Если нет финального теста, курс завершен когда все материалы пройдены
                if total_materials > 0 and completed_materials >= total_materials:
                    status = 'completed'
                elif completed_materials > 0 or user_course.status in ['started', 'in_progress']:
                    status = 'in_progress'
                else:
                    status = 'available'

            course_data = {
                'course': course,
                'user_course': user_course,
                'completed_lessons': completed_lessons,
                'completed_quizzes': completed_quizzes,
                'total_lessons': total_lessons,
                'total_quizzes': total_quizzes,
                'completed_materials': completed_materials,
                'total_materials': total_materials,
                'percent': percent,
                'status': status,
                'quiz_passed': quiz_passed if course.final_quiz else None
            }
            
            courses_data.append(course_data)
        
        # Фильтрация по статусу
        status_filter = self.request.GET.get('status', 'all')
        if status_filter != 'all':
            courses_data = [course for course in courses_data if course['status'] == status_filter]
        
        # Добавляем данные о курсах в контекст
        context.update({
            'courses_data': courses_data,
            'status_filter': status_filter,
            'total_courses': len(courses_data),
            'completed_courses': len([c for c in courses_data if c['status'] == 'completed']),
            'in_progress_courses': len([c for c in courses_data if c['status'] == 'in_progress']),
            'available_courses': len([c for c in courses_data if c['status'] == 'available']),
        })
        
        return context




class TrajectoryCreateView(UserPassesTestMixin, CreateView):
    """
    Создание новой траектории курсов.
    """
    model = Trajectory
    fields = ['name', 'description', 'groups', 'certificate']
    template_name = 'courses/create_trajectory.html'

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    def get_success_url(self):
        return reverse('builder:trajectory_courses', kwargs={'trajectory_id': self.object.id})

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'id': self.object.id, 'name': self.object.name})
        return response




@method_decorator(login_required, name='dispatch')
class CertificateListView(TemplateView):
    """
    Представление для отображения сертификатов пользователя.
    """
    template_name = 'courses/user_certificates.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        certificates = get_user_certificates(self.request.user)
        context.update(certificates)
        return context




class ViewCertificatePdfView(TemplateView):
    template_name = 'courses/certificate_pdf.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        certificate = get_object_or_404(Certificate, certificate_id=kwargs['certificate_id'], user=self.request.user)
        context['certificate'] = certificate
        return context




@login_required
def download_certificate_pdf(request, certificate_id):
    """
    Скачивание сертификата в формате PDF.
    """
    # Получаем сертификат и проверяем права доступа
    certificate = get_object_or_404(Certificate, certificate_id=certificate_id, user=request.user)
    
    # Генерируем HTML из шаблона
    html_string = render_to_string('courses/certificate_pdf.html', {
        'certificate': certificate,
        'generated_at': datetime.now(),
    })
    
    # Создаем PDF с помощью WeasyPrint
    html = HTML(string=html_string)
    pdf = html.write_pdf()
    
    # Формируем имя файла
    if certificate.certificate_type == 'course':
        filename = f"certificate_course_{certificate.course.slug}_{certificate.certificate_id}.pdf"
    else:
        filename = f"certificate_trajectory_{certificate.trajectory.id}_{certificate.certificate_id}.pdf"
    
    # Возвращаем PDF как HttpResponse
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    # Логируем скачивание
    logger.info(
        f'Скачан сертификат {certificate.certificate_id} пользователем {request.user.username}',
        extra={'user': request.user.username, 'certificate_id': certificate.certificate_id}
    )
    
    return response
    



class MetricsFormView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    CBV для формы "передача данных – Метрики эффективности стомклиники"
    Доступ только для пользователей группы "Внешний пользователь" или superuser/is_staff
    """
    template_name = 'courses/metrics_form.html'
    
    def test_func(self):
        """Проверка доступа: superuser/is_staff или группа "Внешний пользователь" """
        user = self.request.user
        if user.is_superuser or user.is_staff:
            return True
        return user.groups.filter(name='Внешний пользователь').exists()
    
    def get(self, request, *args, **kwargs):
        """GET запрос - отображение формы"""
        context = {
            'title': 'передача данных – Метрики эффективности стомклиники'
        }
        return render(request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        """POST запрос - обработка AJAX данных"""
        import json
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON'})
        
        # Сохраняем данные в базу
        from .models import MetricsSubmission
        
        # Извлекаем основные данные
        clinic_name = data.get('clinicName', '')
        initial_month = data.get('startMonth', '')
        doctors_count = int(data.get('docCount', 1))
        chairs_count = int(data.get('chairs', 0))
        work_hours = float(data.get('hoursPerDay', 0))
        
        # Дни в месяце
        days = data.get('days', [])
        
        # Данные врачей
        doctors_data = {
            'doctors': data.get('doctors', []),
            'months': data.get('months', [])
        }
        
        # Создаем запись
        submission = MetricsSubmission.objects.create(
            user=request.user,
            clinic_name=clinic_name,
            initial_month=initial_month,
            doctors_count=doctors_count,
            chairs_count=chairs_count,
            work_hours=work_hours,
            days_month_1=days[0] if len(days) > 0 else 0,
            days_month_2=days[1] if len(days) > 1 else 0,
            days_month_3=days[2] if len(days) > 2 else 0,
            days_month_4=days[3] if len(days) > 3 else 0,
            days_month_5=days[4] if len(days) > 4 else 0,
            days_month_6=days[5] if len(days) > 5 else 0,
            doctors_data=doctors_data
        )
        
        return JsonResponse({'success': True})




class MetricsSuccessView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """
    CBV для страницы успешной отправки формы метрик
    Доступ только для пользователей группы "Внешний пользователь" или superuser/is_staff
    """
    template_name = 'courses/metrics_success.html'
    
    def test_func(self):
        """Проверка доступа: superuser/is_staff или группа "Внешний пользователь" """
        user = self.request.user
        if user.is_superuser or user.is_staff:
            return True
        return user.groups.filter(name='Внешний пользователь').exists()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Форма отправлена успешно'
        return context




class MetricsAdminListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """
    CBV для административной страницы со списком всех заполненных форм метрик (только для superuser)
    """
    template_name = 'courses/metrics_admin_list.html'
    context_object_name = 'submissions'
    
    def test_func(self):
        """Проверка доступа: только superuser"""
        return self.request.user.is_superuser
    
    def get_queryset(self):
        from .models import MetricsSubmission
        return MetricsSubmission.objects.select_related('user').all()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Администрирование форм метрик'
        return context




class MetricsAdminDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """
    CBV для детального просмотра заполненной формы метрик (только для superuser)
    """
    template_name = 'courses/metrics_admin_detail.html'
    context_object_name = 'submission'
    pk_url_kwarg = 'submission_id'
    
    def test_func(self):
        """Проверка доступа: только superuser"""
        return self.request.user.is_superuser
    
    def get_queryset(self):
        from .models import MetricsSubmission
        return MetricsSubmission.objects.all()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Метрики {self.object.clinic_name}'
        return context


@login_required
def export_metrics_to_excel(request, submission_id):
    """
    Экспорт формы метрик в Excel формат согласно шаблону Google Sheets
    """
    # Проверяем права доступа
    if not request.user.is_superuser:
        return HttpResponseForbidden("Доступ запрещен")
    
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
        from openpyxl.utils import get_column_letter
        from django.http import HttpResponse
        from .models import MetricsSubmission
        from datetime import datetime
        import calendar
        
        # Получаем данные формы
        submission = MetricsSubmission.objects.get(id=submission_id)
        
        # Создаем workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "Метрики"
        
        # Определяем стили
        header_font = Font(bold=True, size=11)
        normal_font = Font(size=10)
        fill_yellow = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")
        fill_light_blue = PatternFill(start_color="E6F3FF", end_color="E6F3FF", fill_type="solid")
        
        # Убираем общие границы - будем добавлять только для отдельных таблиц
        # border = Border(
        #     left=Side(border_style="thin"),
        #     right=Side(border_style="thin"),
        #     top=Side(border_style="thin"),
        #     bottom=Side(border_style="thin")
        # )
        
        # Пунктирная граница для таблиц
        dashed_border = Border(
            left=Side(border_style="dashed"),
            right=Side(border_style="dashed"),
            top=Side(border_style="dashed"),
            bottom=Side(border_style="dashed")
        )
        
        # Функция для получения названий месяцев на русском (только первые 3 месяца)
        def get_month_names_ru(initial_month_str):
            year, month = map(int, initial_month_str.split('-'))
            month_names_ru = [
                "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
                "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
            ]
            months = []
            for i in range(3):  # Только первые 3 месяца
                current_month = month + i - 1
                current_year = year
                if current_month >= 12:
                    current_month -= 12
                    current_year += 1
                months.append(f"{month_names_ru[current_month]} {current_year}")
            return months
        
        month_names = get_month_names_ru(submission.initial_month)
        doctors_data = submission.doctors_data.get('doctors', [])
        months_data = submission.doctors_data.get('months', [])
        
        # Заполняем заголовок
        # ws['A1'] = "Правила заполнения:"
        # ws['A1'].font = header_font
        # ws['A2'] = "Ячейки только этого цвета: К ЗАПОЛНЕНИЮ"
        # ws['A2'].fill = fill_yellow
        
        # Основные параметры клиники (строка 4)
        ws['A4'] = "Кол-во кресел, загрузка клиники"
        ws['A4'].font = header_font
        
        # Строка 5 - числовые данные (начинаем с C)
        # Формула: количество кресел * максимальное количество часов работы в день * 30
        ws['A5'] = f"={submission.chairs_count}*{submission.work_hours}*30"
        
        # Загрузка клиники по месяцам (формулы, только первые 3 месяца)
        # Нужно будет добавить формулы после создания итоговых строк
        ws['D5'] = "5%"
        ws['E5'] = "0%"
        ws['F5'] = "0%"
        
        # Строка 6 - заголовки месяцев (начинаем с D)
        ws['A6'] = "Месяц"
        for i, month_name in enumerate(month_names):
            ws[f'{chr(68+i)}6'] = month_name  # D6, E6, F6, etc.
        
        # Строка 7 - заголовок таблицы часов по графику
        ws['A7'] = "Кол-во часов по графику, Т,раб"
        ws['B7'] = "ФИО"
        ws['C7'] = "Специализация"
        
        # Рабочие дни по месяцам в строке 7 (начинаем с D, только первые 3 месяца)
        days_list = [
            submission.days_month_1, submission.days_month_2, submission.days_month_3
        ]
        for i, days in enumerate(days_list):
            ws[f'{chr(68+i)}7'] = days
        
        # Карта специализаций
        spec_map = {
            "hygienist": "Гигиенист",
            "implantologist": "Имплантолог", 
            "orthodontist": "Ортодонт",
            "orthopedist": "Ортопед",
            "periodontist": "Пародонтолог",
            "therapist": "Терапевт",
            "surgeon": "Хирург",
            "therapist_surgeon": "Терапевт-Хирург",
            "orthopedist_surgeon": "Ортопед-Хирург",
            "universal": "Универсал",
            "custom": "Свой вариант"
        }
        
        # Начинаем заполнение данных врачей с 8 строки
        current_row = 8
        schedule_hours_start_row = current_row
        
        # БЛОК 1: Часы по графику (строки 8-26)
        # Используем реальное количество врачей из формы
        max_doctors = len(doctors_data) if doctors_data else 0
        for i in range(max_doctors):
            ws[f'A{current_row}'] = i + 1
            
            if i < len(doctors_data):
                doctor = doctors_data[i]
                ws[f'B{current_row}'] = doctor.get('name', f'ФИО доктора {i+1}')
                ws[f'C{current_row}'] = spec_map.get(doctor.get('specialization', ''), 'заполнить специализацию доктора')
                
                # Часы по графику по месяцам (начинаем с D, только первые 3 месяца)
                for month_idx in range(3):
                    if month_idx < len(months_data) and i < len(months_data[month_idx].get('doctors', [])):
                        schedule_hours = months_data[month_idx]['doctors'][i].get('scheduleHours', 0)
                        ws[f'{chr(68+month_idx)}{current_row}'] = schedule_hours or 0
                    else:
                        ws[f'{chr(68+month_idx)}{current_row}'] = 0
            else:
                ws[f'B{current_row}'] = "ФИО"
                ws[f'C{current_row}'] = "заполнить"
                for month_idx in range(3):
                    ws[f'{chr(68+month_idx)}{current_row}'] = "заполнить"
                    
            current_row += 1
        
        
        # Пропускаем 2 строки
        current_row += 2
        
        # БЛОК 2: Часы с пациентами (строки 29-47)
        ws[f'A{current_row}'] = "Кол-во часов с пациентами, Т,заг"
        ws[f'B{current_row}'] = "ФИО"
        ws[f'C{current_row}'] = "Специализация"
        current_row += 1
        patient_hours_start_row = current_row
        
        for i in range(max_doctors):
            ws[f'A{current_row}'] = i + 1
            
            if i < len(doctors_data):
                doctor = doctors_data[i]
                ws[f'B{current_row}'] = doctor.get('name', f'ФИО доктора {i+1}')
                ws[f'C{current_row}'] = spec_map.get(doctor.get('specialization', ''), 'заполнить специализацию доктора')
                
                # Часы с пациентами по месяцам (начинаем с D)
                for month_idx in range(3):
                    if month_idx < len(months_data) and i < len(months_data[month_idx].get('doctors', [])):
                        patient_hours = months_data[month_idx]['doctors'][i].get('patientHours', 0)
                        ws[f'{chr(68+month_idx)}{current_row}'] = patient_hours or 0
                    else:
                        ws[f'{chr(68+month_idx)}{current_row}'] = 0
            else:
                ws[f'B{current_row}'] = "ФИО"
                ws[f'C{current_row}'] = "заполнить"
                for month_idx in range(3):
                    ws[f'{chr(68+month_idx)}{current_row}'] = "заполнить"
                    
            current_row += 1
        
        # Вычисляем позиции для таблиц
        schedule_table_start = 7
        schedule_table_end = schedule_table_start + max_doctors + 1  # +1 для заголовка
        
        # Вычисляем позиции для таблицы "Часы с пациентами"
        patient_hours_table_start = schedule_table_end + 2 + 1  # +1 для заголовка
        patient_hours_table_end = patient_hours_table_start + max_doctors
        
        # Добавляем суммарные значения для блока 2 (Часы с пациентами) в строку заголовка
        patient_header_row = patient_hours_table_start - 1  # поднимаем на одну строку выше
        for month_idx in range(3):
            # Создаем формулу с операторами плюс для каждой ячейки врача
            cell_formula_parts = []
            for i in range(max_doctors):
                cell_address = f'{chr(68+month_idx)}{patient_hours_start_row + i}'
                cell_formula_parts.append(cell_address)
            formula = f"=({' + '.join(cell_formula_parts)})"
            ws[f'{chr(68+month_idx)}{patient_header_row}'] = formula
        
        # Пропускаем 2 строки
        current_row += 2
        
        # БЛОК 3: Выручка (строки 50-68)
        ws[f'A{current_row}'] = "Выручка, ВВ"
        ws[f'B{current_row}'] = "ФИО"
        ws[f'C{current_row}'] = "Специализация"
        current_row += 1
        revenue_start_row = current_row
        
        for i in range(max_doctors):
            ws[f'A{current_row}'] = i + 1
            
            if i < len(doctors_data):
                doctor = doctors_data[i]
                ws[f'B{current_row}'] = doctor.get('name', f'ФИО доктора {i+1}')
                ws[f'C{current_row}'] = spec_map.get(doctor.get('specialization', ''), 'заполнить специализацию доктора')
                
                # Выручка по месяцам (начинаем с D)
                for month_idx in range(3):
                    if month_idx < len(months_data) and i < len(months_data[month_idx].get('doctors', [])):
                        revenue = months_data[month_idx]['doctors'][i].get('revenue', 0)
                        ws[f'{chr(68+month_idx)}{current_row}'] = revenue or 0
                    else:
                        ws[f'{chr(68+month_idx)}{current_row}'] = 0
            else:
                ws[f'B{current_row}'] = "ФИО"
                ws[f'C{current_row}'] = "заполнить"
                for month_idx in range(3):
                    ws[f'{chr(68+month_idx)}{current_row}'] = "заполнить"
                    
            current_row += 1
        
        # Вычисляем позиции для таблицы "Выручка"
        revenue_table_start = patient_hours_table_end + 2 + 1  # +1 для заголовка
        revenue_table_end = revenue_table_start + max_doctors
        
        # Добавляем суммарные значения для блока 3 (Выручка) в строку заголовка
        revenue_header_row = revenue_table_start - 1  # поднимаем на одну строку выше
        for month_idx in range(3):
            # Создаем формулу с операторами плюс для каждой ячейки врача
            cell_formula_parts = []
            for i in range(max_doctors):
                cell_address = f'{chr(68+month_idx)}{revenue_start_row + i}'
                cell_formula_parts.append(cell_address)
            formula = f"=({' + '.join(cell_formula_parts)})"
            ws[f'{chr(68+month_idx)}{revenue_header_row}'] = formula
        
        # Пропускаем 2 строки
        current_row += 2
        
        # БЛОК 4: Загрузка доктора пациентами (формулы) - строки 73-91
        ws[f'A{current_row}'] = "Загрузка доктора пациентами"
        ws[f'B{current_row}'] = "ФИО"
        ws[f'C{current_row}'] = "Специализация"
        current_row += 1
        
        for i in range(max_doctors):
            ws[f'A{current_row}'] = i + 1
            
            if i < len(doctors_data):
                doctor = doctors_data[i]
                ws[f'B{current_row}'] = doctor.get('name', f'ФИО доктора {i+1}')
                ws[f'C{current_row}'] = spec_map.get(doctor.get('specialization', ''), 'заполнить специализацию доктора')
                
                # Формулы для расчета загрузки (часы с пациентами / часы по графику) (начинаем с D)
                for month_idx in range(3):
                    patient_cell = f'{chr(68+month_idx)}{patient_hours_start_row + i}'
                    schedule_cell = f'{chr(68+month_idx)}{schedule_hours_start_row + i}'
                    ws[f'{chr(68+month_idx)}{current_row}'] = f'=IF({schedule_cell}=0,0,{patient_cell}/{schedule_cell})'
            else:
                ws[f'B{current_row}'] = "ФИО"
                ws[f'C{current_row}'] = "заполнить"
                for month_idx in range(3):
                    ws[f'{chr(68+month_idx)}{current_row}'] = "#VALUE!"
                    
            current_row += 1
        
        
        # Применяем процентный формат к блоку 4 (Загрузка доктора пациентами)
        for i in range(max_doctors):
            row_num = current_row - max_doctors + i
            ws[f'D{row_num}'].number_format = '0%'
            ws[f'E{row_num}'].number_format = '0%'
            ws[f'F{row_num}'].number_format = '0%'
        
        # Пропускаем 2 строки
        current_row += 2
        
        # БЛОК 5: Средний час (формулы) - строки 95-113
        ws[f'A{current_row}'] = "Средний час"
        ws[f'B{current_row}'] = "ФИО"
        ws[f'C{current_row}'] = "Специализация"
        current_row += 1
        
        for i in range(max_doctors):
            ws[f'A{current_row}'] = i + 1
            
            if i < len(doctors_data):
                doctor = doctors_data[i]
                ws[f'B{current_row}'] = doctor.get('name', f'ФИО доктора {i+1}')
                ws[f'C{current_row}'] = spec_map.get(doctor.get('specialization', ''), 'заполнить специализацию доктора')
                
                # Формулы для расчета среднего часа (выручка / часы с пациентами) (начинаем с D)
                for month_idx in range(3):
                    revenue_cell = f'{chr(68+month_idx)}{revenue_start_row + i}'
                    patient_cell = f'{chr(68+month_idx)}{patient_hours_start_row + i}'
                    ws[f'{chr(68+month_idx)}{current_row}'] = f'=IF({patient_cell}=0,0,{revenue_cell}/{patient_cell})'
            else:
                ws[f'B{current_row}'] = "ФИО"
                ws[f'C{current_row}'] = "заполнить"
                for month_idx in range(3):
                    ws[f'{chr(68+month_idx)}{current_row}'] = "#VALUE!"
                    
            current_row += 1
        
        
        # Применяем формат с 2 знаками после запятой к блоку 5 (Средний час)
        for i in range(max_doctors):
            row_num = current_row - max_doctors + i
            ws[f'D{row_num}'].number_format = '0.00'
            ws[f'E{row_num}'].number_format = '0.00'
            ws[f'F{row_num}'].number_format = '0.00'
        
        # Обновляем формулы загрузки клиники по месяцам (только первые 3 месяца)
        for month_idx in range(3):
            # Загрузка клиники = D8+D9+...+DN/A5, где N зависит от количества врачей
            max_hours_cell = 'A5'  # ячейка с максимальными часами
            # Создаем формулу с операторами плюс для каждой ячейки врача
            cell_formula_parts = []
            for i in range(max_doctors):
                cell_address = f'{chr(68+month_idx)}{schedule_hours_start_row + i}'
                cell_formula_parts.append(cell_address)
            formula = f"=({' + '.join(cell_formula_parts)})/{max_hours_cell}"
            ws[f'{chr(68+month_idx)}5'] = formula
        
        # Применяем стили (без границ)
        for row in ws.iter_rows():
            for cell in row:
                # cell.border = border  # Убираем общие границы
                cell.font = normal_font
                cell.alignment = Alignment(horizontal='center', vertical='center')
        
        # Устанавливаем процентный формат для ячеек загрузки клиники
        from openpyxl.styles import NamedStyle
        percentage_style = NamedStyle(name="percentage")
        percentage_style.number_format = '0%'
        
        # Применяем процентный формат к ячейкам D5, E5, F5
        ws['D5'].number_format = '0%'
        ws['E5'].number_format = '0%'
        ws['F5'].number_format = '0%'
        
        # Вычисляем динамические позиции для границ таблиц в зависимости от количества врачей
        
        # 1. Таблица "Кол-во кресел, загрузка клиники" (A6:H7) - фиксированная позиция
        for row in range(6, 8):  # строки 6-7
            for col in range(1, 9):  # колонки A-H
                cell = ws.cell(row=row, column=col)
                cell.border = dashed_border
        
        # 2. Таблица "Кол-во часов по графику" - поднимаем на одну строку выше
        for row in range(schedule_table_start - 1, schedule_table_end + 1):
            for col in range(1, 9):  # колонки A-H
                cell = ws.cell(row=row, column=col)
                cell.border = dashed_border
        
        # 3. Таблица "Кол-во часов с пациентами" - поднимаем на одну строку выше
        for row in range(patient_hours_table_start - 1, patient_hours_table_end + 1):
            for col in range(1, 9):  # колонки A-H
                cell = ws.cell(row=row, column=col)
                cell.border = dashed_border
        
        # 4. Таблица "Выручка" - поднимаем на одну строку выше
        for row in range(revenue_table_start - 1, revenue_table_end + 1):
            for col in range(1, 9):  # колонки A-H
                cell = ws.cell(row=row, column=col)
                cell.border = dashed_border
        
        # 5. Таблица "Загрузка доктора пациентами" - поднимаем на одну строку выше
        load_table_start = revenue_table_end + 2 + 1  # +1 для заголовка
        load_table_end = load_table_start + max_doctors
        for row in range(load_table_start - 1, load_table_end + 1):
            for col in range(1, 9):  # колонки A-H
                cell = ws.cell(row=row, column=col)
                cell.border = dashed_border
        
        # 6. Таблица "Средний час" - поднимаем на одну строку выше
        avg_hour_table_start = load_table_end + 2 + 1  # +1 для заголовка
        avg_hour_table_end = avg_hour_table_start + max_doctors
        for row in range(avg_hour_table_start - 1, avg_hour_table_end + 1):
            for col in range(1, 9):  # колонки A-H
                cell = ws.cell(row=row, column=col)
                cell.border = dashed_border
        
        # Красим ячейки в 7-й строке (кроме A и G) в голубой цвет
        for col in range(2, 9):  # колонки B, C, D, E, F, G, H
            if col != 7:  # пропускаем G (7-я колонка)
                cell = ws.cell(row=7, column=col)
                cell.fill = fill_light_blue
        
        # Красим суммарные ячейки в голубой цвет (динамические позиции)
        # Ячейки для "Часы с пациентами" - в строке заголовка таблицы
        patient_header_row = patient_hours_table_start - 1  # поднимаем на одну строку выше
        for col in range(2, 9):  # колонки B, C, D, E, F, H (пропускаем A и G)
            if col != 7:  # пропускаем G (7-я колонка)
                ws.cell(row=patient_header_row, column=col).fill = fill_light_blue
        
        # Ячейки для "Выручка" - в строке заголовка таблицы
        revenue_header_row = revenue_table_start - 1  # поднимаем на одну строку выше
        for col in range(2, 9):  # колонки B, C, D, E, F, H (пропускаем A и G)
            if col != 7:  # пропускаем G (7-я колонка)
                ws.cell(row=revenue_header_row, column=col).fill = fill_light_blue
        
        # Ячейки для "Загрузка доктора пациентами" - в строке заголовка таблицы
        load_header_row = load_table_start - 1  # поднимаем на одну строку выше
        for col in range(2, 9):  # колонки B, C, D, E, F, H (пропускаем A и G)
            if col != 7:  # пропускаем G (7-я колонка)
                ws.cell(row=load_header_row, column=col).fill = fill_light_blue
        
        # Ячейки для "Средний час" - в строке заголовка таблицы
        avg_hour_header_row = avg_hour_table_start - 1  # поднимаем на одну строку выше
        for col in range(2, 9):  # колонки B, C, D, E, F, H (пропускаем A и G)
            if col != 7:  # пропускаем G (7-я колонка)
                ws.cell(row=avg_hour_header_row, column=col).fill = fill_light_blue
        
        
        # Добавляем формулы для ячеек D7, E7, F7 - сумма часов по графику
        for month_idx in range(3):
            # Создаем формулу с операторами плюс для каждой ячейки врача
            cell_formula_parts = []
            for i in range(max_doctors):
                cell_address = f'{chr(68+month_idx)}{schedule_hours_start_row + i}'
                cell_formula_parts.append(cell_address)
            formula = f"=({' + '.join(cell_formula_parts)})"
            ws[f'{chr(68+month_idx)}7'] = formula

            ws['H7'] = "=(D7+E7+F7)/3"
            ws['H7'].number_format = '0.00'
            
            # Добавляем формулу в ячейку H5: H7/C5 в процентах
            ws['H5'] = "=H7/A5"
            ws['H5'].number_format = '0%'
        

        
        
        # Автоподбор ширины колонок
        for column in ws.columns:
            max_length = 0
            column_letter = get_column_letter(column[0].column)
            for cell in column:
                try:
                    if cell.value and len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max(max_length + 2, 10), 30)
            ws.column_dimensions[column_letter].width = adjusted_width
        
        # Подготавливаем ответ
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        clinic_name_safe = "".join(c for c in submission.clinic_name if c.isalnum() or c in (' ', '-', '_')).strip()
        filename = f"metrics_{clinic_name_safe}_{submission.id}.xlsx"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        wb.save(response)
        return response
        
    except ImportError:
        return HttpResponse("Библиотека openpyxl не установлена. Установите её командой: pip install openpyxl", status=500)
    except MetricsSubmission.DoesNotExist:
        return HttpResponse("Форма метрик не найдена", status=404)
    except Exception as e:
        return HttpResponse(f"Ошибка при создании Excel файла: {str(e)}", status=500)
    
