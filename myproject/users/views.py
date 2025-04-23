from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse

from myapp.models import UserCourse, UserProgress
from courses.models import UserLessonTrajectory
from .forms import UserRegisterForm
from .forms import UserUpdateForm, ProfileUpdateForm

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
    
    

    for user_course in started_courses:
        course = user_course.course
        completed = UserProgress.objects.filter(
            user=user,
            course=course,
            completed=True
        ).count()
        # Получаем траекторию пользователя, если она есть
        trajectory = UserLessonTrajectory.objects.filter(user=request.user, course=course).first()
        if trajectory:
            total = trajectory.lessons.all().count() # Общее количество уроков в траектории пользователя
        else:
            total = course.lessons.count() # Число всех существующих уроков курса, если траектория не задана
        percent = int((completed / total) * 100) if total > 0 else 0
        
        course_data = {
            'course': course,
            'completed': completed,
            'total': total,
            'percent': percent
        }

        if percent >= 100:
            finished_courses.append(course_data)
            exp += 165 # начисляется 150 опыта, т.к. 15 дается за начало курса, а при его завершении эти 15 убираются.
        else:
            unfinished_courses.append(course_data)
            exp += 15

    
    # Функция для расчета уровня и прогресса
    def count_exp(exp, level):
        while exp >= level * 100:
            level += 1
        progress = ((exp - ((level - 1) * 100)) / 100) * 100
        if progress > 100:
            progress = 100
        return level, progress

    # Рассчитываем уровень и прогресс
    level, progress = count_exp(exp, level)

    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect('profile')  # Перенаправление на страницу профиля
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.profile)

    return render(request, 'users/profile.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'unfinished_courses': unfinished_courses,
        'finished_courses': finished_courses,
        'exp': exp,
        'progress':progress,
        'level': level
    })

