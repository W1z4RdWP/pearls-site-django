from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpRequest
from django.contrib.auth.decorators import login_required
from .forms import CourseForm
from .models import Course

def index(request: HttpRequest) -> HttpResponse:
    courses = Course.objects.all()
    return render(request, 'home.html', {'courses': courses})

def about(request: HttpRequest) -> HttpResponse:
    return render(request, 'about.html')

def profile(request: HttpRequest) -> HttpResponse:
    return render(request, 'profile.html')


@login_required
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