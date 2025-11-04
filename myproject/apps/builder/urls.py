from django.urls import path
from django.http import HttpResponseRedirect
from django.urls import reverse

from . import views
from .views import DashboardView

app_name = 'builder'

# URL конфигурация для приложения `builder`.
urlpatterns = [
    # Дашборд (редирект неавторизованных/не-стафф/не-наставников в мастер уроков)
    path('', lambda request: HttpResponseRedirect(reverse('builder:lesson_master')) if not (request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.is_mentor_user))) else DashboardView.as_view()(request), name='dashboard'),

    # Контент и уроки
    path('content/', views.LessonMasterDetailView.as_view(), name='lesson_master'),
    path('lesson/<int:pk>/', views.LessonMasterDetailView.as_view(), name='lesson_detail'),
    path('lesson/<int:pk>/delete/', views.LessonDeleteView.as_view(), name='lesson_delete'),
    path('lesson/<int:pk>/edit/', views.LessonUpdateView.as_view(), name='lesson_edit'),
    path('add/', views.LessonCreateView.as_view(), name='lesson_add'),
    path('add/<int:category_id>/', views.LessonCreateView.as_view(), name='lesson_add_with_category'),
    path('update_control/', views.UpdateControlStandaloneView.as_view(), name='update_control_standalone'),

    # Категории
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/add/', views.CategoryCreateView.as_view(), name='category_add'),
    path('categories/<int:pk>/edit/', views.CategoryUpdateView.as_view(), name='category_edit'),
    path('categories/<int:pk>/delete/', views.CategoryDeleteView.as_view(), name='category_delete'),
    path('categories/ajax_add_root/', views.ajax_add_root_category, name='category_ajax_add_root'),
    path('categories/ajax_add_sub/', views.ajax_add_subcategory, name='category_ajax_add_sub'),
    path('categories/ajax_rename/', views.ajax_rename_category, name='category_ajax_rename'),
    path('categories/reorder/', views.reorder_categories, name='reorder_categories'),

    # Документы и инциденты
    path('documents/', views.DocumentListView.as_view(), name='documents'),
    path('incidents/', views.IncidentListView.as_view(), name='incidents'),
    path('incidents/add/', views.IncidentCreateView.as_view(), name='incident_add'),
    path('incidents/<int:pk>/edit/', views.IncidentUpdateView.as_view(), name='incident_edit'),

    # Поиск/реордеры/клипборд
    path('search/', views.ajax_search_tree, name='search_tree'),
    path('reorder/', views.ajax_reorder, name='reorder'),
    path('lessons/reorder_uncat/', views.reorder_uncat_lessons, name='reorder_uncat_lessons'),
    path('lessons/reorder_in_category/', views.reorder_lessons_in_category, name='reorder_lessons_in_category'),

    path('copy/', views.ajax_copy, name='copy'),
    path('cut/', views.ajax_cut, name='cut'),
    path('paste/', views.ajax_paste, name='paste'),
    path('clipboard/', views.ajax_get_clipboard, name='get_clipboard'),
    path('mirror/', views.ajax_mirror, name='mirror'),
    path('category_tree_json/', views.ajax_category_tree_json, name='category_tree_json'),
    path('ajax_delete_lesson_instance/', views.ajax_delete_lesson_instance, name='ajax_delete_lesson_instance'),

    # Словарь и траектории
    # path('dictionary/', views.DictionaryListView.as_view(), name='dictionary_list'),
    path('dictionary/<int:pk>/', views.DictionarySectionDetailView.as_view(), name='dictionary_detail'),
    path('dictionary/reorder/', views.dictionary_reorder, name='dictionary_reorder'),
    path('actualize_version/', views.actualize_version, name='actualize_version'),
    path('dictionary/save_terms/', views.save_terms, name='save_terms'),

    path('trajectory-management/', views.TrajectoryManagementView.as_view(), name='trajectory_management'),
    path('trajectories/', views.TrajectoryListView.as_view(), name='trajectory_list'),
    path('trajectories/<int:trajectory_id>/detail/', views.trajectory_detail_ajax, name='trajectory_detail_ajax'),
    path('trajectories/<int:pk>/edit/', views.TrajectoryEditView.as_view(), name='trajectory_edit'),
    path('trajectories/<int:trajectory_id>/courses/', views.TrajectoryCoursesView.as_view(), name='trajectory_courses'),
    path('trajectories/<int:trajectory_id>/courses/reorder/', views.trajectory_course_reorder, name='trajectory_course_reorder'),
    path('trajectories/<int:trajectory_id>/courses/add/', views.trajectory_course_add, name='trajectory_course_add'),
    path('trajectories/<int:trajectory_id>/courses/add-multiple/', views.trajectory_course_add_multiple, name='trajectory_course_add_multiple'),
    path('trajectories/<int:trajectory_id>/courses/remove/', views.trajectory_course_remove, name='trajectory_course_remove'),
    path('trajectories/<int:trajectory_id>/delete/', views.trajectory_delete, name='trajectory_delete'),

    # Курсы и документы
    path('courses/', views.CourseListView.as_view(), name='course_list'),
    path('incident-courses/', views.IncidentCourseListView.as_view(), name='incident_course_list'),
    path('documents/<int:pk>/delete/', views.DocumentDeleteView.as_view(), name='document_delete'),

    # Audit API endpoints
    path('api/audit/history/', views.audit_history_api, name='audit_history_api'),
    path('api/audit/search/', views.audit_search_api, name='audit_search_api'),
    
    # User search API
    path('api/users/search/', views.api_search_users, name='api_search_users'),
]
