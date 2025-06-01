from django.views.generic import DetailView
from django.shortcuts import get_object_or_404
from courses.models import Course, Lesson
from myapp.models import UserProgress
from django.views.generic import ListView, CreateView, UpdateView, TemplateView, DeleteView
from django.urls import reverse_lazy
from .models import CategoryName

class LessonListView(ListView):
    model = Lesson
    template_name = 'builder/home.html'
    context_object_name = 'lessons'

class LessonMasterDetailView(TemplateView):
    template_name = 'builder/master_detail.html'

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


class LessonUpdateView(UpdateView):
    model = Lesson
    fields = ['title', 'content', 'video_id', 'order', 'course', 'category']
    template_name = 'builder/lesson_form.html'
    success_url = reverse_lazy('builder:lesson_master')


class CategoryListView(ListView):
    model = CategoryName
    template_name = 'builder/category_list.html'
    context_object_name = 'categories'

class CategoryCreateView(CreateView):
    model = CategoryName
    fields = ['name', 'parent', 'order']
    template_name = 'builder/category_form.html'
    success_url = reverse_lazy('builder:lesson_master')

class CategoryUpdateView(UpdateView):
    model = CategoryName
    fields = ['name', 'parent', 'order']
    template_name = 'builder/category_form.html'
    success_url = reverse_lazy('builder:lesson_master')

class CategoryDeleteView(DeleteView):
    model = CategoryName
    template_name = 'builder/category_confirm_delete.html'
    success_url = reverse_lazy('builder:lesson_master')
