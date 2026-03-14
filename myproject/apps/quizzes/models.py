from django.db import models


class Quiz(models.Model):
  name = models.CharField(max_length=1000)
  points = models.PositiveIntegerField(default=10, verbose_name="Количество DASCOIN за прохождение теста")
  attempt_limit = models.PositiveIntegerField(default=0, verbose_name="Ограничение попыток", help_text="0 = без ограничений")
  pass_threshold = models.PositiveIntegerField(default=70, verbose_name="Проходной балл (%)")
  time_limit = models.PositiveIntegerField(default=0, verbose_name="Время на прохождение (минуты)", help_text="0 = без ограничения по времени")
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
  SEQUENCE = 'sequence'
  QUESTION_TYPES = [
      (SINGLE, 'Один правильный ответ'),
      (MULTIPLE, 'Несколько правильных ответов'),
      (TEXT, 'Открытый ответ'),
      (MATCH, 'Соответствие'),
      (SEQUENCE, 'Последовательность'),
  ]

  quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
  text = models.CharField(max_length=1000)
  question_type = models.CharField(
      max_length=20,
      choices=QUESTION_TYPES,
      default=SINGLE
  )
  mentor_instruction = models.TextField(
      blank=True,
      null=True,
      verbose_name="Комментарий для наставника",
      help_text="Текст, который будет отображаться наставнику при проверке открытого вопроса"
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


class Homework(models.Model):
  """
  Модель задания (открытый ответ с возможностью вставки изображений).
  Задания могут быть добавлены как материал к курсу наравне с тестами и уроками.
  """
  name = models.CharField(max_length=1000, verbose_name="Текст задания")
  mentor_comment = models.TextField(
      blank=True,
      null=True,
      verbose_name="Комментарий для наставника",
      help_text="Отображается наставнику при проверке (по клику на иконку ?)"
  )
  order = models.PositiveIntegerField(default=0, verbose_name="Порядок в курсе")
  points = models.PositiveIntegerField(default=10, verbose_name="Количество DASCOIN за выполнение задания")
  created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
  updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
  
  # Связь many-to-many с курсами
  courses = models.ManyToManyField(
      'courses.Course',
      blank=True,
      related_name='course_homeworks',
      verbose_name="Курсы, в которых используется задание"
  )
  
  # Property для совместимости с шаблонами
  @property
  def title(self):
      return self.name
  
  class Meta:
    verbose_name = "Задание"
    verbose_name_plural = "Задания"
    ordering = ['name']

  def __str__(self):
    return f"{self.name}"


class HomeworkSubmission(models.Model):
  """
  Модель ответа пользователя на задание.
  Хранит текст ответа с CKEditor (включая изображения) и статус проверки.
  """
  STATUS_CHOICES = [
      ('pending', 'Ожидает проверки'),
      ('correct', 'Правильно'),
      ('incorrect', 'Неправильно'),
  ]
  
  user = models.ForeignKey('auth.User', on_delete=models.CASCADE, verbose_name="Пользователь")
  homework = models.ForeignKey(Homework, on_delete=models.CASCADE, verbose_name="Задание")
  course = models.ForeignKey(
      'courses.Course',
      on_delete=models.CASCADE,
      null=True,
      blank=True,
      verbose_name="Курс"
  )
  answer_text = models.TextField(verbose_name="Ответ пользователя")
  status = models.CharField(
      max_length=20,
      choices=STATUS_CHOICES,
      default='pending',
      verbose_name="Статус"
  )
  submitted_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата отправки")
  reviewed_by = models.ForeignKey(
      'auth.User',
      on_delete=models.SET_NULL,
      null=True,
      blank=True,
      related_name='reviewed_homeworks',
      verbose_name="Проверено (кем)"
  )
  reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата проверки")
  mentor_feedback = models.TextField(
      blank=True,
      null=True,
      verbose_name="Комментарий наставника к ответу"
  )
  
  class Meta:
    verbose_name = "Ответ на задание"
    verbose_name_plural = "Ответы на задания"
    ordering = ['-submitted_at']
    indexes = [
        models.Index(fields=['user', 'homework'], name='hw_sub_user_hw_idx'),
        models.Index(fields=['status'], name='hw_sub_status_idx'),
        models.Index(fields=['submitted_at'], name='hw_sub_submitted_idx'),
    ]
  
  def __str__(self):
    return f"{self.user.username} - {self.homework.title} ({self.get_status_display()})"


class HomeworkSubmissionImage(models.Model):
  """
  Модель для хранения изображений, прикреплённых к ответу на задание.
  Поддерживает загрузку нескольких изображений к одному ответу.
  """
  submission = models.ForeignKey(
      HomeworkSubmission,
      on_delete=models.CASCADE,
      related_name='images',
      verbose_name="Ответ на задание"
  )
  image = models.ImageField(
      upload_to='homework_submissions/%Y/%m/',
      verbose_name="Изображение"
  )
  uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата загрузки")
  
  class Meta:
    verbose_name = "Изображение к ответу"
    verbose_name_plural = "Изображения к ответам"
    ordering = ['uploaded_at']
  
  def __str__(self):
    return f"Изображение к ответу {self.submission.id}"
