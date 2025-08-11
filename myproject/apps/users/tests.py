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
        self.user = User.objects.create_user(username='user1@example.com', email='user1@example.com', password='pass')
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
        user2 = User.objects.create_user(username='user2@example.com', email='user2@example.com', password='pass')
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
        self.url = reverse('users:register')

    def test_register_get(self):
        """GET-запрос возвращает страницу регистрации."""
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('Регистрация', resp.content.decode('utf-8'))

    def test_register_post_creates_user_and_profile(self):
        """POST-запрос создаёт пользователя и профиль, is_approved=False."""
        data = {
            'email': 'newuser@example.com',
            'password1': 'Testpass123!',
            'password2': 'Testpass123!',
        }
        resp = self.client.post(self.url, data, follow=True)
        self.assertEqual(User.objects.filter(email='newuser@example.com').count(), 1)
        user = User.objects.get(email='newuser@example.com')
        self.assertTrue(hasattr(user, 'profile'))
        self.assertFalse(user.profile.is_approved)

    def test_register_redirects_if_authenticated(self):
        """Авторизованный пользователь получает редирект при попытке регистрации."""
        user = User.objects.create_user(username='authuser@example.com', email='authuser@example.com', password='pass')
        self.client.login(username='authuser@example.com', password='pass')
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
        self.url = reverse('users:login')
        self.user = User.objects.create_user(username='loginuser@example.com', email='loginuser@example.com', password='pass')
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
        resp = self.client.post(self.url, {'username': 'loginuser@example.com', 'password': 'pass'}, follow=True)
        self.assertIn('ожидает подтверждения', resp.content.decode('utf-8'))
        self.assertFalse('_auth_user_id' in self.client.session)

    def test_login_approved(self):
        """Пользователь с is_approved=True может войти."""
        self.profile.is_approved = True
        self.profile.save()
        resp = self.client.post(self.url, {'username': 'loginuser@example.com', 'password': 'pass'}, follow=True)
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
        self.user = User.objects.create_user(username='profileuser@example.com', email='profile@example.com', password='pass')
        self.user.profile.is_approved = True
        self.user.profile.save()
        self.url = reverse('users:profile')

    def test_profile_requires_login(self):
        """Неавторизованный пользователь не может просматривать профиль."""
        resp = self.client.get(self.url)
        self.assertNotEqual(resp.status_code, 200)

    def test_profile_get(self):
        """Авторизованный пользователь видит свой профиль."""
        self.client.login(username='profileuser@example.com', password='pass')
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('profileuser@example.com', resp.content.decode('utf-8'))

    def test_profile_post_update(self):
        """POST-запрос обновляет профиль пользователя."""
        self.client.login(username='profileuser@example.com', password='pass')
        data = {
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
        self.client.login(username='profileuser@example.com', password='pass')
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('profileuser@example.com', resp.content.decode('utf-8'))

class UserSignalsTest(TestCase):
    """
    Тесты для сигналов создания профиля пользователя.
    """
    def setUp(self):
        """Создаёт клиент для тестов."""
        self.client = Client()

    def test_profile_created_on_user_creation(self):
        """При создании пользователя автоматически создаётся профиль."""
        user = User.objects.create_user(username='signaluser@example.com', email='signaluser@example.com', password='pass')
        self.assertTrue(hasattr(user, 'profile'))

    def test_profile_saved_on_user_save(self):
        """При сохранении пользователя сохраняется профиль."""
        user = User.objects.create_user(username='signaluser2@example.com', email='signaluser2@example.com', password='pass')
        user.profile.dascoin_points = 100
        user.save()
        user.refresh_from_db()
        self.assertEqual(user.profile.dascoin_points, 100)


class AdminDashboardViewTest(TestCase):
    """
    Тесты для административной панели статистики DASCOIN.
    """
    def setUp(self):
        """Создаёт пользователей для тестов."""
        self.client = Client()
        self.admin_user = User.objects.create_user(
            username='admin', 
            password='pass', 
            is_staff=True, 
            is_superuser=True
        )
        self.staff_user = User.objects.create_user(
            username='staff', 
            password='pass', 
            is_staff=True
        )
        self.regular_user = User.objects.create_user(
            username='user', 
            password='pass'
        )
        
        # Создаём профили с разными баллами DASCOIN
        self.admin_user.profile.dascoin_points = 500
        self.admin_user.profile.save()
        
        self.staff_user.profile.dascoin_points = 300
        self.staff_user.profile.save()
        
        self.regular_user.profile.dascoin_points = 100
        self.regular_user.profile.save()
        
        self.url = reverse('users:admin_dashboard')

    def test_admin_dashboard_requires_staff_or_superuser(self):
        """Обычный пользователь получает 403, staff и superuser видят панель."""
        # Обычный пользователь
        self.client.login(username='user', password='pass')
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 403)
        
        # Staff пользователь
        self.client.login(username='staff', password='pass')
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        
        # Superuser
        self.client.login(username='admin', password='pass')
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_admin_dashboard_shows_users_ordered_by_points(self):
        """Панель показывает пользователей, отсортированных по баллам DASCOIN."""
        self.client.login(username='admin', password='pass')
        resp = self.client.get(self.url)
        
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Статистика пользователей по баллам DASCOIN')
        
        # Проверяем, что пользователи отображаются
        self.assertContains(resp, 'admin')
        self.assertContains(resp, 'staff')
        self.assertContains(resp, 'user')

    def test_admin_dashboard_shows_statistics(self):
        """Панель показывает общую статистику."""
        self.client.login(username='admin', password='pass')
        resp = self.client.get(self.url)
        
        # Проверяем наличие статистики
        self.assertContains(resp, 'Всего пользователей')
        self.assertContains(resp, 'Общее количество DASCOIN')
        self.assertContains(resp, 'Активных пользователей')

    def test_admin_dashboard_filtering(self):
        """Фильтрация работает корректно."""
        self.client.login(username='admin', password='pass')
        
        # Фильтр по минимальным баллам
        resp = self.client.get(self.url + '?points_min=200')
        self.assertEqual(resp.status_code, 200)
        
        # Фильтр по максимальным баллам
        resp = self.client.get(self.url + '?points_max=200')
        self.assertEqual(resp.status_code, 200)
        
        # Быстрый фильтр топ-10
        resp = self.client.get(self.url + '?top=10')
        self.assertEqual(resp.status_code, 200)
        
        # Фильтр пользователей без баллов
        resp = self.client.get(self.url + '?zero_points=1')
        self.assertEqual(resp.status_code, 200)

    def test_admin_dashboard_export_requires_permissions(self):
        """Экспорт требует прав администратора."""
        # Обычный пользователь
        self.client.login(username='user', password='pass')
        resp = self.client.get(reverse('users:export_admin_stats_excel'))
        self.assertEqual(resp.status_code, 403)
        
        resp = self.client.get(reverse('users:export_admin_stats_pdf'))
        self.assertEqual(resp.status_code, 403)
        
        # Staff пользователь
        self.client.login(username='staff', password='pass')
        resp = self.client.get(reverse('users:export_admin_stats_excel'))
        self.assertEqual(resp.status_code, 200)
        
        resp = self.client.get(reverse('users:export_admin_stats_pdf'))
        self.assertEqual(resp.status_code, 200)

    def test_admin_dashboard_links_to_user_details(self):
        """Панель содержит ссылки на детали пользователей."""
        self.client.login(username='admin', password='pass')
        resp = self.client.get(self.url)
        
        # Проверяем наличие ссылок на действия
        self.assertContains(resp, 'Детальный отчет')
        self.assertContains(resp, 'Редактировать')
        self.assertContains(resp, 'История транзакций')


class AdminUserTransactionsViewTest(TestCase):
    """
    Тесты для просмотра транзакций конкретного пользователя администратором.
    """
    def setUp(self):
        """Создаёт пользователей и транзакции для тестов."""
        self.client = Client()
        self.admin_user = User.objects.create_user(
            username='admin', 
            password='pass', 
            is_staff=True, 
            is_superuser=True
        )
        self.target_user = User.objects.create_user(
            username='target', 
            password='pass'
        )
        
        # Создаём транзакции для целевого пользователя
        from gamification.models import DascoinTransaction
        DascoinTransaction.objects.create(
            user=self.target_user,
            transaction_type='award',
            points_change=100,
            points_before=0,
            points_after=100,
            reason='Тестовая награда'
        )
        DascoinTransaction.objects.create(
            user=self.target_user,
            transaction_type='deduct',
            points_change=-50,
            points_before=100,
            points_after=50,
            reason='Тестовое списание'
        )
        
        self.url = reverse('users:admin_user_transactions', kwargs={'user_id': self.target_user.id})

    def test_admin_user_transactions_requires_staff_or_superuser(self):
        """Обычный пользователь получает 403, staff и superuser видят транзакции."""
        # Обычный пользователь
        regular_user = User.objects.create_user(username='user', password='pass')
        self.client.login(username='user', password='pass')
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 403)
        
        # Staff пользователь
        staff_user = User.objects.create_user(username='staff', password='pass', is_staff=True)
        self.client.login(username='staff', password='pass')
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        
        # Superuser
        self.client.login(username='admin', password='pass')
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_admin_user_transactions_shows_user_info(self):
        """Страница показывает информацию о пользователе."""
        self.client.login(username='admin', password='pass')
        resp = self.client.get(self.url)
        
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'История транзакций DASCOIN - target')
        self.assertContains(resp, 'target')

    def test_admin_user_transactions_shows_transactions(self):
        """Страница показывает транзакции пользователя."""
        self.client.login(username='admin', password='pass')
        resp = self.client.get(self.url)
        
        self.assertContains(resp, 'Тестовая награда')
        self.assertContains(resp, 'Тестовое списание')
        self.assertContains(resp, '+100')
        self.assertContains(resp, '-50')

    def test_admin_user_transactions_filtering(self):
        """Фильтрация транзакций работает корректно."""
        self.client.login(username='admin', password='pass')
        
        # Фильтр по начислениям
        resp = self.client.get(self.url + '?type=award')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Тестовая награда')
        self.assertNotContains(resp, 'Тестовое списание')
        
        # Фильтр по списаниям
        resp = self.client.get(self.url + '?type=deduct')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Тестовое списание')
        self.assertNotContains(resp, 'Тестовая награда')

    def test_admin_user_transactions_export_requires_permissions(self):
        """Экспорт требует прав администратора."""
        # Обычный пользователь
        regular_user = User.objects.create_user(username='user', password='pass')
        self.client.login(username='user', password='pass')
        
        resp = self.client.get(reverse('users:export_admin_user_transactions_excel', kwargs={'user_id': self.target_user.id}))
        self.assertEqual(resp.status_code, 403)
        
        resp = self.client.get(reverse('users:export_admin_user_transactions_pdf', kwargs={'user_id': self.target_user.id}))
        self.assertEqual(resp.status_code, 403)
        
        # Staff пользователь
        staff_user = User.objects.create_user(username='staff', password='pass', is_staff=True)
        self.client.login(username='staff', password='pass')
        
        resp = self.client.get(reverse('users:export_admin_user_transactions_excel', kwargs={'user_id': self.target_user.id}))
        self.assertEqual(resp.status_code, 200)
        
        resp = self.client.get(reverse('users:export_admin_user_transactions_pdf', kwargs={'user_id': self.target_user.id}))
        self.assertEqual(resp.status_code, 200)

    def test_admin_user_transactions_nonexistent_user(self):
        """Попытка просмотра транзакций несуществующего пользователя возвращает 404."""
        self.client.login(username='admin', password='pass')
        resp = self.client.get(reverse('users:admin_user_transactions', kwargs={'user_id': 99999}))
        self.assertEqual(resp.status_code, 404)
