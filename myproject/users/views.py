from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.contrib.auth import login as auth_login
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView


from myapp.models import UserCourse, UserProgress, QuizResult
from courses.models import UserLessonTrajectory
from .forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm
 

def register(request: HttpRequest) -> HttpResponse:
    """
    Обрабатывает регистрацию нового пользователя.

    Args:
        request (HttpRequest): Объект запроса.

    Returns:
        HttpResponse: Ответ с отрендеренным шаблоном или редирект на главную страницу.
    """
        
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Создан аккаунт {username}!')
            return redirect('home')
    else:
        form = UserRegisterForm()
    return render(request, 'users/register.html', {'form': form})



@login_required
def profile(request: HttpRequest) -> HttpResponse:
    """
    Отображает страницу профиля пользователя, а также его прогресс
    по начатым курсам.

    Args:
        request (HttpRequest): Объект запроса.

    Returns:
        HttpResponse: Ответ с отрендеренным шаблоном профиля.
        Шаблон включает формы для редактирования профиля и список курсов с прогрессом.
    """
    user = request.user
    started_courses = UserCourse.objects.filter(user=user).select_related('course')
    unfinished_courses = []
    finished_courses = []
    exp = 0
    level = 1
    quiz_results = QuizResult.objects.filter(user=request.user).order_by('-completed_at')
    all_lessons_completed = False  # Инициализируем переменную значением по умолчанию
    percent = 0  # Добавляем инициализацию переменной

    for user_course in started_courses:
        course = user_course.course
        completed = UserProgress.objects.filter(
            user=user,
            course=course,
            completed=True
        ).count()

        trajectory = UserLessonTrajectory.objects.filter(user=request.user, course=course).first()
        total = trajectory.lessons.count() if trajectory else course.lessons.count()
        percent = int((completed / total) * 100) if total > 0 else 0

        course_data = {
            'course': course,
            'completed': completed,
            'total': total,
            'percent': percent
        }

        if course.final_quiz:
            quiz_passed = QuizResult.objects.filter(
                user=request.user,
                quiz_title=course.final_quiz,
                passed=True
            ).exists()
            course_data['quiz_passed'] = quiz_passed

        if percent == 100:
            user_course_obj = UserCourse.objects.get(user=user, course=course)
            if user_course_obj.can_receive_exp():
                finished_courses.append(course_data)
                exp += user_course_obj.exp_reward()
            else:
                unfinished_courses.append(course_data)
                exp += 15
        else:
            unfinished_courses.append(course_data)
            exp += 15

        # Обновляем флаг завершения всех уроков
        all_lessons_completed = (percent == 100) or all_lessons_completed

    # Функция для расчета уровня и прогресса
    def count_exp(exp, level):
        while exp >= level * 100:
            level += 1
        progress = ((exp - ((level - 1) * 100)) / 100) * 100
        return level, min(progress, 100)

    level, progress = count_exp(exp, level)

    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect('profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.profile)

    return render(request, 'users/profile.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'unfinished_courses': unfinished_courses,
        'finished_courses': finished_courses,
        'exp': exp,
        'progress': int(progress),
        'level': level,
        'quiz_results': quiz_results,
        'all_lessons_completed': all_lessons_completed,
    })


class CustomLoginView(LoginView):
    """
    Кастомный класс расширяющий функционал встроенной в Django функции авторизации.
    Если пользователь зарегистрирован, но администратор сайта не поставил ему в админ панеле галочку - подтверждение,
    то пользователю, при попытке входа, будет выводится сообщение "Ваш аккаунт ожидает подтверждения администратором."
    """
    template_name = "users/login.html"

    def form_valid(self, form):
        user = form.get_user()
        if not user.profile.is_approved:
            messages.error(self.request, "Ваш аккаунт ожидает подтверждения администратором.")
            return redirect('login')
        auth_login(self.request, user)
        return redirect(self.get_success_url())