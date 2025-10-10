from django.db import models


class Quiz(models.Model):
  name = models.CharField(max_length=1000)
  points = models.PositiveIntegerField(default=10, verbose_name="Количество DASCOIN за прохождение теста")
  attempt_limit = models.PositiveIntegerField(default=0, verbose_name="Ограничение попыток", help_text="0 = без ограничений")
  pass_threshold = models.PositiveIntegerField(default=70, verbose_name="Проходной балл (%)")
  order = models.PositiveIntegerField(default=0, verbose_name="Порядок в курсе")
  
  # Связь many-to-many с курсами для гибкости
  courses = models.ManyToManyField(
      'courses.Course',
      blank=True,
      related_name='course_quizzes',
      verbose_name="Курсы, в которых используется тест"
  )
  
  class Meta:
    verbose_name = "Тест" # Как будет отображаться в админ панели
    verbose_name_plural = "Тесты" # Отображаться в множественном числе
    ordering = ['name']

    indexes = [models.Index(fields=['name'], name='name_idx')]

  def __str__(self):
    return f"{self.name}" # Так будет отображаться в админ панели


class Question(models.Model):
  SINGLE = 'single'
  MULTIPLE = 'multiple'
  TEXT = 'text'
  MATCH = 'match'
  QUESTION_TYPES = [
      (SINGLE, 'Один правильный ответ'),
      (MULTIPLE, 'Несколько правильных ответов'),
      (TEXT, 'Открытый ответ'),
      (MATCH, 'Соответствие'),
  ]

  quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
  text = models.CharField(max_length=1000)
  question_type = models.CharField(
      max_length=20,
      choices=QUESTION_TYPES,
      default=SINGLE
  )

  class Meta:
    verbose_name = "Вопрос"
    verbose_name_plural = "Вопросы"
    indexes = [
        models.Index(fields=['quiz'], name='question_quiz_idx'),
    ]

  def __str__(self):
    return f"Вопрос {self.text} из теста: {self.quiz}"


class Answer(models.Model):
  question = models.ForeignKey(Question, on_delete=models.CASCADE)
  text = models.CharField(max_length=1000)
  is_correct = models.BooleanField(default=False)
  image = models.ImageField(upload_to='quiz_answers/', null=True, blank=True, verbose_name="Изображение")

  class Meta:
    verbose_name = "Ответ"
    verbose_name_plural = "Ответы"
    indexes = [
        models.Index(fields=['question'], name='answer_question_idx'),
    ]

  def __str__(self):
    return f"Ответ к вопросу: {self.question}"


class QuizAttempt(models.Model):
  """Модель для отслеживания попыток прохождения тестов пользователями"""
  user = models.ForeignKey('auth.User', on_delete=models.CASCADE, verbose_name="Пользователь")
  quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, verbose_name="Тест")
  attempt_number = models.PositiveIntegerField(verbose_name="Номер попытки")
  started_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата начала")
  completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата завершения")
  
  class Meta:
    verbose_name = "Попытка теста"
    verbose_name_plural = "Попытки тестов"
    unique_together = ('user', 'quiz', 'attempt_number')
    indexes = [
      models.Index(fields=['user', 'quiz'], name='quiz_attempt_user_quiz_idx'),
    ]
    
  def __str__(self):
    return f"{self.user.username} - {self.quiz.name} (попытка {self.attempt_number})"


class QuizLock(models.Model):
  """Модель для отслеживания блокировки тестов для пользователей"""
  user = models.ForeignKey('auth.User', on_delete=models.CASCADE, verbose_name="Пользователь")
  quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, verbose_name="Тест")
  is_locked = models.BooleanField(default=False, verbose_name="Заблокирован")
  locked_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата блокировки")
  
  class Meta:
    verbose_name = "Блокировка теста"
    verbose_name_plural = "Блокировки тестов"
    unique_together = ('user', 'quiz')
    indexes = [
      models.Index(fields=['user', 'quiz'], name='quiz_lock_user_quiz_idx'),
    ]
    
  def __str__(self):
    status = "заблокирован" if self.is_locked else "разблокирован"
    return f"{self.user.username} - {self.quiz.name} ({status})"
