from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model

from builder.models import CategoryName, LessonVersion
from courses.models import Lesson
from users.models import Profile


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class LessonCreateUpdateTest(TestCase):
    """
    Проверяет создание и редактирование уроков с учётом прав доступа и версионирования.
    """

    def setUp(self):
        self.client = Client()
        User = get_user_model()
        self.staff = User.objects.create_user(username='staff', password='pass', is_staff=True)
        self.superuser = User.objects.create_superuser(username='admin', password='pass')
        self.mentor = User.objects.create_user(username='mentor', password='pass')
        Profile.objects.get_or_create(user=self.mentor, defaults={'is_mentor': True})

        self.root_cat = CategoryName.objects.create(name='Root', order=1)
        self.sub_cat = CategoryName.objects.create(name='Sub', order=1, parent=self.root_cat)

    def _login(self, user):
        self.client.logout()
        self.client.login(username=user.username, password='pass')

    def test_staff_can_create_lesson_without_category(self):
        """Staff может создать урок без категории."""
        self._login(self.staff)
        url = reverse('builder:lesson_add')
        resp = self.client.post(url, {
            'title': 'No category lesson',
            'content': '<p>text</p>',
            'required_time': 5,
            'category': '',
            'final_quiz': '',
        }, follow=True)
        self.assertEqual(resp.status_code, 200)
        lesson = Lesson.objects.get(title='No category lesson')
        self.assertIsNone(lesson.category)
        self.assertEqual(LessonVersion.objects.filter(lesson=lesson).count(), 1)

    def test_superuser_can_create_lesson_in_category(self):
        """Superuser может создать урок в выбранной категории или подкатегории."""
        self._login(self.superuser)
        url = reverse('builder:lesson_add_with_category', args=[self.sub_cat.pk])
        resp = self.client.post(url, {
            'title': 'Subcat lesson',
            'content': '<p>content</p>',
            'required_time': 7,
            'category': self.sub_cat.pk,
            'final_quiz': '',
        }, follow=True)
        self.assertEqual(resp.status_code, 200)
        lesson = Lesson.objects.get(title='Subcat lesson')
        self.assertEqual(lesson.category, self.sub_cat)
        self.assertEqual(LessonVersion.objects.filter(lesson=lesson).count(), 1)

    def test_staff_can_edit_lesson_and_versions_increment(self):
        """Staff может редактировать урок (без категории или в подкатегории) и создаётся новая версия."""
        # Создаём урок без категории
        self._login(self.staff)
        create_url = reverse('builder:lesson_add')
        self.client.post(create_url, {
            'title': 'Editable lesson',
            'content': '<p>v1</p>',
            'required_time': 10,
            'category': '',
            'final_quiz': '',
        }, follow=True)
        lesson = Lesson.objects.get(title='Editable lesson')
        self.assertEqual(LessonVersion.objects.filter(lesson=lesson).count(), 1)

        # Редактируем, переносим в подкатегорию и меняем заголовок/контент
        edit_url = reverse('builder:lesson_edit', args=[lesson.pk])
        resp = self.client.post(edit_url, {
            'title': 'Editable lesson v2',
            'content': '<p>v2</p>',
            'order': lesson.order,
            'required_time': lesson.required_time,
            'category': self.sub_cat.pk,
            'final_quiz': '',
        }, follow=True)
        self.assertEqual(resp.status_code, 200)

        lesson.refresh_from_db()
        self.assertEqual(lesson.title, 'Editable lesson v2')
        self.assertEqual(lesson.category, self.sub_cat)

        versions = LessonVersion.objects.filter(lesson=lesson).order_by('-version')
        self.assertEqual(versions.count(), 2)
        self.assertEqual(versions.first().version, 2)
        self.assertEqual(versions.first().title, 'Editable lesson v2')

    def test_mentor_cannot_create_lesson(self):
        """Наставник не может создавать уроки."""
        self._login(self.mentor)
        url = reverse('builder:lesson_add')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 403)
        resp = self.client.post(url, {
            'title': 'Forbidden lesson',
            'content': '<p>x</p>',
            'required_time': 5,
            'category': '',
            'final_quiz': '',
        })
        self.assertEqual(resp.status_code, 403)
        self.assertFalse(Lesson.objects.filter(title='Forbidden lesson').exists())

    def test_mentor_cannot_edit_lesson(self):
        """Наставник не может редактировать уроки."""
        # Подготовим урок
        self._login(self.staff)
        create_url = reverse('builder:lesson_add')
        self.client.post(create_url, {
            'title': 'Mentor forbidden edit',
            'content': '<p>v1</p>',
            'required_time': 8,
            'category': '',
            'final_quiz': '',
        }, follow=True)
        lesson = Lesson.objects.get(title='Mentor forbidden edit')

        # Попытка наставника
        self._login(self.mentor)
        edit_url = reverse('builder:lesson_edit', args=[lesson.pk])
        resp = self.client.get(edit_url)
        self.assertEqual(resp.status_code, 403)
        resp = self.client.post(edit_url, {
            'title': 'Mentor edit attempt',
            'content': '<p>v2</p>',
            'order': lesson.order,
            'required_time': lesson.required_time,
            'category': '',
            'final_quiz': '',
        })
        self.assertEqual(resp.status_code, 403)
        lesson.refresh_from_db()
        self.assertEqual(lesson.title, 'Mentor forbidden edit')
        self.assertEqual(LessonVersion.objects.filter(lesson=lesson).count(), 1)

