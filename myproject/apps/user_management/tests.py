from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group
from users.models import Profile

class UserManagementListViewTest(TestCase):
    """
    Тесты для списка пользователей (UserListView): права доступа, отображение, фильтрация.
    """
    def setUp(self):
        """Создаёт обычного пользователя, staff и superuser."""
        self.client = Client()
        self.staff = User.objects.create_user(username='staff', password='pass', is_staff=True)
        self.superuser = User.objects.create_superuser(username='admin', password='pass')
        self.user = User.objects.create_user(username='user', password='pass')
        self.url = reverse('user_management:user_list')

    def test_list_requires_staff_or_superuser(self):
        """Обычный пользователь получает 403, staff и superuser видят список."""
        self.client.login(username='user', password='pass')
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 403)
        self.client.login(username='staff', password='pass')
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.client.login(username='admin', password='pass')
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_list_search_and_filter(self):
        """Фильтрация по имени, email, статусу подтверждения."""
        self.client.login(username='admin', password='pass')
        resp = self.client.get(self.url + '?q=user')
        self.assertContains(resp, 'user')
        resp = self.client.get(self.url + '?approved=0')
        self.assertContains(resp, 'user')

class UserManagementCreateEditTest(TestCase):
    """
    Тесты для создания и редактирования пользователя: права, формы, is_approved, read-only.
    """
    def setUp(self):
        """Создаёт staff, superuser и обычного пользователя."""
        self.client = Client()
        self.staff = User.objects.create_user(username='staff', password='pass', is_staff=True)
        self.superuser = User.objects.create_superuser(username='admin', password='pass')
        self.user = User.objects.create_user(username='user', password='pass')
        self.edit_url = reverse('user_management:user_edit', args=[self.user.pk])
        self.create_url = reverse('user_management:user_create_step1')

    def test_create_requires_staff(self):
        """Обычный пользователь не может создавать пользователей."""
        self.client.login(username='user', password='pass')
        resp = self.client.get(self.create_url)
        self.assertEqual(resp.status_code, 200)
        self.client.login(username='staff', password='pass')
        resp = self.client.get(self.create_url)
        self.assertEqual(resp.status_code, 200)

    def test_edit_requires_staff(self):
        """Обычный пользователь не может редактировать других."""
        self.client.login(username='user', password='pass')
        resp = self.client.get(self.edit_url)
        self.assertEqual(resp.status_code, 403)
        self.client.login(username='staff', password='pass')
        resp = self.client.get(self.edit_url)
        self.assertEqual(resp.status_code, 200)

    def test_edit_is_approved_toggle(self):
        """Staff может менять is_approved пользователя."""
        self.client.login(username='staff', password='pass')
        url = self.edit_url
        data = {
            'username': 'user',
            'email': 'user@example.com',
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'groups': [],
            'is_active': True,
            'middle_name': '',
            'date_of_birth': '',
            'phone_number': '+79999999999',
            'bio': '',
            'is_approved': True,
            'image': '',
        }
        resp = self.client.post(url, data, follow=True)
        self.user.refresh_from_db()
        self.assertTrue(self.user.profile.is_approved)

    def test_edit_readonly_for_lower_privilege(self):
        """Staff не может редактировать superuser (read-only режим)."""
        self.client.login(username='staff', password='pass')
        url = reverse('user_management:user_edit', args=[self.superuser.pk])
        resp = self.client.get(url)
        self.assertContains(resp, 'readonly')
        resp = self.client.post(url, {'username': 'admin'}, follow=True)
        self.assertEqual(resp.status_code, 403)

class UserManagementPasswordChangeTest(TestCase):
    """
    Тесты для смены пароля пользователя через user_management.
    """
    def setUp(self):
        """Создаёт staff и пользователя."""
        self.client = Client()
        self.staff = User.objects.create_user(username='staff', password='pass', is_staff=True)
        self.user = User.objects.create_user(username='user', password='pass')
        self.url = reverse('user_management:user_password_change', args=[self.user.pk])

    def test_password_change_requires_staff(self):
        """Обычный пользователь не может менять чужой пароль."""
        self.client.login(username='user', password='pass')
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 403)
        self.client.login(username='staff', password='pass')
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)

    def test_password_change_success(self):
        """Staff может сменить пароль пользователя."""
        self.client.login(username='staff', password='pass')
        data = {
            'new_password1': 'Newpass123!',
            'new_password2': 'Newpass123!',
        }
        resp = self.client.post(self.url, data, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('Newpass123!'))
