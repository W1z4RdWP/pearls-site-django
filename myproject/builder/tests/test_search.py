from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from builder.models import CategoryName
from courses.models import Lesson

class SearchTreeAjaxTest(TestCase):
    """
    Тестирует поиск по категориям и урокам через /builder/search/
    """
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='admin', password='123', is_staff=True)
        self.client = Client()
        self.client.login(username='admin', password='123')
        # Категории
        self.cat1 = CategoryName.objects.create(name='Backend', order=1)
        self.cat2 = CategoryName.objects.create(name='Frontend', order=2)
        # Уроки
        self.lesson1 = Lesson.objects.create(title='Django basics', order=1, category=self.cat1)
        self.lesson2 = Lesson.objects.create(title='React intro', order=2, category=self.cat2)
        self.lesson3 = Lesson.objects.create(title='Без категории', order=1, category=None)

    def test_search_category(self):
        resp = self.client.get('/builder/search/', {'query': 'back'})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn(self.cat1.id, data['categories'])
        self.assertNotIn(self.cat2.id, data['categories'])

    def test_search_lesson(self):
        resp = self.client.get('/builder/search/', {'query': 'django'})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn(self.lesson1.id, data['lessons'])
        self.assertNotIn(self.lesson2.id, data['lessons'])

    def test_search_case_insensitive(self):
        resp = self.client.get('/builder/search/', {'query': 'REACT'})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn(self.lesson2.id, data['lessons'])

    def test_search_no_results(self):
        resp = self.client.get('/builder/search/', {'query': 'qwerty'})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data['categories'], [])
        self.assertEqual(data['lessons'], []) 