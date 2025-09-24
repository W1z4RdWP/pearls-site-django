from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from courses.models import Course, Lesson

class CoursesCRUDTest(TestCase):
    """
    Smoke-тесты на CRUD курсов и уроков: staff может создавать, редактировать, удалять.
    """


    def setUp(self):
        """Создаёт staff и обычного пользователя."""
        self.client = Client()
        self.staff = User.objects.create_user(username='staff', password='pass', is_staff=True)
        self.user = User.objects.create_user(username='user', password='pass')
        self.client.login(username='staff', password='pass')
        self.course = Course.objects.create(title='TestCourse', slug='testcourse', author=self.staff)


    def test_create_lesson(self):
        """Staff может создать урок через форму."""
        url = reverse('create_lesson', args=[self.course.slug])
        resp = self.client.post(url, {'title': 'Lesson1', 'order': 1, 'course': self.course.pk}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(Lesson.objects.filter(title='Lesson1').exists())


    def test_edit_lesson(self):
        """Staff может редактировать урок."""
        lesson = Lesson.objects.create(title='Lesson2', order=2, course=self.course)
        url = reverse('edit_lesson', args=[lesson.pk])
        resp = self.client.post(url, {'title': 'Lesson2-Edit', 'order': 2, 'course': self.course.pk}, follow=True)
        self.assertEqual(resp.status_code, 200)
        lesson.refresh_from_db()
        self.assertEqual(lesson.title, 'Lesson2-Edit')


    def test_delete_lesson(self):
        """Staff может удалить урок."""
        lesson = Lesson.objects.create(title='Lesson3', order=3, course=self.course)
        url = reverse('delete_lesson', args=[lesson.pk])
        resp = self.client.post(url, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Lesson.objects.filter(pk=lesson.pk).exists())




class CoursesAccessTest(TestCase):
    """
    Тесты на права доступа к курсам и урокам: staff, обычный пользователь, неавторизованный.
    """

    def setUp(self):
        """Создаёт staff, обычного пользователя и курс."""
        self.client = Client()
        self.staff = User.objects.create_user(username='staff', password='pass', is_staff=True)
        self.user = User.objects.create_user(username='user', password='pass')
        self.course = Course.objects.create(title='TestCourse', slug='testcourse', author=self.staff)
        self.lesson = Lesson.objects.create(title='Lesson1', order=1, course=self.course)


    def test_course_detail_access(self):
        """Любой авторизованный пользователь может просматривать курс."""
        self.client.login(username='user', password='pass')
        url = reverse('courses:course_detail', args=[self.course.slug])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'TestCourse')


    def test_lesson_detail_access(self):
        """Любой авторизованный пользователь может просматривать урок."""
        self.client.login(username='user', password='pass')
        url = reverse('courses:lesson_detail', args=[self.course.slug, self.lesson.pk])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Lesson1')


    def test_course_requires_login(self):
        """Неавторизованный пользователь получает 302/403 на курс."""
        url = reverse('courses:course_detail', args=[self.course.slug])
        resp = self.client.get(url)
        self.assertIn(resp.status_code, [302, 403])




class CoursesProgressTest(TestCase):
    """
    Тесты для прогресса пользователя по урокам.
    """

    def setUp(self):
        """Создаёт пользователя, курс и урок."""
        self.client = Client()
        self.user = User.objects.create_user(username='user', password='pass')
        self.course = Course.objects.create(title='TestCourse', slug='testcourse', author=self.user)
        self.lesson = Lesson.objects.create(title='Lesson1', order=1, course=self.course)


    def test_lesson_access(self):
        """Пользователь может получить доступ к уроку."""
        self.client.login(username='user', password='pass')
        url = reverse('courses:lesson_detail', args=[self.course.slug, self.lesson.pk])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Lesson1')
