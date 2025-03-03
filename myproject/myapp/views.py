from django.shortcuts import render
from django.http import HttpResponse, HttpRequest

def index(request: HttpRequest) -> HttpResponse:
    return render(request, 'home.html')

def about(request: HttpRequest) -> HttpResponse:
    return render(request, 'about.html')

def profile(request: HttpRequest) -> HttpResponse:
    return render(request, 'profile.html')