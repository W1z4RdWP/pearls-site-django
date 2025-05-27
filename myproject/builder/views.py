from django.views.generic import DetailView
from django.shortcuts import get_object_or_404
from courses.models import Course, Lesson
from myapp.models import UserProgress
from django.views.generic import ListView, CreateView, UpdateView, TemplateView
from django.urls import reverse_lazy

class LessonListView(ListView):
    model = Lesson
    template_name = 'builder/home.html'
    context_object_name = 'lessons'

class LessonMasterDetailView(TemplateView):
    template_name = 'builder/master_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lessons = Lesson.objects.all().order_by('id')
        context['lessons'] = lessons

        pk = self.kwargs.get('pk')
        if pk:
            context['selected_lesson'] = Lesson.objects.get(pk=pk)
        elif lessons:
            context['selected_lesson'] = lessons[0]
        else:
            context['selected_lesson'] = None
        return context


class LessonCreateView(CreateView):
    model = Lesson
    fields = ['title', 'content', 'video_id', 'order', 'course']
    template_name = 'builder/lesson_form.html'
    success_url = reverse_lazy('builder:lesson_master')


class LessonUpdateView(UpdateView):
    model = Lesson
    fields = ['title', 'content', 'video_id', 'order', 'course']
    template_name = 'builder/lesson_form.html'
    success_url = reverse_lazy('builder:lesson_master')
