from django.shortcuts import render
from django.http import HttpResponse, HttpRequest
from .models import Course


def index(request: HttpRequest) -> HttpResponse:
    courses = Course.objects.all()
    return render(request, 'home.html', {'courses': courses})

def about(request: HttpRequest) -> HttpResponse:
    return render(request, 'about.html')

def is_admin(user) -> bool:
    return user.is_staff

def is_author_or_admin(user, course):
    return user.is_staff or user == course.author

def page_not_found_view(request, exception):
    return render(request, '404.html', status=404)
