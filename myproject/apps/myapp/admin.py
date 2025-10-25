from django.contrib import admin
from .models import UserCourse, QuizResult, UserAnswer, ChangeLog

admin.site.site_header = "Kupryazha"
admin.site.site_title = "Администрирование сайта"
admin.site.index_title = "Панель управления"

@admin.register(UserCourse)
class UserCourseAdmin(admin.ModelAdmin):
    list_display = ('user', 'course',)
    list_filter = ('course',)
    search_fields = ('user__username', 'course__title')

@admin.register(ChangeLog)
class ChangeLogAdmin(admin.ModelAdmin):
    list_display = ('version', 'release_date', 'type', 'title', 'is_public')
    list_filter = ('type', 'is_public')
    search_fields = ('title', 'description')
    date_hierarchy = 'release_date'

@admin.register(QuizResult)
class QuizResultAdmin(admin.ModelAdmin):
    list_display = ('user', 'quiz_title', 'score', 'total_questions', 'percent', 'passed', 'completed_at')
    list_filter = ('passed', 'completed_at', 'course')
    search_fields = ('user__username', 'quiz_title')
    readonly_fields = ('completed_at',)

@admin.register(UserAnswer)
class UserAnswerAdmin(admin.ModelAdmin):
    list_display = ('user', 'question', 'question_type', 'selected_answer_text', 'answer_text_preview', 'is_correct')
    list_filter = ('question__question_type', 'is_correct', 'question__quiz')
    search_fields = ('user__username', 'question__text', 'answer_text')
    readonly_fields = ('user', 'question', 'quiz_result')
    
    def question_type(self, obj):
        return obj.question.question_type
    question_type.short_description = 'Тип вопроса'
    
    def selected_answer_text(self, obj):
        if obj.selected_answer:
            return obj.selected_answer.text
        return '-'
    selected_answer_text.short_description = 'Выбранный ответ'
    
    def answer_text_preview(self, obj):
        if obj.answer_text:
            return obj.answer_text[:50] + '...' if len(obj.answer_text) > 50 else obj.answer_text
        return '-'
    answer_text_preview.short_description = 'Текстовый ответ'