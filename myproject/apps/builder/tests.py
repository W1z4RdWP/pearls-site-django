from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from builder.models import CategoryName
from courses.models import Lesson

class BuilderMasterDetailViewTest(TestCase):
    """
    Тесты для master_detail (главная страница базы знаний): права, только чтение, отображение.
    """
    def setUp(self):
        """Создаёт обычного пользователя, staff и superuser."""
        self.client = Client()
        self.staff = User.objects.create_user(username='staff', password='pass', is_staff=True)
        self.superuser = User.objects.create_superuser(username='admin', password='pass')
        self.user = User.objects.create_user(username='user', password='pass')
        self.url = reverse('builder:lesson_master')

    def test_master_detail_requires_login(self):
        """Неавторизованный пользователь получает 403/редирект."""
        resp = self.client.get(self.url)
        self.assertNotEqual(resp.status_code, 200)

    def test_master_detail_staff_and_superuser(self):
        """Staff и superuser видят страницу, могут редактировать."""
        self.client.login(username='staff', password='pass')
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Категории')
        self.client.login(username='admin', password='pass')
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_master_detail_readonly_for_user(self):
        """Обычный пользователь видит только чтение (is_readonly)."""
        self.client.login(username='user', password='pass')
        resp = self.client.get(self.url)
        self.assertContains(resp, 'Категории')
        # Проверяем, что пользователь видит страницу, но без прав редактирования
        self.assertNotIn('Добавить категорию', resp.content.decode('utf-8'))

class BuilderSearchAjaxTest(TestCase):
    """
    Тесты для ajax поиска по категориям и урокам: права, корректность поиска.
    """
    def setUp(self):
        """Создаёт staff и обычного пользователя, категории и уроки."""
        self.client = Client()
        self.staff = User.objects.create_user(username='staff', password='pass', is_staff=True)
        self.user = User.objects.create_user(username='user', password='pass')
        self.cat = CategoryName.objects.create(name='Backend', order=1)
        self.lesson = Lesson.objects.create(title='Django basics', order=1, category=self.cat)
        self.url = reverse('builder:search_tree')

    def test_search_requires_auth(self):
        """Неавторизованный пользователь получает 302/403."""
        resp = self.client.get(self.url, {'query': 'Django'})
        self.assertIn(resp.status_code, [302, 403])

    def test_search_staff_and_user(self):
        """Staff и обычный пользователь могут искать категории и уроки."""
        self.client.login(username='staff', password='pass')
        resp = self.client.get(self.url, {'query': 'Back'})
        self.assertEqual(resp.status_code, 200)
        self.assertIn(self.cat.id, resp.json()['categories'])
        self.client.login(username='user', password='pass')
        resp = self.client.get(self.url, {'query': 'Django'})
        self.assertEqual(resp.status_code, 200)
        self.assertIn(self.lesson.id, resp.json()['lessons'])

class BuilderAjaxPermissionsTest(TestCase):
    """
    Тесты для ajax copy/cut/paste/reorder: права доступа, ошибки.
    """
    def setUp(self):
        """Создаёт staff и обычного пользователя, категорию и урок."""
        self.client = Client()
        self.staff = User.objects.create_user(username='staff', password='pass', is_staff=True)
        self.user = User.objects.create_user(username='user', password='pass')
        self.cat = CategoryName.objects.create(name='Backend', order=1)
        self.lesson = Lesson.objects.create(title='Django basics', order=1, category=self.cat)

    def test_copy_requires_staff(self):
        """Обычный пользователь не может копировать (403)."""
        self.client.login(username='user', password='pass')
        resp = self.client.post('/builder/copy/', {'id': self.cat.id, 'type': 'category'}, content_type='application/json')
        self.assertEqual(resp.status_code, 403)
        self.client.login(username='staff', password='pass')
        resp = self.client.post('/builder/copy/', {'id': self.cat.id, 'type': 'category'}, content_type='application/json')
        self.assertEqual(resp.status_code, 200)

    def test_cut_requires_staff(self):
        """Обычный пользователь не может вырезать (403)."""
        self.client.login(username='user', password='pass')
        resp = self.client.post('/builder/cut/', {'id': self.cat.id, 'type': 'category'}, content_type='application/json')
        self.assertEqual(resp.status_code, 403)

    def test_paste_requires_staff(self):
        """Обычный пользователь не может вставлять (403)."""
        self.client.login(username='user', password='pass')
        resp = self.client.post('/builder/paste/', {'target_category': self.cat.id}, content_type='application/json')
        self.assertEqual(resp.status_code, 403)

    def test_reorder_requires_staff(self):
        """Обычный пользователь не может менять порядок (403)."""
        self.client.login(username='user', password='pass')
        resp = self.client.post('/builder/reorder/', {'parent_id': self.cat.id, 'items': []}, content_type='application/json')
        self.assertEqual(resp.status_code, 403)

class BuilderCRUDTest(TestCase):
    """
    Smoke-тесты на CRUD категорий и уроков: staff может создавать, редактировать, удалять.
    """
    def setUp(self):
        """Создаёт staff и категорию."""
        self.client = Client()
        self.staff = User.objects.create_user(username='staff', password='pass', is_staff=True)
        self.client.login(username='staff', password='pass')
        self.cat = CategoryName.objects.create(name='Backend', order=1)

    def test_create_category(self):
        """Staff может создать категорию через форму."""
        url = reverse('builder:category_add')
        resp = self.client.post(url, {'name': 'NewCat', 'order': 2}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(CategoryName.objects.filter(name='NewCat').exists())

    def test_edit_category(self):
        """Staff может редактировать категорию."""
        url = reverse('builder:category_edit', args=[self.cat.pk])
        resp = self.client.post(url, {'name': 'Backend2', 'order': 1}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.cat.refresh_from_db()
        self.assertEqual(self.cat.name, 'Backend2')

    def test_delete_category(self):
        """Staff может удалить категорию."""
        url = reverse('builder:category_delete', args=[self.cat.pk])
        resp = self.client.post(url, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(CategoryName.objects.filter(pk=self.cat.pk).exists())
