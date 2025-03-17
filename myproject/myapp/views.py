from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpRequest
from django.db.models import Max
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST
from .forms import CourseForm, LessonForm
from .models import Course, Lesson, UserProgress, UserCourse


def index(request: HttpRequest) -> HttpResponse:
    courses = Course.objects.all()
    return render(request, 'home.html', {'courses': courses})


def course_detail(request, slug):
    course = get_object_or_404(Course, slug=slug)
    has_started = False
    progress = 0
    completed_lessons = 0
    total_lessons = course.lessons.count()
    next_lesson = None
    all_completed = False

    if request.user.is_authenticated:
        has_started = UserCourse.objects.filter(user=request.user, course=course).exists()
        
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

        # Получаем максимальный порядок завершенных уроков
            max_completed_order = UserProgress.objects.filter(
                user=request.user,
                course=course,
                completed=True
            ).aggregate(max_order=Max('lesson__order'))['max_order'] or 0

            # Находим следующий урок
            next_lesson = Lesson.objects.filter(
                course=course,
                order__gt=max_completed_order
            ).order_by('order').first()

            # Если все уроки завершены, берем первый урок
            if not next_lesson:
                next_lesson = course.lessons.first()

        # Обработка POST запроса должна быть внутри authenticated блока
        if request.method == 'POST' and 'start_course' in request.POST:
            if not has_started:
                UserCourse.objects.create(user=request.user, course=course)
                return redirect('course_detail', slug=slug)
    else:
        return redirect('login')

    return render(request, 'course_detail.html', {
        'course': course,
        'has_started': has_started,
        'progress': progress,
        'completed_lessons': completed_lessons,
        'completed_lessons_ids': completed_lessons_ids,
        'total_lessons': total_lessons,
        'next_lesson': next_lesson,
        'all_completed': all_completed
    })



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
    return render(request, 'lesson_detail.html', {'lesson': lesson})


def about(request: HttpRequest) -> HttpResponse:
    return render(request, 'about.html')


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


@login_required
@user_passes_test(is_admin, login_url='/')
def edit_lesson(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    return render("404.html")



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
    
    return redirect('course_detail', slug=course_slug)