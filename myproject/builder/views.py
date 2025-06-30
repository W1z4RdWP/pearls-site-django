from django.views.generic import DetailView, TemplateView
from django.shortcuts import get_object_or_404
from courses.models import Course, Lesson
from myapp.models import UserProgress
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import CategoryName
from django.core.exceptions import PermissionDenied


@method_decorator(login_required(login_url='/login/'), name='dispatch')
class LessonMasterDetailView(TemplateView):
    template_name = 'builder/master_detail.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            raise PermissionDenied("Доступ разрешён только для сотрудников или суперпользователей.")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        categories = CategoryName.objects.filter(parent__isnull=True).prefetch_related('subcategories', 'lessons')
        context['categories'] = categories

        # Уроки без категории
        uncategorized_lessons = Lesson.objects.filter(category__isnull=True)
        context['uncategorized_lessons'] = uncategorized_lessons

        pk = self.kwargs.get('pk')
        if pk:
            context['selected_lesson'] = Lesson.objects.get(pk=pk)
        else:
            # Выбираем первый урок из категорий или из uncategorized
            first_lesson = None
            for cat in categories:
                if cat.lessons.exists():
                    first_lesson = cat.lessons.first()
                    break
            if not first_lesson and uncategorized_lessons.exists():
                first_lesson = uncategorized_lessons.first()
            context['selected_lesson'] = first_lesson
        return context


class LessonCreateView(CreateView):
    model = Lesson
    fields = ['title', 'content', 'video_id', 'order', 'course', 'category']
    template_name = 'builder/lesson_form.html'
    success_url = reverse_lazy('builder:lesson_master')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            raise PermissionDenied("Доступ разрешён только для сотрудников или суперпользователей.")
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        category_id = self.kwargs.get('category_id')
        if category_id:
            category = get_object_or_404(CategoryName, pk=category_id)
            initial['category'] = category
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category_id = self.kwargs.get('category_id')
        if category_id:
            context['preselected_category'] = get_object_or_404(CategoryName, pk=category_id)
        return context


class LessonUpdateView(UpdateView):
    model = Lesson
    fields = ['title', 'content', 'video_id', 'order', 'course', 'category']
    template_name = 'builder/lesson_form.html'
    success_url = reverse_lazy('builder:lesson_master')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            raise PermissionDenied("Доступ разрешён только для сотрудников или суперпользователей.")
        return super().dispatch(request, *args, **kwargs)


class LessonDeleteView(DeleteView):
    model = Lesson
    success_url = reverse_lazy('builder:lesson_master')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            raise PermissionDenied("Доступ разрешён только для сотрудников или суперпользователей.")
        return super().dispatch(request, *args, **kwargs)


class CategoryListView(ListView):
    model = CategoryName
    template_name = 'builder/category_list.html'
    context_object_name = 'categories'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            raise PermissionDenied("Доступ разрешён только для сотрудников или суперпользователей.")
        return super().dispatch(request, *args, **kwargs)


class CategoryCreateView(CreateView):
    model = CategoryName
    fields = ['name', 'parent', 'order']
    template_name = 'builder/category_form.html'
    success_url = reverse_lazy('builder:lesson_master')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            raise PermissionDenied("Доступ разрешён только для сотрудников или суперпользователей.")
        return super().dispatch(request, *args, **kwargs)


class CategoryUpdateView(UpdateView):
    model = CategoryName
    fields = ['name', 'parent', 'order']
    template_name = 'builder/category_form.html'
    success_url = reverse_lazy('builder:lesson_master')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            raise PermissionDenied("Доступ разрешён только для сотрудников или суперпользователей.")
        return super().dispatch(request, *args, **kwargs)


class CategoryDeleteView(DeleteView):
    model = CategoryName
    template_name = 'builder/category_confirm_delete.html'
    success_url = reverse_lazy('builder:lesson_master')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            raise PermissionDenied("Доступ разрешён только для сотрудников или суперпользователей.")
        return super().dispatch(request, *args, **kwargs)


class DashboardView(TemplateView):
    template_name = 'builder/dashboard.html'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            raise PermissionDenied("Доступ разрешён только для сотрудников или суперпользователей.")
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Можно добавить статистику по базе знаний, если потребуется
        return context
