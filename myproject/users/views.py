from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse

from myapp.models import UserCourse, UserProgress
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
    
    course_progress = []
    for user_course in started_courses:
        course = user_course.course
        completed = UserProgress.objects.filter(
            user=user,
            course=course,
            completed=True
        ).count()
        total = course.lessons.count()
        percent = int((completed / total) * 100) if total > 0 else 0
        
        if percent != 100:
            course_progress.append({
                'course': course,
                'completed': completed,
                'total': total,
                'percent': percent
            })
    

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
        'course_progress': course_progress
    })



@login_required
def profile_finished_courses(request: HttpRequest) -> HttpResponse:
    """
    Отображает страницу профиля пользователя, а также его завершенные курсы.
    """
    user = request.user
    started_courses = UserCourse.objects.filter(user=user).select_related('course')
    
    finished_courses = []
    for user_course in started_courses:
        course = user_course.course
        completed = UserProgress.objects.filter(
            user=user,
            course=course,
            completed=True
        ).count()
        total = course.lessons.count()
        percent = int((completed / total) * 100) if total > 0 else 0

        if percent == 100:  # Проверяем, завершен ли курс
            finished_courses.append({
                'course': course,
                'completed': completed,
                'total': total,
                'percent': percent
            })
    
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect('profile_finished_courses')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.profile)

    return render(request, 'users/finished_courses.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'course_progress': finished_courses  # Передаем только завершенные курсы
    })