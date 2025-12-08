from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model

import json

from courses.models import Trajectory, Course, TrajectoryCourse
from users.models import Profile


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class TrajectoryAccessTest(TestCase):
    """
    Проверяет, что траектории могут создавать/редактировать/удалять только staff/superuser.
    """

    def setUp(self):
        self.client = Client()
        User = get_user_model()
        self.staff = User.objects.create_user(username='staff', password='pass', is_staff=True)
        self.superuser = User.objects.create_superuser(username='admin', password='pass')
        self.mentor = User.objects.create_user(username='mentor', password='pass')
        Profile.objects.get_or_create(user=self.mentor, defaults={'is_mentor': True})
        self.create_url = reverse('courses:trajectory_create')

    def _payload(self, name='Traj', desc='desc'):
        return {
            'name': name,
            'description': desc,
            'certificate': False,
        }

    def test_staff_can_create_trajectory(self):
        self.client.login(username='staff', password='pass')
        resp = self.client.post(self.create_url, self._payload('Staff traj', 'd'))
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Trajectory.objects.filter(name='Staff traj').exists())

    def test_superuser_can_create_trajectory(self):
        self.client.login(username='admin', password='pass')
        resp = self.client.post(self.create_url, self._payload('Super traj', 'd2'))
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Trajectory.objects.filter(name='Super traj').exists())

    def test_mentor_cannot_create_trajectory(self):
        self.client.login(username='mentor', password='pass')
        resp = self.client.post(self.create_url, self._payload('Mentor traj', 'd3'))
        self.assertEqual(resp.status_code, 403)
        self.assertFalse(Trajectory.objects.filter(name='Mentor traj').exists())

    # --- Редактирование ---
    def test_staff_can_edit_trajectory(self):
        traj = Trajectory.objects.create(name='Edit staff', description='d')
        self.client.login(username='staff', password='pass')
        url = reverse('builder:trajectory_edit', args=[traj.pk])
        resp = self.client.post(url, self._payload('Edit staff v2', 'd2'))
        self.assertEqual(resp.status_code, 302)
        traj.refresh_from_db()
        self.assertEqual(traj.name, 'Edit staff v2')

    def test_superuser_can_edit_trajectory(self):
        traj = Trajectory.objects.create(name='Edit super', description='d')
        self.client.login(username='admin', password='pass')
        url = reverse('builder:trajectory_edit', args=[traj.pk])
        resp = self.client.post(url, self._payload('Edit super v2', 'd2'))
        self.assertEqual(resp.status_code, 302)
        traj.refresh_from_db()
        self.assertEqual(traj.name, 'Edit super v2')

    def test_mentor_cannot_edit_trajectory(self):
        traj = Trajectory.objects.create(name='Edit mentor', description='d')
        self.client.login(username='mentor', password='pass')
        url = reverse('builder:trajectory_edit', args=[traj.pk])
        resp_get = self.client.get(url)
        self.assertEqual(resp_get.status_code, 403)
        resp_post = self.client.post(url, self._payload('changed', 'd2'))
        self.assertEqual(resp_post.status_code, 403)
        traj.refresh_from_db()
        self.assertEqual(traj.name, 'Edit mentor')

    # --- Удаление ---
    def test_staff_can_delete_trajectory(self):
        traj = Trajectory.objects.create(name='Delete staff', description='d')
        self.client.login(username='staff', password='pass')
        url = reverse('builder:trajectory_delete', args=[traj.pk])
        resp = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Trajectory.objects.filter(pk=traj.pk).exists())

    def test_superuser_can_delete_trajectory(self):
        traj = Trajectory.objects.create(name='Delete super', description='d')
        self.client.login(username='admin', password='pass')
        url = reverse('builder:trajectory_delete', args=[traj.pk])
        resp = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Trajectory.objects.filter(pk=traj.pk).exists())

    def test_mentor_cannot_delete_trajectory(self):
        traj = Trajectory.objects.create(name='Delete mentor', description='d')
        self.client.login(username='mentor', password='pass')
        url = reverse('builder:trajectory_delete', args=[traj.pk])
        resp = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code, 403)
        self.assertTrue(Trajectory.objects.filter(pk=traj.pk).exists())

    # --- Курсы в траектории ---
    def _make_course(self, title, author):
        return Course.objects.create(
            title=title,
            description='d',
            author=author,
            slug=f"{title.lower().replace(' ', '-')}",
            mentors_time_to_check=2,
            certificate=False,
            is_incident=False,
        )

    def test_staff_add_reorder_remove_courses(self):
        traj = Trajectory.objects.create(name='Traj courses staff', description='d')
        self.client.login(username='staff', password='pass')
        c1 = self._make_course('Course 1', self.staff)
        c2 = self._make_course('Course 2', self.staff)

        add_url = reverse('builder:trajectory_course_add', args=[traj.pk])
        reorder_url = reverse('builder:trajectory_course_reorder', args=[traj.pk])
        remove_url = reverse('builder:trajectory_course_remove', args=[traj.pk])

        # add two courses
        self.client.post(add_url, data=json.dumps({'course_id': c1.id}), content_type='application/json')
        self.client.post(add_url, data=json.dumps({'course_id': c2.id}), content_type='application/json')
        orders = list(TrajectoryCourse.objects.filter(trajectory=traj).order_by('order').values_list('course_id', 'order'))
        self.assertEqual(orders, [(c1.id, 1), (c2.id, 2)])

        # reorder: swap
        self.client.post(reorder_url, data=json.dumps({'course_orders': [
            {'course_id': c1.id, 'order': 2},
            {'course_id': c2.id, 'order': 1},
        ]}), content_type='application/json')
        orders_reordered = list(TrajectoryCourse.objects.filter(trajectory=traj).order_by('order').values_list('course_id', 'order'))
        self.assertEqual(orders_reordered, [(c2.id, 1), (c1.id, 2)])

        # remove one course and ensure order compacted
        self.client.post(remove_url, data=json.dumps({'course_id': c2.id}), content_type='application/json')
        remaining = list(TrajectoryCourse.objects.filter(trajectory=traj).order_by('order').values_list('course_id', 'order'))
        self.assertEqual(remaining, [(c1.id, 1)])

    def test_superuser_add_remove_courses(self):
        traj = Trajectory.objects.create(name='Traj courses super', description='d')
        self.client.login(username='admin', password='pass')
        c1 = self._make_course('Course X', self.superuser)

        add_url = reverse('builder:trajectory_course_add', args=[traj.pk])
        remove_url = reverse('builder:trajectory_course_remove', args=[traj.pk])

        self.client.post(add_url, data=json.dumps({'course_id': c1.id}), content_type='application/json')
        self.assertTrue(TrajectoryCourse.objects.filter(trajectory=traj, course=c1).exists())

        self.client.post(remove_url, data=json.dumps({'course_id': c1.id}), content_type='application/json')
        self.assertFalse(TrajectoryCourse.objects.filter(trajectory=traj, course=c1).exists())

