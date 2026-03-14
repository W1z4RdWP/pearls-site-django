from django.contrib.auth.models import Group, User
from django.test import Client, TestCase
from django.urls import reverse


class UserManagementListMentorScopeTest(TestCase):
    """
    Проверяет, что наставник видит только свою группу, staff/superuser — всех.
    """
    def setUp(self):
        self.client = Client()
        self.url = reverse('user_management:user_list')
        self.group_a = Group.objects.create(name='Group A')
        self.group_b = Group.objects.create(name='Group B')

        # Пользователи групп
        self.user_a = User.objects.create_user(
            username='user_a@example.com', email='user_a@example.com', password='pass'
        )
        self.user_a.groups.add(self.group_a)
        self.user_a.profile.is_approved = True
        self.user_a.profile.save()

        self.user_b = User.objects.create_user(
            username='user_b@example.com', email='user_b@example.com', password='pass'
        )
        self.user_b.groups.add(self.group_b)
        self.user_b.profile.is_approved = True
        self.user_b.profile.save()

        # Наставник: только группа A
        self.mentor = User.objects.create_user(
            username='mentor@example.com', email='mentor@example.com', password='pass'
        )
        self.mentor.groups.add(self.group_a)
        self.mentor.profile.is_mentor = True
        self.mentor.profile.is_approved = True
        self.mentor.profile.save()

        # Staff и superuser (superuser трактуем приоритетно)
        self.staff = User.objects.create_user(
            username='staff@example.com', email='staff@example.com', password='pass', is_staff=True
        )
        self.staff.groups.add(self.group_b)
        self.staff.profile.is_approved = True
        self.staff.profile.save()

        self.superuser = User.objects.create_superuser(
            username='admin@example.com', email='admin@example.com', password='pass'
        )
        self.superuser.groups.add(self.group_a, self.group_b)
        # Суперпользователь также наставник, но должно работать как superuser
        self.superuser.profile.is_mentor = True
        self.superuser.profile.is_approved = True
        self.superuser.profile.save()

    def test_mentor_sees_only_his_group(self):
        self.client.login(username='mentor@example.com', password='pass')
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        emails = set(resp.context['users'].values_list('email', flat=True))
        self.assertIn('user_a@example.com', emails)
        self.assertNotIn('user_b@example.com', emails)

    def test_staff_sees_all_users(self):
        self.client.login(username='staff@example.com', password='pass')
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        emails = set(resp.context['users'].values_list('email', flat=True))
        self.assertIn('user_a@example.com', emails)
        self.assertIn('user_b@example.com', emails)
        self.assertIn('mentor@example.com', emails)

    def test_superuser_sees_all_users(self):
        self.client.login(username='admin@example.com', password='pass')
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        emails = set(resp.context['users'].values_list('email', flat=True))
        self.assertIn('user_a@example.com', emails)
        self.assertIn('user_b@example.com', emails)
        self.assertIn('mentor@example.com', emails)
        self.assertIn('staff@example.com', emails)
