from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from courses.models import Trajectory, UserCourseTrajectory, TrajectoryCourse
from myapp.models import UserCourse


class Command(BaseCommand):
    help = 'Исправляет назначения траекторий пользователям на основе их групп'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Показать что будет сделано без выполнения изменений',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('Режим dry-run - изменения не будут применены'))
        
        # Получаем все траектории с группами
        trajectories = Trajectory.objects.filter(groups__isnull=False).distinct()
        
        total_assignments = 0
        total_course_assignments = 0
        
        for trajectory in trajectories:
            self.stdout.write(f'Обрабатываем траекторию: {trajectory.name}')
            
            # Получаем группы траектории
            trajectory_groups = trajectory.groups.all()
            
            # Находим пользователей в этих группах
            users = User.objects.filter(groups__in=trajectory_groups).distinct()
            
            self.stdout.write(f'  Найдено пользователей в группах: {users.count()}')
            
            for user in users:
                # Назначаем траекторию пользователю
                user_trajectory, created = UserCourseTrajectory.objects.get_or_create(
                    user=user,
                    trajectory=trajectory
                )
                
                if created:
                    total_assignments += 1
                    self.stdout.write(f'    Назначена траектория пользователю: {user.username}')
                    
                    # Назначаем курсы из траектории
                    trajectory_courses = TrajectoryCourse.objects.filter(trajectory=trajectory).order_by('order')
                    
                    for tc in trajectory_courses:
                        user_course, course_created = UserCourse.objects.get_or_create(
                            user=user,
                            course=tc.course,
                            defaults={'status': 'available'}
                        )
                        
                        if course_created:
                            total_course_assignments += 1
                            self.stdout.write(f'      Назначен курс: {tc.course.title}')
        
        self.stdout.write(self.style.SUCCESS(
            f'Завершено! Назначено траекторий: {total_assignments}, курсов: {total_course_assignments}'
        ))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('Это был dry-run. Для применения изменений запустите команду без --dry-run')) 