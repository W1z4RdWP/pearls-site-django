from django.contrib.auth import get_user_model
from django.test import TestCase

from builder.models import Incident
from builder.signals import check_and_update_incident_studies_completed_status
from courses.models import Course
from myapp.models import UserCourse, QuizResult, UserAnswer
from quizzes.models import Question, Quiz


class IncidentStatusesFromCourseProgressTest(TestCase):
    """
    Проверка смены статусов инцидента в зависимости от прогресса по курсу-инциденту.
    """

    def setUp(self):
        User = get_user_model()

        # Пользователь, зафиксировавший инцидент
        self.author = User.objects.create_user(
            username="author",
            password="pass",
            email="author@test.com",
            is_staff=True,
        )

        # Назначенные сотрудники
        self.employee1 = User.objects.create_user(
            username="employee1",
            password="pass",
            email="employee1@test.com",
        )
        self.employee2 = User.objects.create_user(
            username="employee2",
            password="pass",
            email="employee2@test.com",
        )

        # Курс-инцидент
        self.course = Course.objects.create(
            title="Test incident course",
            description="",
            author=self.author,
            is_incident=True,
        )

        # Сам инцидент
        self.incident = Incident.objects.create(
            title="Test incident",
            description="",
            incident_type="educational",
            user=self.author,
            status="assigned",
            course=self.course,
        )
        self.incident.assigned_to.add(self.employee1, self.employee2)

    def test_incident_becomes_resolved_when_all_assigned_completed_and_no_pending_reviews(self):
        """
        После завершения всеми назначенными сотрудниками обучения по инциденту,
        при отсутствии ожидающих проверки тестов/заданий статус инцидента становится «Завершён».
        """
        # Всем назначенным пользователям курс завершен
        UserCourse.objects.create(
            user=self.employee1,
            course=self.course,
            status="completed",
        )
        UserCourse.objects.create(
            user=self.employee2,
            course=self.course,
            status="completed",
        )

        # Не создаём ни результатов тестов в статусе pending, ни открытых ответов

        check_and_update_incident_studies_completed_status(self.incident)
        self.incident.refresh_from_db()

        self.assertEqual(
            self.incident.status,
            "resolved",
            "Инцидент должен перейти в статус 'resolved' после завершения курса всеми назначенными пользователями, "
            "если нет ожидающих проверки тестов или заданий.",
        )

    def test_incident_becomes_studies_completed_when_only_pending_open_answers_left(self):
        """
        Если по курсу-инциденту все материалы пройдены назначенными пользователями,
        но остались тесты/задания с открытыми ответами в статусе pending (ожидают проверки наставника),
        статус инцидента должен быть «Обучение завершено».
        """
        # Назначенный пользователь завершил курс
        # Для простоты используем одного сотрудника, второй тоже завершил курс
        UserCourse.objects.create(
            user=self.employee1,
            course=self.course,
            status="completed",
        )
        UserCourse.objects.create(
            user=self.employee2,
            course=self.course,
            status="completed",
        )

        # Создаём тест с открытым вопросом и результат в статусе pending
        quiz = Quiz.objects.create(name="Incident quiz")
        text_question = Question.objects.create(
            quiz=quiz,
            text="Open question",
            question_type=Question.TEXT,
        )

        quiz_result = QuizResult.objects.create(
            user=self.employee1,
            quiz_title=quiz.name,
            course=self.course,
            score=0,
            total_questions=1,
            percent=0,
            passed=False,
            status="pending",
        )

        # Открытый ответ, требующий проверки (is_correct=None)
        UserAnswer.objects.create(
            user=self.employee1,
            quiz_result=quiz_result,
            question=text_question,
            answer_text="Some text answer",
            is_correct=None,
        )

        check_and_update_incident_studies_completed_status(self.incident)
        self.incident.refresh_from_db()

        self.assertEqual(
            self.incident.status,
            "studies_completed",
            "Инцидент должен перейти в статус 'studies_completed', если все материалы курса пройдены, "
            "а остались только открытые ответы/задания, ожидающие проверки наставника.",
        )

