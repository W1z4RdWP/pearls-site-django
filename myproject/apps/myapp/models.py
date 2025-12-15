from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django_ckeditor_5.fields import CKEditor5Field
from django.utils import timezone
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from datetime import timedelta


from courses.models import Course, Lesson
from quizzes.models import Question, Answer

    
class UserProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'lesson')
        indexes = [
            models.Index(fields=['user'], name='userprogress_user_idx'),
        ]

    def save(self, *args, **kwargs):
        if not self.course_id:
            # Получаем первый курс из связанных с уроком
            self.course = self.lesson.courses.first()
        super().save(*args, **kwargs)



class UserCourse(models.Model):
    """
    Модель связывает пользователя и курс, показывает, что курс назначен пользователю.
    """
    STATUS_CHOICES = [
        ('available', 'Доступен'),
        ('started', 'Начат'),
        ('completed', 'Завершен'),
        ('blocked', 'Заблокирован')
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='started_courses')
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)
    deadline = models.DateTimeField(null=True, blank=True, verbose_name="Срок завершения курса", help_text="Дата, до которой нужно завершить курс")
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='available'
    )
    course_complete_animation_shown = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'course')
        verbose_name = 'Курс пользователя'
        verbose_name_plural = 'Курсы пользователей'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['user'], name='usercourse_user_idx'),
        ]

    def save(self, *args, **kwargs):
        """Устанавливаем end_date только при первом завершении курса и проверяем deadline"""
        # Автоматически устанавливаем deadline на основе course.default_deadline_days, если deadline не установлен
        if not self.deadline:
            # Получаем курс (может быть передан как объект или как ID)
            course = self.course
            if course and hasattr(course, 'default_deadline_days'):
                # Если у курса установлен default_deadline_days, используем его для расчета deadline
                if course.default_deadline_days and course.default_deadline_days > 0:
                    self.deadline = timezone.now() + timedelta(days=course.default_deadline_days)
        
        # Проверяем deadline и блокируем курс, если срок истек
        if self.deadline and self.status not in ['completed', 'blocked']:
            if timezone.now() > self.deadline:
                self.status = 'blocked'
        
        # Устанавливаем end_date только при первом завершении курса
        if self.status == 'completed' and not self.end_date:
            self.end_date = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.course.title} ({self.get_status_display()})"


class ManualCourseUnassignment(models.Model):
    """
    Модель для отслеживания ручных отмен назначений курсов.
    Используется для предотвращения автоматического переназначения курсов,
    которые были отменены вручную администратором.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='manual_unassignments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    unassigned_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата отмены назначения")
    unassigned_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='performed_unassignments',
        verbose_name="Кто отменил"
    )
    reason = models.TextField(blank=True, verbose_name="Причина отмены", help_text="Опционально")
    
    class Meta:
        unique_together = ('user', 'course')
        verbose_name = 'Ручная отмена назначения курса'
        verbose_name_plural = 'Ручные отмены назначений курсов'
        indexes = [
            models.Index(fields=['user', 'course']),
        ]
    
    def __str__(self):
        return f"Отмена: {self.user.username} - {self.course.title}"
    

class QuizResult(models.Model):
    """
    Модель отвечающая за сохранения данных о результате пройденного тестирования,
    конкретным пользователем.

    Attrs:
        - user(ForeignKey) - ссылка на пользователя, который прошел тест;
        - quiz_title(CharField) - название пройденного теста;
        - course(ForeignKey) - ссылка на курс, в рамках которого пройден тест;
        - score(Float) - баллы за правильные ответы (может быть дробным, например 1.5);
        - total_questions(Integer) - всего было вопросов в данном тесте;
        - percent(Float) - вычисление правильных ответов на вопросы данных пользователем в процентном соотношении;
        - completed_at(DateTime) - Дата и время когда тест был завершен;
        - passed(Bool) - Отмечает тест за пройденный по результатам пользователя или нет, если не соотв. условиям.
        - status(CharField) - Статус теста: 'completed' или 'pending' (ожидает проверки наставником);
        - reviewed_by(ForeignKey) - Наставник/администратор, который проверил открытые ответы;
        - reviewed_at(DateTime) - Дата и время проверки наставником;
        - mentor_comment(TextField) - Комментарий наставника к результату теста.

    """
    STATUS_CHOICES = [
        ('completed', 'Завершен'),
        ('pending', 'Ожидает проверки'),
        ('reviewed', 'Проверен'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    quiz_title = models.CharField(max_length=200)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Курс")
    score = models.FloatField()
    total_questions = models.IntegerField()
    percent = models.FloatField()
    completed_at = models.DateTimeField(auto_now_add=True)
    passed = models.BooleanField(default=False)
    excluded_from_limit = models.BooleanField(
        default=False, 
        verbose_name="Исключен из лимита попыток",
        help_text="Если True, эта попытка не учитывается при проверке лимита попыток"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='completed',
        verbose_name="Статус"
    )
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_quizzes',
        verbose_name="Проверил наставник"
    )
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Дата проверки"
    )
    mentor_comment = models.TextField(
        blank=True,
        null=True,
        verbose_name="Комментарий наставника"
    )

    class Meta:
        verbose_name = 'Результат теста'
        verbose_name_plural = 'Результаты тестов'
        indexes = [
            models.Index(fields=['user'], name='quizresult_user_idx'),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.quiz_title} ({self.percent}%)"
    

class UserAnswer(models.Model):
    """
    Ответы на вопросы при прохождении теста, которые дает пользователь.

    Attrs:
        - user(ForeignKey) - ссылка на пользователя, который дал ответ;
        - quiz_result(ForeignKey) - ссылка на результат прохождения теста;
        - question(ForeignKey) - ссылка на вопрос к которому относится ответ;
        - selected_answer(ForeignKey) - ссылка на ответ, который дал пользователь при прохождении теста;
        - is_correct(Bool) - правильно ли ответил пользователь;
        - answer_text(CharField) - текст ответа;
        - score_points(FloatField) - баллы за ответ (0, 0.5, 1) для многоуровневой оценки.
    
    """
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_answers')
    quiz_result = models.ForeignKey('QuizResult', on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey('quizzes.Question', on_delete=models.CASCADE)
    selected_answer = models.ForeignKey('quizzes.Answer', on_delete=models.SET_NULL, null=True, blank=True)
    is_correct = models.BooleanField(null=True, blank=True, help_text="Для открытых ответов: None = не оценено")
    answer_text = models.CharField(max_length=2000, blank=True, null=True)
    score_points = models.FloatField(
        null=True,
        blank=True,
        default=None,
        verbose_name="Баллы",
        help_text="Для открытых вопросов: 0 (неверно), 0.5 (частично верно), 1 (верно)"
    )

    class Meta:
        indexes = [
            models.Index(fields=['user'], name='useranswer_user_idx'),
            models.Index(fields=['quiz_result'], name='useranswer_quizresult_idx'),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.question.text} ({'верно' if self.is_correct else 'неверно'})"


class ChangeLog(models.Model):
    """
    Модель для ведения истории изменений. 
    В Админ панели можно выбрать что было добавлено в новой версии и дать подробное описание.
    """
    VERSION_TYPES = (
        ('feature', '🎁 Новый функционал'),
        ('bugfix', '🐞 Исправление ошибок'),
        ('improvement', '⚡ Улучшение'),
        ('security', '🔒 Безопасность'),
    )

    version = models.CharField('Версия', max_length=20)
    release_date = models.DateField('Дата релиза', default=timezone.now)
    type = models.CharField('Тип изменения', max_length=20, choices=VERSION_TYPES)
    title = models.CharField('Заголовок', max_length=200)
    description = models.TextField('Подробное описание')
    related_link = models.URLField('Ссылка', blank=True)
    is_public = models.BooleanField('Опубликовано', default=True)
    order = models.PositiveIntegerField('Порядок', default=0)

    class Meta:
        ordering = ['-release_date', '-order']
        verbose_name = 'Запись изменений'
        verbose_name_plural = 'История изменений'

    def __str__(self):
        return f"{self.version} - {self.title}"
