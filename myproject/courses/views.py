from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Max
from django.db import transaction
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST
from .forms import CourseForm, LessonForm
from .models import Course, Lesson
from myapp.models import UserProgress, UserCourse
from myapp.views import is_admin, is_author_or_admin



def course_detail(request, slug):
    course = get_object_or_404(Course, slug=slug)
    has_started = False
    user_course = None
    progress = 0
    completed_lessons = 0
    total_lessons = course.lessons.count()
    next_lesson = None
    all_completed = False
    completed_lessons_ids = None
    exp_earned = 150  # Можно вынести в модель курса

    if request.user.is_authenticated:
        user_course = UserCourse.objects.filter(user=request.user, course=course).first()
        has_started = user_course is not None  # Упрощенная проверка
        
        if has_started:
            completed_lessons = UserProgress.objects.filter(
                user=request.user, 
                course=course, 
                completed=True
            ).count()
            progress = int((completed_lessons / total_lessons) * 100) if total_lessons > 0 else 0

            completed_lessons_ids = UserProgress.objects.filter(
                user=request.user,
                course=course,
                completed=True
            ).values_list('lesson_id', flat=True)

            max_completed_order = UserProgress.objects.filter(
                user=request.user,
                course=course,
                completed=True
            ).aggregate(max_order=Max('lesson__order'))['max_order'] or 0

            next_lesson = Lesson.objects.filter(
                course=course,
                order__gt=max_completed_order
            ).order_by('order').first()

            if not next_lesson:
                next_lesson = course.lessons.first()

        if request.method == 'POST' and 'start_course' in request.POST:
            if not has_started:
                UserCourse.objects.create(user=request.user, course=course)
                return redirect('course_detail', slug=slug)
    else:
        return redirect('login')

    all_completed = has_started and (completed_lessons == total_lessons)
    
    # Обновляем флаг анимации
    if all_completed and user_course and not user_course.course_complete_animation_shown:
        with transaction.atomic():
            user_course.refresh_from_db()
            if not user_course.course_complete_animation_shown:
                user_course.end_date = timezone.now()
                user_course.is_completed = True
                user_course.course_complete_animation_shown = True
                user_course.save()

    return render(request, 'courses/course_detail.html', {
        'course': course,
        'user_course': user_course,
        'has_started': has_started,
        'progress': progress,
        'completed_lessons': completed_lessons,
        'completed_lessons_ids': completed_lessons_ids,
        'total_lessons': total_lessons,
        'next_lesson': next_lesson,
        'all_completed': all_completed,
        'shown_animation': user_course.course_complete_animation_shown,
        'exp_earned': exp_earned
    })

def course_detail_all(request):
    courses = Course.objects.all()  # Получаем все доступные курсы
    completed_courses = []

    if request.user.is_authenticated:
        # Получаем список завершенных курсов для текущего пользователя
        completed_courses = UserCourse.objects.filter(user=request.user, is_completed=True).values_list('course_id', flat=True)


    context = {
        'courses': courses,
        'completed_courses': completed_courses,
    }
    return render(request, 'courses/all_courses_list.html', context)

def lesson_detail(request, course_slug, lesson_id):
    if not request.user.is_authenticated:
        return redirect('login')
    
    course = get_object_or_404(Course, slug=course_slug)
    lesson = get_object_or_404(Lesson, id=lesson_id, course=course)
    
    # Проверка доступа
    if not UserCourse.objects.filter(user=request.user, course=course).exists():
        return redirect('course_detail', slug=course.slug)
    
    # Помечаем урок как просмотренный (но не завершенный)
    UserProgress.objects.get_or_create(
        user=request.user,
        lesson=lesson,
        defaults={'course': course}
    )
    return render(request, 'courses/lesson_detail.html', {'lesson': lesson})


@login_required
@user_passes_test(is_admin, login_url='/')
def create_course(request):
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.save(commit=False)
            course.author = request.user
            course.save()
            return redirect('home')
    else:
        form = CourseForm()
    return render(request, 'courses/create_course.html', {'form': form})

@login_required
def create_lesson(request, course_slug):
    course = get_object_or_404(Course, slug=course_slug)
    if request.method == 'POST':
        form = LessonForm(request.POST)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.course = course
            lesson.save()
            return redirect('course_detail', course_slug)
    else:
        form = LessonForm()
    return render(request, 'courses/create_lesson.html', {'form': form, 'course': course})


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


@require_POST
def complete_lesson(request, course_slug, lesson_id):
    """Отмечает урок как завершенный и начисляет пользователю опыт"""

    if not request.user.is_authenticated:
        return redirect('login')
    
    course = get_object_or_404(Course, slug=course_slug)
    lesson = get_object_or_404(Lesson, id=lesson_id, course=course)
    
    # Проверяем, что пользователь начал курс
    if not UserCourse.objects.filter(user=request.user, course=course).exists():
        return redirect('course_detail', slug=course.slug)
    
    # Обновляем прогресс
    UserProgress.objects.update_or_create(
        user=request.user,
        lesson=lesson,
        defaults={'completed': True, 'course': course}
    )
    
    # Начисляем опыт пользователю
    # profile = Profile.objects.get(user=request.user)
    # profile.exp += 20  # Например, 50 опыта за урок
    # profile.save()

    return redirect('course_detail', slug=course_slug)