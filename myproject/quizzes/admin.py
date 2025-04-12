from django.contrib import admin
from .models import Quiz, Question, Answer


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ['name']
    list_filter = ['name']
    search_fields = ['name']

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['quiz', 'text']
    list_filter = ['quiz']
    search_fields = ['text']

@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ['question', 'text', 'is_correct']
    list_filter = ['question', 'is_correct']
    search_fields = ['question__text','text']
