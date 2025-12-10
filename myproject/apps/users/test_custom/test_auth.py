from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.messages import get_messages
from django.test import Client, TestCase, override_settings
from django.urls import reverse


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class AuthFlowTests(TestCase):
    """Проверки корректности входа и выхода."""

    def setUp(self):
        self.client = Client()
        self.User = get_user_model()
        self.login_url = reverse('users:login')
        self.logout_url = reverse('users:logout')
        self.profile_url = reverse('users:profile')
        self.home_url = reverse(settings.LOGIN_REDIRECT_URL)
        self.homepage_url = reverse('homepage')

    def create_user(self, email: str, password: str, *, approved: bool = True, external: bool = False):
        user = self.User.objects.create_user(username=email, email=email, password=password)
        profile = user.profile
        profile.is_approved = approved
        profile.save()

        if external:
            group, _ = Group.objects.get_or_create(name='Внешний пользователь')
            user.groups.add(group)

        return user

    def test_login_success_sets_flags_and_redirects(self):
        """Одобренный пользователь авторизуется и получает флаг первого входа."""
        user = self.create_user('user@example.com', 'pass123', approved=True)

        response = self.client.post(self.login_url, {'username': user.username, 'password': 'pass123'})

        self.assertRedirects(response, self.home_url)
        user.refresh_from_db()
        self.assertTrue(user.profile.first_login_shown)
        self.assertTrue(self.client.session.get('show_intro_modal'))
        self.assertIn('_auth_user_id', self.client.session)

    def test_external_user_redirects_to_homepage(self):
        """Внешний пользователь уходит на homepage без показа модалки."""
        user = self.create_user('ext@example.com', 'pass123', approved=True, external=True)

        response = self.client.post(self.login_url, {'username': user.username, 'password': 'pass123'})

        self.assertRedirects(response, self.homepage_url, fetch_redirect_response=False)
        self.assertNotIn('show_intro_modal', self.client.session)
        self.assertIn('_auth_user_id', self.client.session)

    def test_unapproved_profile_cannot_login(self):
        """Неодобренный профиль получает сообщение и остаётся неавторизованным."""
        user = self.create_user('pending@example.com', 'pass123', approved=False)

        response = self.client.post(self.login_url, {'username': user.username, 'password': 'pass123'}, follow=True)

        self.assertRedirects(response, self.login_url)
        messages = [str(message) for message in get_messages(response.wsgi_request)]
        self.assertTrue(any("Ваш аккаунт ожидает подтверждения администратором." in msg for msg in messages))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_login_without_profile_shows_error_template(self):
        """Если профиль удалён, показывается страница ошибки без входа."""
        user = self.create_user('noprofile@example.com', 'pass123', approved=True)
        user.profile.delete()

        response = self.client.post(self.login_url, {'username': user.username, 'password': 'pass123'})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/profile_error.html')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_authenticated_user_gets_redirect_from_login(self):
        """Авторизованный пользователь при заходе на /login уходит в профиль."""
        user = self.create_user('already@example.com', 'pass123', approved=True)
        self.client.login(username=user.username, password='pass123')

        response = self.client.get(self.login_url)

        self.assertRedirects(response, self.profile_url)

    def test_logout_clears_session_and_redirects(self):
        """Выход завершает сессию и редиректит на страницу входа."""
        user = self.create_user('logout@example.com', 'pass123', approved=True)
        self.client.login(username=user.username, password='pass123')

        response = self.client.post(self.logout_url)

        self.assertRedirects(response, reverse(settings.LOGOUT_REDIRECT_URL), fetch_redirect_response=False)
        self.assertNotIn('_auth_user_id', self.client.session)
        # Убедимся, что защищённая страница теперь недоступна
        protected_response = self.client.get(self.profile_url)
        self.assertRedirects(protected_response, f"{self.login_url}?next={self.profile_url}")

