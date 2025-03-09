from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpRequest
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST
from .forms import CourseForm, LessonForm
from .models import Course, Lesson, UserProgress, UserCourse


def index(request: HttpRequest) -> HttpResponse:
    courses = Course.objects.all()
    return render(request, 'home.html', {'courses': courses})

# def course_detail(request, slug):
#     course = get_object_or_404(Course, slug=slug)
#     lessons = course.lessons.all()
#     return render(request, 'course_detail.html', {'course': course, 'lessons': lessons})
def course_detail(request, slug):
    course = get_object_or_404(Course, slug=slug)
    has_started = False
    progress = 0
    completed_lessons = 0
    total_lessons = course.lessons.count()

    if request.user.is_authenticated:
        has_started = UserCourse.objects.filter(user=request.user, course=course).exists()
        
        if has_started:
            completed_lessons = UserProgress.objects.filter(
                user=request.user, 
                course=course, 
                completed=True
            ).count()
            progress = int((completed_lessons / total_lessons) * 100) if total_lessons > 0 else 0

    if request.method == 'POST' and 'start_course' in request.POST:
        if not has_started:
            UserCourse.objects.create(user=request.user, course=course)
            return redirect('course_detail', slug=slug)

    return render(request, 'course_detail.html', {
        'course': course,
        'has_started': has_started,
        'progress': progress,
        'completed_lessons': completed_lessons,
        'total_lessons': total_lessons
    })

# def lesson_detail(request, course_slug, lesson_id):
#     course = get_object_or_404(Course, slug=course_slug)
#     lesson = get_object_or_404(Lesson, id=lesson_id, course=course)
#     return render(request, 'lesson_detail.html', {'lesson': lesson})

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
    
    return render(request, 'lesson_detail.html', {
        'lesson': lesson,
        'course_slug': course_slug
    })


def about(request: HttpRequest) -> HttpResponse:
    return render(request, 'about.html')


def profile(request):
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
        
        course_progress.append({
            'course': course,
            'completed': completed,
            'total': total,
            'percent': int((completed / total) * 100) if total > 0 else 0
        })
    
    context = {
        'course_progress': course_progress
    }
    return render(request, 'profile.html', context)


def is_admin(user) -> bool:
    return user.is_staff

def page_not_found_view(request, exception):
    return render(request, '404.html', status=404)

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
    return render(request, 'create_course.html', {'form': form})

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
    return render(request, 'create_lesson.html', {'form': form, 'course': course})


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


def lesson_detail(request, course_slug, lesson_id):
    course = get_object_or_404(Course, slug=course_slug)
    lesson = get_object_or_404(Lesson, id=lesson_id, course=course)
    
    # Отмечаем урок как пройденный
    if not UserProgress.objects.filter(user=request.user, lesson=lesson).exists():
        UserProgress.objects.create(
            user=request.user,
            course=course,
            lesson=lesson,
            completed=True
        )
    
    return render(request, 'lesson_detail.html', {'lesson': lesson})


@require_POST
def complete_lesson(request, course_slug, lesson_id):
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
    
    return redirect('lesson_detail', course_slug=course_slug, lesson_id=lesson_id)