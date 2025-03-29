from django.contrib import admin
# from .models import Quiz, Question, Answer, UserQuizResult

# class AnswerInline(admin.TabularInline):
#     model = Answer
#     extra = 1  # Количество пустых полей для ответов

# class QuestionInline(admin.TabularInline):
#     model = Question
#     extra = 1
#     inlines = [AnswerInline]

# @admin.register(Quiz)
# class QuizAdmin(admin.ModelAdmin):
#     list_display = ('title', 'is_active', 'created_at')
#     inlines = [QuestionInline]

# @admin.register(UserQuizResult)
# class UserQuizResultAdmin(admin.ModelAdmin):
#     list_display = ('user', 'quiz', 'score', 'completed_at')
#     list_filter = ('quiz', 'user')