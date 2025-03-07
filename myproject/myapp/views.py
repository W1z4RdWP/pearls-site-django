from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpRequest
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import CourseForm, LessonForm
from .models import Course, Lesson

def index(request: HttpRequest) -> HttpResponse:
    courses = Course.objects.all()
    return render(request, 'home.html', {'courses': courses})

def course_detail(request, slug):
    course = get_object_or_404(Course, slug=slug)
    lessons = course.lessons.all()
    return render(request, 'course_detail.html', {'course': course, 'lessons': lessons})

def lesson_detail(request, course_slug, lesson_id):
    course = get_object_or_404(Course, slug=course_slug)
    lesson = get_object_or_404(Lesson, id=lesson_id, course=course)
    return render(request, 'lesson_detail.html', {'lesson': lesson})

def about(request: HttpRequest) -> HttpResponse:
    return render(request, 'about.html')

def profile(request: HttpRequest) -> HttpResponse:
    return render(request, 'profile.html')

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