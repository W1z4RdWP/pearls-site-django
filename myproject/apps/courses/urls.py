from django.urls import path
from . import views as course_views
from .views import UserCourseTrajectoryDetailView, UserCourseTrajectoryListView

app_name = 'courses'

# URL конфигурация для приложения `courses`.

urlpatterns = [
    # Курсы
    path('', course_views.CourseDetailView.as_view(), name='course-detail'),
    path('create-course/', course_views.CreateCourseView.as_view(), name='create-course'),
    path('course/<slug:slug>/', course_views.CourseDetailView.as_view(), name='course_detail'),
    path('courses_list/', course_views.CourseListView.as_view(), name='course_detail_all'),

    # Уроки
    path('course/<slug:course_slug>/lesson/<int:lesson_id>/', course_views.LessonDetailView.as_view(), name='lesson_detail'),
    path('course/<slug:course_slug>/create-lesson/', course_views.CreateLessonView.as_view(), name='create_lesson'),
    path('course/<slug:course_slug>/add-lesson/', course_views.AddLessonView.as_view(), name='add_lesson'),
    path('course/<slug:course_slug>/reorder-materials/', course_views.reorder_materials, name='reorder_materials'),
    path('course/<slug:slug>/delete/', course_views.DeleteCourseView.as_view(), name='delete_course'),
    path('lesson/<int:lesson_id>/delete/', course_views.DeleteLessonView.as_view(), name='delete_lesson'),
    path('course/<slug:course_slug>/lesson/<int:lesson_id>/complete/', course_views.complete_lesson, name='complete_lesson'),
    path('course/<slug:slug>/edit/', course_views.edit_course, name='edit_course'),
    path('lesson/<int:lesson_id>/edit/', course_views.edit_lesson, name='edit_lesson'),

    # Тесты
    path('course/<slug:course_slug>/redir_to_quiz/', course_views.redir_to_quiz, name='redir_to_quiz'),
    path('course/<slug:course_slug>/quiz/<int:quiz_id>/remove/', course_views.remove_quiz_from_course, name='remove_quiz_from_course'),

    # Траектории
    path('trajectory/<int:pk>/', UserCourseTrajectoryDetailView.as_view(), name='user_course_trajectory_detail'),
    path('trajectories/', UserCourseTrajectoryListView.as_view(), name='user_course_trajectory_list'),
    path('trajectory-create/', course_views.TrajectoryCreateView.as_view(), name='trajectory_create'),

    # Сертификаты
    path('user-certificates/', course_views.CertificateListView.as_view(), name='user_certificates'),
    path('certificate/<str:certificate_id>/download/', course_views.download_certificate_pdf, name='download_certificate_pdf'),
    path('certificate/<str:certificate_id>/view/', course_views.ViewCertificatePdfView.as_view(), name='view_certificate_pdf'),

    # Метрики
    path('metrics/', course_views.MetricsFormView.as_view(), name='metrics_form'),
    path('metrics/success/', course_views.MetricsSuccessView.as_view(), name='metrics_success'),
    path('metrics/admin/', course_views.MetricsAdminListView.as_view(), name='metrics_admin_list'),
    path('metrics/admin/<int:submission_id>/', course_views.MetricsAdminDetailView.as_view(), name='metrics_admin_detail'),
    path('metrics/admin/<int:submission_id>/export/', course_views.export_metrics_to_excel, name='metrics_export_excel'),
]
