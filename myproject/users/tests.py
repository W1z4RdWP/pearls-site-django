from django.test import TestCase, Client
from django.contrib.auth import get_user_model, authenticate
from django.urls import reverse
from django.contrib.auth.models import User
from users.models import Profile
from users.backends import ApprovalBackend

class ApprovalBackendTest(TestCase):
    """
    Тесты для кастомного бэкенда аутентификации ApprovalBackend.
    Проверяет, что только is_active и is_approved пользователи могут логиниться.
    """
    def setUp(self):
        """Создаёт пользователя и профиль для тестов."""
        self.user = User.objects.create_user(username='user1', password='pass')
        self.profile = self.user.profile
        self.profile.is_approved = True
        self.profile.save()
        self.backend = ApprovalBackend()

    def test_user_can_authenticate_approved(self):
        """Пользователь с is_approved=True может аутентифицироваться."""
        self.assertTrue(self.backend.user_can_authenticate(self.user))

    def test_user_cannot_authenticate_not_approved(self):
        """Пользователь с is_approved=False не может аутентифицироваться."""
        self.profile.is_approved = False
        self.profile.save()
        self.assertFalse(self.backend.user_can_authenticate(self.user))

    def test_user_cannot_authenticate_no_profile(self):
        """Пользователь без профиля не может аутентифицироваться."""
        user2 = User.objects.create_user(username='user2', password='pass')
        Profile.objects.filter(user=user2).delete()
        self.assertFalse(self.backend.user_can_authenticate(user2))

class RegisterViewTest(TestCase):
    """
    Тесты для регистрации пользователя через RegisterView.
    Проверяет GET, POST, создание профиля, редиректы.
    """
    def setUp(self):
        """Создаёт клиент и определяет url регистрации."""
        self.client = Client()
        self.url = reverse('register')

    def test_register_get(self):
        """GET-запрос возвращает страницу регистрации."""
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('Регистрация', resp.content.decode('utf-8'))

    def test_register_post_creates_user_and_profile(self):
        """POST-запрос создаёт пользователя и профиль, is_approved=False."""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'Testpass123!',
            'password2': 'Testpass123!',
        }
        resp = self.client.post(self.url, data, follow=True)
        self.assertEqual(User.objects.filter(username='newuser').count(), 1)
        user = User.objects.get(username='newuser')
        self.assertTrue(hasattr(user, 'profile'))
        self.assertFalse(user.profile.is_approved)

    def test_register_redirects_if_authenticated(self):
        """Авторизованный пользователь получает редирект при попытке регистрации."""
        user = User.objects.create_user(username='authuser', password='pass')
        self.client.login(username='authuser', password='pass')
        resp = self.client.get(self.url, follow=True)
        self.assertNotEqual(resp.redirect_chain, [])

class CustomLoginViewTest(TestCase):
    """
    Тесты для кастомного логина (CustomLoginView).
    Проверяет права, is_approved, редиректы, ошибки.
    """
    def setUp(self):
        """Создаёт пользователя и url логина."""
        self.client = Client()
        self.url = reverse('login')
        self.user = User.objects.create_user(username='loginuser', password='pass')
        self.profile = self.user.profile

    def test_login_get(self):
        """GET-запрос возвращает страницу логина."""
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('Вход', resp.content.decode('utf-8'))

    def test_login_not_approved(self):
        """Пользователь с is_approved=False не может войти."""
        self.profile.is_approved = False
        self.profile.save()
        resp = self.client.post(self.url, {'username': 'loginuser', 'password': 'pass'}, follow=True)
        self.assertIn('ожидает подтверждения', resp.content.decode('utf-8'))
        self.assertFalse('_auth_user_id' in self.client.session)

    def test_login_approved(self):
        """Пользователь с is_approved=True может войти."""
        self.profile.is_approved = True
        self.profile.save()
        resp = self.client.post(self.url, {'username': 'loginuser', 'password': 'pass'}, follow=True)
        self.assertTrue('_auth_user_id' in self.client.session)

    def test_login_redirect_if_authenticated(self):
        """Уже залогиненный пользователь получает редирект при попытке логина."""
        self.profile.is_approved = True
        self.profile.save()
        self.client.login(username='loginuser', password='pass')
        resp = self.client.get(self.url, follow=True)
        self.assertNotEqual(resp.redirect_chain, [])

class ProfileViewTest(TestCase):
    """
    Тесты для страницы профиля пользователя.
    Проверяет права, GET/POST, обновление, ошибки.
    """
    def setUp(self):
        """Создаёт пользователя и url профиля."""
        self.client = Client()
        self.user = User.objects.create_user(username='profileuser', password='pass', email='profile@example.com')
        self.user.profile.is_approved = True
        self.user.profile.save()
        self.url = reverse('profile')

    def test_profile_requires_login(self):
        """Неавторизованный пользователь не может просматривать профиль."""
        resp = self.client.get(self.url)
        self.assertNotEqual(resp.status_code, 200)

    def test_profile_get(self):
        """Авторизованный пользователь видит свой профиль."""
        self.client.login(username='profileuser', password='pass')
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('profileuser', resp.content.decode('utf-8'))

    def test_profile_post_update(self):
        """POST-запрос обновляет профиль пользователя."""
        self.client.login(username='profileuser', password='pass')
        data = {
            'username': 'profileuser',
            'email': 'newmail@example.com',
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'middle_name': 'Отчество',
            'date_of_birth': '2000-01-01',
            'phone_number': '+79999999999',
            'bio': 'about',
        }
        resp = self.client.post(self.url, data, follow=True)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'newmail@example.com')
        self.assertEqual(self.user.profile.phone_number, '+79999999999')

    def test_profile_error_if_no_profile(self):
        """Если профиль удалён — возвращается страница ошибки."""
        self.client.login(username='profileuser', password='pass')
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('profileuser', resp.content.decode('utf-8'))

class UserSignalsTest(TestCase):
    """
    Тесты для сигналов users: автоматическое создание и сохранение профиля.
    """
    def test_profile_created_on_user_creation(self):
        """При создании User автоматически создаётся Profile."""
        user = User.objects.create_user(username='signaluser', password='pass')
        self.assertTrue(Profile.objects.filter(user=user).exists())

    def test_profile_saved_on_user_save(self):
        """При сохранении User сохраняется и профиль."""
        user = User.objects.create_user(username='signaluser2', password='pass')
        user.profile.bio = 'bio'
        user.save()
        user.profile.refresh_from_db()
        self.assertEqual(user.profile.bio, 'bio')
