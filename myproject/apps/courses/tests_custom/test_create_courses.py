from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model

from courses.models import Course
from courses.models import Lesson
from quizzes.models import Quiz
from users.models import Profile


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class CourseCreateAccessTest(TestCase):
    """
    Проверяет доступ к созданию курса:
    - staff/superuser создают успешно,
    - наставник (mentor) не имеет доступа.
    """

    def setUp(self):
        self.client = Client()
        User = get_user_model()
        self.staff = User.objects.create_user(username='staff', password='pass', is_staff=True)
        self.superuser = User.objects.create_superuser(username='admin', password='pass')
        self.mentor = User.objects.create_user(username='mentor', password='pass')
        Profile.objects.get_or_create(user=self.mentor, defaults={'is_mentor': True})
        self.url = reverse('courses:create-course')

    def _course_payload(self, title, slug):
        return {
            'title': title,
            'description': '<p>desc</p>',
            'slug': slug,
            'mentors_time_to_check': 2,
            'certificate': False,
            'is_incident': False,
        }

    def test_staff_can_create_course(self):
        """Staff может создать курс."""
        self.client.login(username='staff', password='pass')
        resp = self.client.post(self.url, self._course_payload('Staff course', 'staff-course'))
        self.assertEqual(resp.status_code, 302)
        course = Course.objects.get(title='Staff course')
        self.assertEqual(course.author, self.staff)

    def test_superuser_can_create_course(self):
        """Superuser может создать курс."""
        self.client.login(username='admin', password='pass')
        resp = self.client.post(self.url, self._course_payload('Super course', 'super-course'))
        self.assertEqual(resp.status_code, 302)
        course = Course.objects.get(title='Super course')
        self.assertEqual(course.author, self.superuser)

    def test_mentor_cannot_create_course(self):
        """Наставник не может создать курс."""
        self.client.login(username='mentor', password='pass')
        resp_get = self.client.get(self.url)
        self.assertEqual(resp_get.status_code, 403)
        resp_post = self.client.post(self.url, self._course_payload('Mentor course', 'mentor-course'))
        self.assertEqual(resp_post.status_code, 403)
        self.assertFalse(Course.objects.filter(title='Mentor course').exists())

    # --- Редактирование курса ---
    def _create_course(self, author, title, slug):
        return Course.objects.create(
            title=title,
            description='desc',
            author=author,
            slug=slug,
            mentors_time_to_check=2,
            certificate=False,
            is_incident=False
        )

    def test_staff_can_edit_course(self):
        """Staff может редактировать курс."""
        course = self._create_course(self.staff, 'Staff course edit', 'staff-course-edit')
        self.client.login(username='staff', password='pass')
        url = reverse('courses:edit_course', args=[course.slug])
        resp = self.client.post(url, self._course_payload('Staff course edit v2', course.slug))
        self.assertEqual(resp.status_code, 302)
        course.refresh_from_db()
        self.assertEqual(course.title, 'Staff course edit v2')

    def test_superuser_can_edit_course(self):
        """Superuser может редактировать курс."""
        course = self._create_course(self.superuser, 'Super course edit', 'super-course-edit')
        self.client.login(username='admin', password='pass')
        url = reverse('courses:edit_course', args=[course.slug])
        resp = self.client.post(url, self._course_payload('Super course edit v2', course.slug))
        self.assertEqual(resp.status_code, 302)
        course.refresh_from_db()
        self.assertEqual(course.title, 'Super course edit v2')


    # --- Удаление курса ---
    def test_staff_can_delete_course(self):
        """Staff может удалить курс."""
        course = self._create_course(self.staff, 'Staff delete', 'staff-delete')
        self.client.login(username='staff', password='pass')
        url = reverse('courses:delete_course', args=[course.slug])
        resp = self.client.post(url, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Course.objects.filter(pk=course.pk).exists())

    def test_superuser_can_delete_course(self):
        """Superuser может удалить курс."""
        course = self._create_course(self.superuser, 'Super delete', 'super-delete')
        self.client.login(username='admin', password='pass')
        url = reverse('courses:delete_course', args=[course.slug])
        resp = self.client.post(url, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Course.objects.filter(pk=course.pk).exists())

    # --- Материалы курса ---
    def test_staff_can_add_and_remove_materials(self):
        """Staff добавляет и удаляет уроки/тесты из материалов курса."""
        course = self._create_course(self.staff, 'Materials staff', 'materials-staff')
        self.client.login(username='staff', password='pass')

        lesson = Lesson.objects.create(
            title='Lesson A',
            content='l',
            order=1,
            category=None,
            required_time=5,
        )
        quiz = Quiz.objects.create(name='Quiz A', order=2)

        lesson.courses.add(course)
        quiz.courses.add(course)

        materials = course.get_course_materials()
        self.assertEqual(len(materials), 2)
        self.assertEqual({m['title'] for m in materials}, {'Lesson A', 'Quiz A'})

        lesson.courses.remove(course)
        quiz.courses.remove(course)
        self.assertEqual(course.get_course_materials(), [])

    def test_superuser_can_add_and_remove_materials(self):
        """Superuser добавляет и удаляет уроки/тесты из материалов курса."""
        course = self._create_course(self.superuser, 'Materials super', 'materials-super')
        self.client.login(username='admin', password='pass')

        lesson = Lesson.objects.create(
            title='Lesson B',
            content='l2',
            order=1,
            category=None,
            required_time=6,
        )
        quiz = Quiz.objects.create(name='Quiz B', order=2)

        lesson.courses.add(course)
        quiz.courses.add(course)

        materials = course.get_course_materials()
        self.assertEqual(len(materials), 2)
        self.assertEqual({m['title'] for m in materials}, {'Lesson B', 'Quiz B'})

        lesson.courses.remove(course)
        quiz.courses.remove(course)
        self.assertEqual(course.get_course_materials(), [])


