from django.shortcuts import render
from django.http import HttpResponse, HttpRequest
from django.views.generic import TemplateView, ListView
from .models import Course, UserCourse, ChangeLog
from courses.models import Course as CourseModel
from datetime import date

class IndexView(TemplateView):
    """Класс представление домашней страницы

        Attrs:
            template_name: имя файла для рендера
            get_context_data: функция передает контекст в шаблон 
    """
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if user.is_authenticated:
            # Получаем курсы, назначенные пользователю через UserCourse
            user_courses = UserCourse.objects.filter(user=user).values_list('course', flat=True)
            context['courses'] = CourseModel.objects.filter(id__in=user_courses)
        else:
            context['courses'] = []
        return context

class AboutView(TemplateView):
    """Класс представление страницы 'О нас' """
    template_name = 'about.html'

def is_admin(user) -> bool:
    return user.is_staff

def is_author_or_admin(user, course):
    return user.is_staff or user == course.author

def page_not_found_view(request, exception):
    return render(request, '404.html', status=404)

def permission_denied_view(request, exception=None):
    return render(request, '403.html', status=403)

def method_not_allowed_view(request, exception=None):
    return render(request, '405.html', status=405)

def custom_error_500(request):
    return render(request, '500.html', status=500)

class ChangelogListView(ListView):
    model = ChangeLog
    paginate_by = 5
    template_name = 'changelog.html'
    context_object_name = 'changelog'

    def get_queryset(self):
        return ChangeLog.objects.filter(is_public=True)

class PrivacyPolicyView(TemplateView):
    """Класс представление страницы политики конфиденциальности"""
    template_name = 'privacy_policy.html'

    def get_context_data(self, **kwargs):
        """Добавляет текущую дату в контекст шаблона"""
        context = super().get_context_data(**kwargs)
        context['current_date'] = date.today()
        return context