from django.shortcuts import render, redirect
from django.views.generic import ListView, CreateView, UpdateView, DetailView, FormView
from django.contrib.auth.models import User
from django.db.models import Q, Count, Max
from users.models import Profile, Role
from django import forms
from django.urls import reverse_lazy
from django.core.exceptions import PermissionDenied
from myapp.models import UserProgress, UserCourse, QuizResult, UserAnswer
from courses.models import Course, Lesson, UserLessonTrajectory
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.utils.decorators import method_decorator
from django.contrib.admin.views.decorators import staff_member_required
from .forms import UserProfileForm
from users.forms import UserRegisterNoCaptchaForm
from django.contrib.auth.forms import SetPasswordForm
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.contrib import messages

class UserListView(ListView):
    model = User
    template_name = 'user_management/user_list.html'
    context_object_name = 'users'
    paginate_by = 20

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            raise PermissionDenied("У вас нет доступа к управлению пользователями.")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset().order_by('username')
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(username__icontains=q) |
                Q(email__icontains=q) |
                Q(first_name__icontains=q) |
                Q(last_name__icontains=q)
            )
        filter_val = self.request.GET.get('filter')
        if filter_val == 'approved':
            queryset = queryset.filter(profile__is_approved=True)
        elif filter_val == 'not_approved':
            queryset = queryset.filter(profile__is_approved=False)
        elif filter_val == 'responsible':
            queryset = queryset.filter(profile__is_resonsible=True)
        elif filter_val == 'not_responsible':
            queryset = queryset.filter(profile__is_resonsible=False)
        return queryset


class UserCreateStep1View(CreateView):
    template_name = 'user_management/user_create_step1.html'
    form_class = UserRegisterNoCaptchaForm
    success_url = reverse_lazy('user_management:user_create_step2')

    def form_valid(self, form):
        user = form.save()
        self.request.session['user_create_step1_user_id'] = user.id
        return redirect(self.success_url)

class UserCreateStep2View(CreateView):
    template_name = 'user_management/user_create_step2.html'
    form_class = UserProfileForm
    success_url = reverse_lazy('user_management:user_list')

    def dispatch(self, request, *args, **kwargs):
        if 'user_create_step1_user_id' not in request.session:
            return redirect('user_management:user_create_step1')
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        user_id = self.request.session.get('user_create_step1_user_id')
        user = User.objects.get(id=user_id)
        kwargs['instance'] = user.profile
        kwargs['user_instance'] = user
        return kwargs

    def form_valid(self, form):
        form.save()
        del self.request.session['user_create_step1_user_id']
        return redirect(self.success_url)

def get_user_privilege_level(user):
    if user.is_superuser:
        return 3
    if user.is_staff:
        return 2
    return 1

def role_manage(request):
    if not request.user.is_staff:
        raise PermissionDenied
    if request.method == 'POST':
        name = request.POST.get('new_role', '').strip()
        if name:
            Role.objects.get_or_create(name=name)
            messages.success(request, f'Должность "{name}" добавлена.')
        return redirect(request.META.get('HTTP_REFERER', reverse('user_management:user_list')))
    return redirect('user_management:user_list')

@require_POST
def role_delete(request, role_id):
    if not request.user.is_staff:
        raise PermissionDenied
    Role.objects.filter(id=role_id).delete()
    messages.success(request, 'Должность удалена.')
    return redirect(request.META.get('HTTP_REFERER', reverse('user_management:user_list')))

class UserUpdateView(UpdateView):
    model = User
    template_name = 'user_management/user_form.html'
    fields = ['username', 'email', 'first_name', 'last_name', 'groups', 'is_active']
    success_url = reverse_lazy('user_management:user_list')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            raise PermissionDenied("У вас нет доступа к управлению пользователями.")
        user_to_edit = self.get_object()
        if get_user_privilege_level(request.user) < get_user_privilege_level(user_to_edit):
            self.readonly = True
        else:
            self.readonly = False
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['profile_form'] = UserProfileForm(self.request.POST, self.request.FILES, instance=self.object.profile, user_instance=self.object)
        else:
            context['profile_form'] = UserProfileForm(instance=self.object.profile, user_instance=self.object)
        context['readonly'] = getattr(self, 'readonly', False)
        context['roles'] = Role.objects.all()
        return context

    def form_valid(self, form):
        if getattr(self, 'readonly', False):
            raise PermissionDenied("Недостаточно прав для редактирования этого пользователя.")
        response = super().form_valid(form)
        profile_form = UserProfileForm(self.request.POST, self.request.FILES, instance=self.object.profile, user_instance=self.object)
        if profile_form.is_valid():
            profile_form.save()
        return response

class UserProgressDashboardView(DetailView):
    model = User
    template_name = 'user_management/user_progress_dashboard.html'
    context_object_name = 'target_user'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            raise PermissionDenied("У вас нет доступа к управлению пользователями.")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        profile = user.profile
        exp = profile.exp 
        
        # Получаем все курсы пользователя
        user_courses = UserCourse.objects.filter(user=user).select_related('course')
        
        # Получаем все результаты тестирования пользователя ДО цикла по курсам
        quiz_results = list(QuizResult.objects.filter(user=user).order_by('-completed_at'))
        
        # Подготавливаем данные о прогрессе для каждого курса
        courses_progress = []
        
        for user_course in user_courses:
            course = user_course.course
            
            # Получаем траекторию пользователя для этого курса
            trajectory = UserLessonTrajectory.objects.filter(user=user, course=course).first()
            
            if trajectory:
                # Используем уроки из траектории
                lessons = trajectory.lessons.all().order_by('order')
                total_lessons = lessons.count()
                lesson_ids = lessons.values_list('id', flat=True)
                
                completed_lessons = UserProgress.objects.filter(
                    user=user,
                    course=course,
                    completed=True,
                    lesson_id__in=lesson_ids
                ).count()
            else:
                # Используем все уроки курса
                lessons = course.lessons.all().order_by('order')
                total_lessons = lessons.count()
                completed_lessons = UserProgress.objects.filter(
                    user=user,
                    course=course,
                    completed=True
                ).count()
            
            # Вычисляем процент прогресса
            progress_percent = int((completed_lessons / total_lessons) * 100) if total_lessons > 0 else 0
            
            # Проверяем прохождение финального теста
            quiz_passed = False
            if course.final_quiz:
                quiz_passed = QuizResult.objects.filter(
                    user=user,
                    quiz_title=course.final_quiz.name,
                    passed=True
                ).exists()
            
            # Получаем детальную информацию об уроках
            lessons_detail = []
            for lesson in lessons:
                progress = UserProgress.objects.filter(
                    user=user,
                    lesson=lesson,
                    completed=True
                ).first()
                
                lessons_detail.append({
                    'lesson': lesson,
                    'completed': progress is not None,
                    'completed_at': progress.completed_at if progress else None,
                    'order': lesson.order
                })
            
            best_attempt = None
            if course.final_quiz:
                attempts = [qr for qr in quiz_results if qr.quiz_title == course.final_quiz.name]
                if attempts:
                    best_attempt = sorted(attempts, key=lambda x: (x.percent, x.completed_at), reverse=True)[0]
            
            courses_progress.append({
                'course': course,
                'user_course': user_course,
                'total_lessons': total_lessons,
                'completed_lessons': completed_lessons,
                'progress_percent': progress_percent,
                'quiz_passed': quiz_passed,
                'lessons_detail': lessons_detail,
                'can_receive_exp': user_course.can_receive_exp(),
                'exp_reward': user_course.exp_reward() if user_course.status == 'completed' else 0,
                'best_attempt': best_attempt,
            })
        
        # Общая статистика
        total_courses = len(courses_progress)
        completed_courses = len([cp for cp in courses_progress if cp['user_course'].status == 'completed'])
        started_courses = len([cp for cp in courses_progress if cp['user_course'].status == 'started'])
        available_courses = len([cp for cp in courses_progress if cp['user_course'].status == 'available'])
        
        total_lessons_completed = sum(cp['completed_lessons'] for cp in courses_progress)
        total_lessons_available = sum(cp['total_lessons'] for cp in courses_progress)
        overall_progress = int((total_lessons_completed / total_lessons_available) * 100) if total_lessons_available > 0 else 0
        
        def count_exp(exp, level=1):
            while exp >= level * 100:
                level += 1
            progress = ((exp - ((level - 1) * 100)) / 100) * 100
            return level, min(progress, 100)
        level, progress = count_exp(exp)

        # Детальная информация о результатах тестов
        detailed_quiz_results = []
        for quiz_result in quiz_results:
            # Получаем ответы пользователя для этого теста
            user_answers = UserAnswer.objects.filter(
                user=user,
                quiz_result=quiz_result
            ).select_related('question', 'selected_answer')
            
            # Группируем ответы по вопросам
            questions_data = []
            for answer in user_answers:
                question = answer.question
                
                # Получаем все варианты ответов для вопроса
                all_answers = question.answer_set.all()
                
                # Определяем правильные ответы
                correct_answers = all_answers.filter(is_correct=True)
                
                questions_data.append({
                    'question': question,
                    'user_answer': answer,
                    'all_answers': all_answers,
                    'correct_answers': correct_answers,
                    'is_correct': answer.is_correct,
                    'question_type': question.question_type
                })
            
            detailed_quiz_results.append({
                'quiz_result': quiz_result,
                'questions_data': questions_data,
                'total_questions': len(questions_data),
                'correct_answers_count': len([qd for qd in questions_data if qd['is_correct']])
            })
        
        # Пагинация по попыткам тестов
        paginator = Paginator(quiz_results, 4)
        page_number = self.request.GET.get('page', 1)
        try:
            page_obj = paginator.page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)
        
        # Пагинация по курсам
        paginator_courses = Paginator(courses_progress, 4)
        page_number_courses = self.request.GET.get('courses_page', 1)
        try:
            page_obj_courses = paginator_courses.page(page_number_courses)
        except PageNotAnInteger:
            page_obj_courses = paginator_courses.page(1)
        except EmptyPage:
            page_obj_courses = paginator_courses.page(paginator_courses.num_pages)
        
        context.update({
            'exp': exp,
            'level': level,
            'progress': int(progress),
            'courses_progress': courses_progress,
            'total_courses': total_courses,
            'completed_courses': completed_courses,
            'started_courses': started_courses,
            'available_courses': available_courses,
            'total_lessons_completed': total_lessons_completed,
            'total_lessons_available': total_lessons_available,
            'overall_progress': overall_progress,
            'detailed_quiz_results': detailed_quiz_results,
            'quiz_results': quiz_results,
            'page_obj': page_obj,
            'page_obj_courses': page_obj_courses,
        })
        
        return context

@method_decorator(staff_member_required, name='dispatch')
class UserQuizReportView(DetailView):
    model = QuizResult
    template_name = 'user_management/user_quiz_report.html'
    context_object_name = 'quiz_result'

    def get_object(self):
        return QuizResult.objects.get(id=self.kwargs['quiz_id'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        quiz_result = self.get_object()
        answers = quiz_result.answers.select_related('question', 'selected_answer').all()
        # Группируем ответы по вопросам
        grouped = {}
        for ans in answers:
            grouped.setdefault(ans.question, []).append(ans)
        context['grouped_answers'] = grouped
        return context


class UserPasswordChangeView(FormView):
    template_name = 'user_management/user_password_change.html'
    form_class = SetPasswordForm
    success_url = reverse_lazy('user_management:user_list')

    def dispatch(self, request, *args, **kwargs):
        # Только staff или superuser могут менять пароли другим
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            raise PermissionDenied('У вас нет прав для смены пароля других пользователей.')
        # Можно добавить: запрет staff менять пароль superuser, если нужно
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = User.objects.get(pk=self.kwargs['pk'])
        return kwargs

    def form_valid(self, form):
        form.save()  # set_password + save
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['object'] = User.objects.get(pk=self.kwargs['pk'])
        return context