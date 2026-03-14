from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.utils import timezone
from courses.models import Course, Lesson, Trajectory
from quizzes.models import Quiz


class StaticViewSitemap(Sitemap):
    """Статические страницы сайта"""
    priority = 0.8
    changefreq = 'weekly'
    protocol = 'https'

    def items(self):
        return ['home', 'about', 'privacy_policy', 'changelog']

    def location(self, item):
        return reverse(item)

    def lastmod(self, item):
        return timezone.now()


class CourseSitemap(Sitemap):
    """Карта курсов"""
    changefreq = 'weekly'
    priority = 0.9
    protocol = 'https'

    def items(self):
        return Course.objects.all()

    def lastmod(self, obj):
        return obj.created_at

    def location(self, obj):
        return reverse('courses:course_detail', kwargs={'slug': obj.slug})


class LessonSitemap(Sitemap):
    """Карта уроков в контексте курсов"""
    changefreq = 'monthly'
    priority = 0.7
    protocol = 'https'

    def items(self):
        # Возвращаем уроки, привязанные к курсам
        return Lesson.objects.filter(courses__isnull=False).distinct()

    def lastmod(self, obj):
        return obj.created_at

    def location(self, obj):
        # Берем первый курс, к которому привязан урок
        course = obj.courses.first()
        if course:
            return reverse('courses:lesson_detail', kwargs={
                'course_slug': course.slug,
                'lesson_id': obj.id
            })
        return None


class TrajectorySitemap(Sitemap):
    """Карта траекторий курсов"""
    changefreq = 'monthly'
    priority = 0.6
    protocol = 'https'

    def items(self):
        return Trajectory.objects.all()

    def location(self, obj):
        return reverse('courses:user_course_trajectory_detail', kwargs={'pk': obj.id})


class QuizSitemap(Sitemap):
    """Карта квизов"""
    changefreq = 'monthly'
    priority = 0.5
    protocol = 'https'

    def items(self):
        return Quiz.objects.all()

    def location(self, obj):
        return reverse('quizzes:quiz_start', kwargs={'quiz_id': obj.id})

    def lastmod(self, obj):
        return obj.created_at if hasattr(obj, 'created_at') else timezone.now()
