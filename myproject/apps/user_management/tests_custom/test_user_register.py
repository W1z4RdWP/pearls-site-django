from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from unittest.mock import patch

from users.models import Role


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class UserRegisterFlowTest(TestCase):
    """
    Проверяет двухшаговое создание пользователя:
    - доступ только для staff/superuser;
    - шаг 1 создаёт учетку и редиректит на шаг 2;
    - шаг 2 сохраняет профиль и группы пользователя.
    """

    def setUp(self):
        self.client = Client()
        self.User = get_user_model()

        self.staff = self.User.objects.create_user(
            username='staff', email='staff@example.com', password='pass', is_staff=True
        )
        self.superuser = self.User.objects.create_superuser(
            username='admin', email='admin@example.com', password='pass'
        )
        self.regular = self.User.objects.create_user(
            username='user', email='user@example.com', password='pass'
        )

        self.step1_url = reverse('user_management:user_create_step1')
        self.step2_url = reverse('user_management:user_create_step2')
        self.user_list_url = reverse('user_management:user_list')

    def test_non_staff_cannot_access_user_creation(self):
        """Обычный пользователь получает 403 при попытке доступа к шагу 1."""
        self.client.login(username='user', password='pass')
        response = self.client.get(self.step1_url)
        self.assertEqual(response.status_code, 403)

    def test_staff_step1_creates_user_and_redirects_to_step2(self):
        """Staff создаёт учетку на шаге 1 и получает редирект на шаг 2."""
        self.client.login(username='staff', password='pass')
        payload = {
            'email': 'newuser@example.com',
            'password1': 'StrongPass123',
            'password2': 'StrongPass123',
        }
        response = self.client.post(self.step1_url, data=payload)
        self.assertRedirects(response, self.step2_url)

        created_user = self.User.objects.get(email='newuser@example.com')
        session = self.client.session
        self.assertEqual(session.get('user_create_step1_user_id'), created_user.id)
        self.assertEqual(session.get('user_password'), payload['password1'])

    @patch('user_management.views.send_user_credentials_email', return_value=True)
    def test_full_flow_creates_profile_and_assigns_groups(self, mock_send):
        """Полный поток: staff проходит оба шага, профиль и группы сохраняются."""
        self.client.login(username='staff', password='pass')
        password = 'StrongPass123'
        step1_payload = {
            'email': 'flowuser@example.com',
            'password1': password,
            'password2': password,
        }
        self.client.post(self.step1_url, data=step1_payload)
        user = self.User.objects.get(email='flowuser@example.com')

        group = Group.objects.create(name='QA')
        role = Role.objects.create(name='Manager')

        step2_payload = {
            'first_name': 'Ivan',
            'last_name': 'Ivanov',
            'middle_name': 'Ivanovich',
            'role': role.id,
            'date_of_birth': '2000-01-01',
            'phone_number': '+70000000000',
            'phone_arbitrary_format': '',
            'bio': 'Bio',
            'is_approved': 'on',
            'is_mentor': 'on',
            'groups': [str(group.id)],
        }
        response = self.client.post(self.step2_url, data=step2_payload)
        self.assertRedirects(response, self.user_list_url)

        user.refresh_from_db()
        profile = user.profile

        self.assertEqual(user.first_name, 'Ivan')
        self.assertEqual(user.last_name, 'Ivanov')
        self.assertEqual(profile.middle_name, 'Ivanovich')
        self.assertEqual(profile.role, role)
        self.assertTrue(profile.is_approved)
        self.assertTrue(profile.is_mentor)
        self.assertIn(group, user.groups.all())
        self.assertNotIn('user_create_step1_user_id', self.client.session)
        self.assertNotIn('user_password', self.client.session)

        mock_send.assert_called_once_with(user, password)
