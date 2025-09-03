from django.urls import path
from . import views as course_views
from .views import UserCourseTrajectoryDetailView, UserCourseTrajectoryListView

app_name = 'courses'

urlpatterns = [
    path('', course_views.CourseDetailView.as_view(), name='course-detail'),
    path('create-course/', course_views.create_course, name='create-course'),
    path('course/<slug:slug>/', course_views.CourseDetailView.as_view(), name='course_detail'),
    path('courses_list/', course_views.CourseListView.as_view(), name='course_detail_all'),
    path('course/<slug:course_slug>/lesson/<int:lesson_id>/', course_views.lesson_detail, name='lesson_detail'),
    path('course/<slug:course_slug>/create-lesson/', course_views.create_lesson, name='create_lesson'),
    path('course/<slug:course_slug>/add-lesson/', course_views.add_lesson, name='add_lesson'),
    path('course/<slug:course_slug>/reorder-materials/', course_views.reorder_materials, name='reorder_materials'),
    path('course/<slug:slug>/delete/', course_views.delete_course, name='delete_course'),
    path('lesson/<int:lesson_id>/delete/', course_views.delete_lesson, name='delete_lesson'),
    path('course/<slug:course_slug>/lesson/<int:lesson_id>/complete/', course_views.complete_lesson, name='complete_lesson'),
    path('course/<slug:slug>/edit/', course_views.edit_course, name='edit_course'),
    path('lesson/<int:lesson_id>/edit/', course_views.edit_lesson, name='edit_lesson'),
    path('course/<slug:course_slug>/redir_to_quiz/', course_views.redir_to_quiz, name='redir_to_quiz'),
    path('trajectory/<int:pk>/', UserCourseTrajectoryDetailView.as_view(), name='user_course_trajectory_detail'),
    path('trajectories/', UserCourseTrajectoryListView.as_view(), name='user_course_trajectory_list'),
    path('trajectory-create/', course_views.TrajectoryCreateView.as_view(), name='trajectory_create'),
    path('user-certificates/', course_views.CertificateListView.as_view(), name='user_certificates'),
    path('certificate/<str:certificate_id>/download/', course_views.download_certificate_pdf, name='download_certificate_pdf'),
    path('certificate/<str:certificate_id>/view/', course_views.view_certificate_pdf, name='view_certificate_pdf'),
]
