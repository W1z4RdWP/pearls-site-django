from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Max
from django.views.generic import DetailView, ListView
from django.contrib.auth.models import User
from django.db import transaction, models
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST, require_http_methods
from .forms import CourseForm, LessonForm
from .models import Course, Lesson, UserLessonTrajectory, Trajectory, UserCourseTrajectory, TrajectoryCourse
from myapp.models import UserProgress, UserCourse, QuizResult
from myapp.views import is_admin, is_author_or_admin
import logging
from builder.models import CategoryName
from django.contrib.auth import get_user_model
from django.utils.decorators import method_decorator

logger = logging.getLogger(__name__)
audit_logger = logging.getLogger('audit')

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
        # --- автоапдейт статуса и опыта ---
        if all_completed and not user_trajectory.completed:
            user_trajectory.completed = True
            user_trajectory.save(update_fields=['completed'])
        context['trajectory_progress'] = progress
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
        # --- Блокировка доступа к курсу вне очереди траектории ---
        user = request.user
        if user.is_authenticated:
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
            return redirect('login')
        
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
        
        return redirect('course_detail', slug=course.slug)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request = self.request
        course = self.object
        user = request.user
        
        # Инициализация переменных
        user_course = None
        progress = 0
        completed_lessons = 0
        total_lessons = course.lessons.count()
        next_lesson = None
        all_completed = False
        completed_lessons_ids = None
        trajectory = None
        show_final_quiz = False
        show_completion_animation = False
        exp_earned = None
        
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

                    max_completed_order = UserProgress.objects.filter(
                        user=user,
                        course=course,
                        completed=True,
                        lesson_id__in=lesson_ids
                    ).aggregate(max_order=Max('lesson__order'))['max_order'] or 0

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

                    max_completed_order = UserProgress.objects.filter(
                        user=user,
                        course=course,
                        completed=True
                    ).aggregate(max_order=Max('lesson__order'))['max_order'] or 0

                    next_lesson = Lesson.objects.filter(
                        course=course,
                        order__gt=max_completed_order
                    ).order_by('order').first() or course.lessons.first()
                
                # Вычисляем прогресс
                progress = int((completed_lessons / total_lessons) * 100) if total_lessons > 0 else 0
                all_completed = completed_lessons >= total_lessons

                # Автоматическое завершение курса при выполнении условий
                if user_course.status == 'started' and all_completed:
                    # Если есть финальный тест, проверяем его прохождение
                    if course.final_quiz:
                        quiz_passed = QuizResult.objects.filter(
                            user=user,
                            quiz_title=course.final_quiz.name,
                            passed=True
                        ).exists()
                        if quiz_passed:
                            user_course.status = 'completed'
                            user_course.save()
                    else:
                        # Если теста нет - завершаем автоматически
                        user_course.status = 'completed'
                        user_course.save()

                # Проверка для отображения финального теста
                if course.final_quiz:
                    quiz_passed = QuizResult.objects.filter(
                        user=user,
                        quiz_title=course.final_quiz.name,
                        passed=True
                    ).exists()
                    if quiz_passed:
                        show_final_quiz = True
                elif all_completed:
                    show_final_quiz = True

                # Логика анимации завершения
                if user_course.status == 'completed' and not user_course.course_complete_animation_shown:
                    show_completion_animation = True
                    user_course.course_complete_animation_shown = True
                    user_course.save(update_fields=['course_complete_animation_shown'])
                    # --- вычисляем опыт для модалки ---
                    exp_earned = 150
                    if course.final_quiz:
                        exp_earned = int(exp_earned * 1.1)
            else:
                # Для статуса 'available' используем все уроки курса
                lessons = course.lessons.all()
        else:
            # Для неаутентифицированных пользователей
            lessons = course.lessons.all()

        # Формирование контекста
        context.update({
            'course_author': course.author.username,
            'user_course': user_course,
            'progress': progress,
            'completed_lessons': completed_lessons,
            'completed_lessons_ids': completed_lessons_ids or [],
            'total_lessons': total_lessons,
            'next_lesson': next_lesson,
            'all_completed': all_completed,
            'show_completion_animation': show_completion_animation,
            'exp_earned': exp_earned,
            'lessons': lessons,
            'show_final_quiz': show_final_quiz,
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
        available_courses = []
        completed_courses_list = []
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
                user_courses = UserCourse.objects.filter(user=user).select_related('course')
                available_courses = [
                    uc.course for uc in user_courses 
                    if uc.status in ['available', 'started']
                ]
                completed_courses_list = [
                    uc.course for uc in user_courses 
                    if uc.status == 'completed'
                ]
        context.update({
            'available_courses': available_courses,
            'completed_courses_list': completed_courses_list,
        })
        return context

def lesson_detail(request, course_slug, lesson_id):
    if not request.user.is_authenticated:
        return redirect('login')

    course = get_object_or_404(Course, slug=course_slug)
    lesson = get_object_or_404(Lesson, id=lesson_id, course=course)
    previous_lesson = lesson.get_previous_lesson()
    next_lesson = lesson.get_next_lesson()

    # Проверка доступа к курсу
    user_course = UserCourse.objects.filter(user=request.user, course=course).first()
    if not user_course:
        return redirect('course_detail', slug=course.slug)

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
        trajectory_lessons = trajectory.lessons.all().order_by('order').select_related('course') 
        previous_lesson = trajectory_lessons.filter(
            order__lt=lesson.order
        ).order_by('-order').first()
        next_lesson = trajectory_lessons.filter(
            order__gt=lesson.order
        ).order_by('order').first()
    else:
        previous_lesson = lesson.get_previous_lesson()
        next_lesson = lesson.get_next_lesson()

    # Помечаем урок как просмотренный (но не завершенный)
    UserProgress.objects.get_or_create(
        user=request.user,
        lesson=lesson,
        defaults={'course': course}
    )

    context = {
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
            return redirect('home')
    else:
        form = CourseForm()
    return render(request, 'courses/create_course.html', {'form': form})

@login_required
def create_lesson(request, course_slug):
    course = get_object_or_404(Course, slug=course_slug)
    max_order = course.lessons.aggregate(models.Max('order'))['order__max'] or 0
    if request.method == 'POST':
        form = LessonForm(request.POST, initial={'order': max_order + 1}, hide_order=True)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.course = course
            lesson.order = max_order + 1
            lesson.save()
            return redirect('course_detail', course_slug)
    else:
        form = LessonForm(initial={'order': max_order + 1}, hide_order=True)
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
    existing_lessons = Lesson.objects.all()
    categories = CategoryName.objects.all()
    categories_with_path = [
        {'id': c.id, 'path': get_category_full_path(c)} for c in categories
    ]
    if request.method == 'POST':
        if 'create_new' in request.POST:
            return redirect('create_lesson', course_slug=course.slug)
        elif 'select_existing' in request.POST:
            lesson_id = request.POST.get('lesson_id')
            if lesson_id:
                lesson = get_object_or_404(Lesson, id=lesson_id)
                lesson.course = course
                max_order = course.lessons.aggregate(Max('order'))['order__max'] or 0
                lesson.order = max_order + 1
                lesson.save()
                return redirect('course_detail', slug=course.slug)
        elif 'add_category_lessons' in request.POST:
            category_id = request.POST.get('category_id')
            if category_id:
                lessons = Lesson.objects.filter(category_id=category_id)
                max_order = course.lessons.aggregate(Max('order'))['order__max'] or 0
                for i, lesson in enumerate(lessons, start=1):
                    lesson.course = course
                    lesson.order = max_order + i
                    lesson.save()
                return redirect('course_detail', slug=course.slug)
    return render(request, 'courses/add_lesson.html', {
        'course': course,
        'existing_lessons': existing_lessons,
        'categories': categories,
        'categories_with_path': categories_with_path,
    })


@login_required
@user_passes_test(is_admin, login_url='/')
def delete_course(request, slug):
    course = get_object_or_404(Course, slug=slug)
    if request.method == 'POST':
        course.delete()
        return redirect('home')
    return redirect('course_detail', slug=slug)


@login_required
@user_passes_test(is_admin, login_url='/')
def delete_lesson(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    course_slug = lesson.course.slug
    if request.method == 'POST':
        lesson.delete()
    return redirect('course_detail', course_slug)


@login_required
@user_passes_test(lambda u: is_author_or_admin(u, Course), login_url='/')
def edit_course(request, slug):
    course = get_object_or_404(Course, slug=slug)
    
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            form.save()
            return redirect('course_detail', slug=course.slug)
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
    course = lesson.course
    
    if request.method == 'POST':
        form = LessonForm(request.POST, instance=lesson)
        if form.is_valid():
            form.save()
            return redirect('lesson_detail', course_slug=course.slug, lesson_id=lesson.id)
    else:
        form = LessonForm(instance=lesson)
    
    return render(request, 'courses/edit_lesson.html', {
        'form': form,
        'course': lesson.course,
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
            return redirect('quiz_start', quiz_id=course.final_quiz.id)
        else:
            return redirect('profile')

    # GET-запрос - показываем страницу с подтверждением
    return render(request, 'courses/redir_to_quiz.html', {'course': course})

@require_POST
def complete_lesson(request, course_slug, lesson_id):
    """Отмечает урок как завершенный и начисляет пользователю опыт"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    course = get_object_or_404(Course, slug=course_slug)
    lesson = get_object_or_404(Lesson, id=lesson_id, course=course)
    
    if not UserCourse.objects.filter(user=request.user, course=course).exists():
        return redirect('course_detail', slug=course.slug)
    
    # Получаем траекторию пользователя
    trajectory = UserLessonTrajectory.objects.filter(user=request.user, course=course).first()
    
    # Проверяем, что урок входит в траекторию пользователя (если траектория задана)
    if trajectory and lesson not in trajectory.lessons.all():
        return redirect('course_detail', slug=course.slug)

    # Создаем или обновляем прогресс
    UserProgress.objects.update_or_create(
        user=request.user,
        lesson=lesson,
        defaults={'completed': True, 'course': course}
    )

    # Получаем общее количество уроков для пользователя
    if trajectory:
        total_lessons = trajectory.lessons.count()
        lesson_ids = trajectory.lessons.values_list('id', flat=True)
    else:
        total_lessons = course.lessons.count()
        lesson_ids = course.lessons.values_list('id', flat=True)

    # Считаем ТОЛЬКО уроки из траектории
    completed_lessons = UserProgress.objects.filter(
        user=request.user,
        course=course,
        completed=True,
        lesson_id__in=lesson_ids
    ).count()

    all_completed = completed_lessons >= total_lessons

    user_course = UserCourse.objects.get(user=request.user, course=course)
    
    if all_completed:
        if course.final_quiz:
            return redirect('redir_to_quiz', course_slug=course_slug)
        else:
            user_course.is_completed = True
            user_course.save()
    
    return redirect('course_detail', slug=course.slug)


def complete_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    user_course = UserCourse.objects.get(user=request.user, course=course)
    
    if course.final_quiz:
        quiz_result = QuizResult.objects.filter(
            user=request.user,
            quiz=course.final_quiz,
            passed=True
        ).exists()
        
        if quiz_result:
            user_course.is_completed = True
            user_course.save()
            return redirect('course_detail', slug=course.slug)
        else:
            return redirect('quiz_start', quiz_id=course.final_quiz.id)
    else:
        user_course.is_completed = True
        user_course.save()
        return redirect('course_detail', slug=course.slug)
    

@method_decorator(login_required, name='dispatch')
class UserCourseTrajectoryListView(ListView):
    """
    Список всех траекторий пользователя.
    """
    model = UserCourseTrajectory
    template_name = 'courses/user_course_trajectory_list.html'
    context_object_name = 'user_trajectories'

    def get_queryset(self):
        return UserCourseTrajectory.objects.filter(user=self.request.user).select_related('trajectory')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        return context
    

