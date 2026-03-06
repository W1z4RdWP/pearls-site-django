from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from courses.models import Course, Lesson, Trajectory, TrajectoryCourse, UserCourseTrajectory
from courses.signals import assign_courses_from_trajectory
from myapp.models import UserCourse


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class TrajectoryCourseAssignmentTest(TestCase):
    """Проверка того, что курсы траектории назначаются только после завершения предыдущего."""

    def setUp(self) -> None:
        User = get_user_model()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass',
            email='test@example.com'
        )

        self.staff_user = User.objects.create_user(
            username='staff',
            password='testpass',
            is_staff=True
        )

        self.course1 = Course.objects.create(
            title='course 1',
            author=self.staff_user,
        )

        self.course2 = Course.objects.create(
            title='course 2',
            author=self.staff_user,
        )

        self.course3 = Course.objects.create(
            title='course 3',
            author=self.staff_user,
        )

        self.lesson = Lesson.objects.create(
            title='lesson 1',
            content='content',
            order=1
        )
        self.lesson.courses.add(self.course1, self.course2, self.course3)

        self.trajectory = Trajectory.objects.create(name='test_trajectory')
        TrajectoryCourse.objects.create(trajectory=self.trajectory, course=self.course1, order=1)
        TrajectoryCourse.objects.create(trajectory=self.trajectory, course=self.course2, order=2)
        TrajectoryCourse.objects.create(trajectory=self.trajectory, course=self.course3, order=3)

    def test_assign_trajectory_assigns_only_first_course(self):
        """При назначении траектории пользователю создаётся только первый курс траектории."""
        UserCourseTrajectory.objects.create(user=self.user, trajectory=self.trajectory)
        assign_courses_from_trajectory(self.user, self.trajectory)

        self.assertTrue(
            UserCourse.objects.filter(user=self.user, course=self.course1).exists(),
            'Первый курс траектории должен быть назначен',
        )
        self.assertFalse(
            UserCourse.objects.filter(user=self.user, course=self.course2).exists(),
            'Второй курс не должен быть назначен до завершения первого',
        )
        self.assertFalse(
            UserCourse.objects.filter(user=self.user, course=self.course3).exists(),
            'Третий курс не должен быть назначен до завершения второго',
        )

    def test_second_course_assigned_after_first_completed(self):
        """Второй курс назначается только после завершения первого."""
        UserCourseTrajectory.objects.create(user=self.user, trajectory=self.trajectory)
        assign_courses_from_trajectory(self.user, self.trajectory)

        uc1 = UserCourse.objects.get(user=self.user, course=self.course1)
        self.assertFalse(
            UserCourse.objects.filter(user=self.user, course=self.course2).exists(),
            'До завершения первого курса второго быть не должно',
        )

        uc1.status = 'completed'
        uc1.save()

        self.assertTrue(
            UserCourse.objects.filter(user=self.user, course=self.course2).exists(),
            'После завершения первого курса должен появиться второй',
        )
        self.assertFalse(
            UserCourse.objects.filter(user=self.user, course=self.course3).exists(),
            'Третий курс по-прежнему не должен быть назначен',
        )

    def test_third_course_assigned_after_second_completed(self):
        """Третий курс назначается только после завершения второго."""
        UserCourseTrajectory.objects.create(user=self.user, trajectory=self.trajectory)
        assign_courses_from_trajectory(self.user, self.trajectory)

        uc1 = UserCourse.objects.get(user=self.user, course=self.course1)
        uc1.status = 'completed'
        uc1.save()

        uc2 = UserCourse.objects.get(user=self.user, course=self.course2)
        self.assertFalse(
            UserCourse.objects.filter(user=self.user, course=self.course3).exists(),
            'До завершения второго курса третьего быть не должно',
        )

        uc2.status = 'completed'
        uc2.save()

        self.assertTrue(
            UserCourse.objects.filter(user=self.user, course=self.course3).exists(),
            'После завершения второго курса должен появиться третий',
        )

    def test_courses_not_assigned_ahead_of_order(self):
        """Курсы не назначаются вперёд: без завершения первого нет ни второго, ни третьего."""
        UserCourseTrajectory.objects.create(user=self.user, trajectory=self.trajectory)
        assign_courses_from_trajectory(self.user, self.trajectory)

        # Первый в статусе available или started — следующих быть не должно
        self.assertEqual(
            UserCourse.objects.filter(user=self.user).count(),
            1,
            'Должен быть назначен только один курс (первый)',
        )
        self.assertEqual(
            UserCourse.objects.get(user=self.user, course=self.course1).course,
            self.course1,
        )
