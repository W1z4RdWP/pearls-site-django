from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client, TestCase
from django.urls import reverse


class UserEditDetailedPermissionsTest(TestCase):
    """
    Проверяет, кто может редактировать подробную карточку пользователя.
    - Наставник (mentor) имеет только readonly и не может отправлять POST.
    - Staff не может редактировать superuser.
    - Staff может редактировать обычного пользователя.
    - Superuser может редактировать любого пользователя.
    """

    def setUp(self):
        self.client = Client()
        self.User = get_user_model()

        # Группы для полноты формы
        self.group = Group.objects.create(name='Group A')

        # Целевой пользователь
        self.target_user = self.User.objects.create_user(
            username='target@example.com', email='target@example.com', password='pass'
        )
        self.target_user.groups.add(self.group)
        self.target_user.profile.is_approved = True
        self.target_user.profile.save()

        # Наставник
        self.mentor = self.User.objects.create_user(
            username='mentor@example.com', email='mentor@example.com', password='pass'
        )
        self.mentor.profile.is_mentor = True
        self.mentor.profile.is_approved = True
        self.mentor.profile.save()

        # Staff
        self.staff = self.User.objects.create_user(
            username='staff@example.com', email='staff@example.com', password='pass', is_staff=True
        )
        self.staff.profile.is_approved = True
        self.staff.profile.save()

        # Superuser
        self.superuser = self.User.objects.create_superuser(
            username='admin@example.com', email='admin@example.com', password='pass'
        )
        self.superuser.profile.is_approved = True
        self.superuser.profile.save()

        self.url_target = reverse('user_management:user_edit_detailed', args=[self.target_user.pk])
        self.url_super = reverse('user_management:user_edit_detailed', args=[self.superuser.pk])

    def _payload(self, email, first_name, last_name, phone='+70000000000'):
        return {
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
            'groups': [str(self.group.pk)],
            'is_active': 'on',
            'middle_name': '',
            'role': '',
            'date_of_birth': '',
            'phone_number': phone,
            'phone_arbitrary_format': '',
            'bio': '',
            'is_approved': 'on',
            'is_mentor': '',
        }

    def test_mentor_cannot_edit(self):
        """Наставник получает 403 при попытке POST на detailed форму."""
        self.client.login(username='mentor@example.com', password='pass')
        resp = self.client.post(self.url_target, data=self._payload('new@example.com', 'New', 'Name'))
        self.assertEqual(resp.status_code, 403)

    def test_staff_cannot_edit_superuser(self):
        """Staff не может изменить superuser: POST -> 403, данные не меняются."""
        self.client.login(username='staff@example.com', password='pass')
        resp = self.client.post(self.url_super, data=self._payload('hacked@example.com', 'Hack', 'Me'))
        self.assertEqual(resp.status_code, 403)
        self.superuser.refresh_from_db()
        self.assertNotEqual(self.superuser.email, 'hacked@example.com')

    def test_staff_can_edit_regular_user(self):
        """Staff успешно сохраняет изменения обычного пользователя."""
        self.client.login(username='staff@example.com', password='pass')
        resp = self.client.post(self.url_target, data=self._payload('updated@example.com', 'Staff', 'Edited'), follow=True)
        self.assertIn(resp.status_code, (200, 302))
        self.target_user.refresh_from_db()
        self.assertEqual(self.target_user.email, 'updated@example.com')
        self.assertEqual(self.target_user.first_name, 'Staff')
        self.assertEqual(self.target_user.last_name, 'Edited')

    def test_superuser_can_edit_any_user(self):
        """Superuser может редактировать staff/обычного пользователя."""
        self.client.login(username='admin@example.com', password='pass')
        resp = self.client.post(self.url_target, data=self._payload('rootedit@example.com', 'Root', 'Edit'), follow=True)
        self.assertIn(resp.status_code, (200, 302))
        self.target_user.refresh_from_db()
        self.assertEqual(self.target_user.email, 'rootedit@example.com')
        self.assertEqual(self.target_user.first_name, 'Root')
        self.assertEqual(self.target_user.last_name, 'Edit')
