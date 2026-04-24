from django.urls import path
from django.http import HttpResponseRedirect
from django.urls import reverse


from builder.views.ajax_lessons_cats import (
                    ajax_category_tree_json, ajax_copy, ajax_cut, ajax_delete_lesson_instance, 
                    ajax_get_clipboard, ajax_mirror, ajax_paste, ajax_reorder, ajax_search_tree, 
                    reorder_lessons_in_category, reorder_uncat_lessons
)
from builder.views.api_views import api_get_category_lessons, api_get_group_users, api_get_groups, api_get_users_by_ids, api_search_users
from builder.views.audit import audit_history_api, audit_search_api
from builder.views.lessons_views import (
                    LessonCreateView, LessonDeleteView, LessonMasterDetailView, 
                    LessonUpdateView, UpdateControlStandaloneView, actualize_version,
                    create_lesson_draft, LessonDraftUpdateView, LessonDraftReviewView,
                    LessonDraftHistoryListView, LessonDraftHistoryDetailView
)
from builder.views.categories_views import (
                    CategoryDeleteView, CategoryListView, 
                    ajax_add_root_category, ajax_add_subcategory, 
                    ajax_rename_category, reorder_categories
)
from builder.views.incidents_views import (
                    BulkUnassignIncidentUsersView, CreateCourseFromIncidentView, IncidentDeclineView, IncidentDeleteView, IncidentDetailListView, IncidentDetailLoadMoreView,
                    IncidentListView, IncidentCreateView, IncidentStatusesReportView, IncidentUpdateView, UnassignIncidentUserView, 
                    incidents_export_excel_report
                )
from builder.views.ipr_views import (
                    IPRCreateView, IPRListView, IPRModuleCompleteView, IPRModuleCreateView, IPRModuleDetailView, 
                    IPRModuleListView, IPRModulePauseView, IPRModuleResumeView, IPRModuleStartView, 
                    IPRModuleUpdateView, IPRUpdateView
)
from builder.views.dictionary_views import DictionarySectionDetailView, dictionary_reorder, save_terms
from builder.views.courses_trajectories_views import (
                    CourseListView, IncidentCourseListView, TrajectoryCoursesView, TrajectoryEditView, 
                    TrajectoryListView, TrajectoryManagementView, trajectory_course_add, trajectory_course_add_multiple, 
                    trajectory_course_remove, trajectory_course_reorder, trajectory_delete, trajectory_detail_ajax
)
from builder.views.dashboard_views import DashboardView


app_name = 'builder'

# URL конфигурация для приложения `builder`.
urlpatterns = [
    # Дашборд (редирект неавторизованных/не-стафф/не-наставников в мастер уроков)
    path('', lambda request: HttpResponseRedirect(reverse('builder:lesson_master')) if not (request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.is_mentor_user))) else DashboardView.as_view()(request), name='dashboard'),

    # Контент и уроки
    path('content/', LessonMasterDetailView.as_view(), name='lesson_master'),
    path('lesson/<int:pk>/', LessonMasterDetailView.as_view(), name='lesson_detail'),
    path('lesson/<int:pk>/delete/', LessonDeleteView.as_view(), name='lesson_delete'),
    path('lesson/<int:pk>/edit/', LessonUpdateView.as_view(), name='lesson_edit'),
    path('add/', LessonCreateView.as_view(), name='lesson_add'),
    path('add/<int:category_id>/', LessonCreateView.as_view(), name='lesson_add_with_category'),
    path('update_control/', UpdateControlStandaloneView.as_view(), name='update_control_standalone'),
    
    # Черновики уроков
    path('lesson/<int:lesson_id>/draft/create/', create_lesson_draft, name='lesson_draft_create'),
    path('lesson/draft/<int:pk>/edit/', LessonDraftUpdateView.as_view(), name='lesson_draft_edit'),
    path('lesson/draft/<int:pk>/review/', LessonDraftReviewView.as_view(), name='lesson_draft_review'),
    path('lesson/draft/history/', LessonDraftHistoryListView.as_view(), name='lesson_draft_history'),
    path('lesson/draft/<int:pk>/history/', LessonDraftHistoryDetailView.as_view(), name='lesson_draft_history_detail'),

    # Категории
    path('categories/', CategoryListView.as_view(), name='category_list'),
    path('categories/<int:pk>/delete/', CategoryDeleteView.as_view(), name='category_delete'),
    path('categories/ajax_add_root/', ajax_add_root_category, name='category_ajax_add_root'),
    path('categories/ajax_add_sub/', ajax_add_subcategory, name='category_ajax_add_sub'),
    path('categories/ajax_rename/', ajax_rename_category, name='category_ajax_rename'),
    path('categories/reorder/', reorder_categories, name='reorder_categories'),

    # Документы и инциденты
    path('incidents/', IncidentListView.as_view(), name='incidents'),
    path('incidents/add/', IncidentCreateView.as_view(), name='incident_add'),
    path('incidents/<int:pk>/edit/', IncidentUpdateView.as_view(), name='incident_edit'),
    path('incidents/<int:pk>/decline/', IncidentDeclineView.as_view(), name='incident_decline'),
    path('incidents/<int:pk>/delete/', IncidentDeleteView.as_view(), name='incident_delete'),
    path('incidents/<int:pk>/create-course/', CreateCourseFromIncidentView.as_view(), name='incident_create_course'),
    path('incidents/detail/', IncidentDetailListView.as_view(), name='incident_detail'),
    path('incidents/detail/bulk-unassign/', BulkUnassignIncidentUsersView.as_view(), name='incident_bulk_unassign'),
    path('incidents/detail/load-more/', IncidentDetailLoadMoreView.as_view(), name='incident_detail_load_more'),
    path('incidents/statuses-report/', IncidentStatusesReportView.as_view(), name='incident_statuses_report'),
    path('incidents/<int:incident_id>/unassign-user/<int:user_id>/', UnassignIncidentUserView.as_view(), name='incident_unassign_user'),
    path('incident/export_excel_report/', incidents_export_excel_report, name='incidents_export_excel_report'),

    # Поиск/реордеры/клипборд
    path('search/', ajax_search_tree, name='search_tree'),
    path('reorder/', ajax_reorder, name='reorder'),
    path('lessons/reorder_uncat/', reorder_uncat_lessons, name='reorder_uncat_lessons'),
    path('lessons/reorder_in_category/', reorder_lessons_in_category, name='reorder_lessons_in_category'),

    path('copy/', ajax_copy, name='copy'),
    path('cut/', ajax_cut, name='cut'),
    path('paste/', ajax_paste, name='paste'),
    path('clipboard/', ajax_get_clipboard, name='get_clipboard'),
    path('mirror/', ajax_mirror, name='mirror'),
    path('category_tree_json/', ajax_category_tree_json, name='category_tree_json'),
    path('ajax_delete_lesson_instance/', ajax_delete_lesson_instance, name='ajax_delete_lesson_instance'),

    # Словарь и траектории
    # path('dictionary/', views.DictionaryListView.as_view(), name='dictionary_list'),
    path('dictionary/<int:pk>/', DictionarySectionDetailView.as_view(), name='dictionary_detail'),
    path('dictionary/reorder/', dictionary_reorder, name='dictionary_reorder'),
    path('actualize_version/', actualize_version, name='actualize_version'),
    path('dictionary/save_terms/', save_terms, name='save_terms'),

    path('trajectory-management/', TrajectoryManagementView.as_view(), name='trajectory_management'),
    path('trajectories/', TrajectoryListView.as_view(), name='trajectory_list'),
    path('trajectories/<int:trajectory_id>/detail/', trajectory_detail_ajax, name='trajectory_detail_ajax'),
    path('trajectories/<int:pk>/edit/', TrajectoryEditView.as_view(), name='trajectory_edit'),
    path('trajectories/<int:trajectory_id>/courses/', TrajectoryCoursesView.as_view(), name='trajectory_courses'),
    path('trajectories/<int:trajectory_id>/courses/reorder/', trajectory_course_reorder, name='trajectory_course_reorder'),
    path('trajectories/<int:trajectory_id>/courses/add/', trajectory_course_add, name='trajectory_course_add'),
    path('trajectories/<int:trajectory_id>/courses/add-multiple/', trajectory_course_add_multiple, name='trajectory_course_add_multiple'),
    path('trajectories/<int:trajectory_id>/courses/remove/', trajectory_course_remove, name='trajectory_course_remove'),
    path('trajectories/<int:trajectory_id>/delete/', trajectory_delete, name='trajectory_delete'),

    # Курсы и документы
    path('courses/', CourseListView.as_view(), name='course_list'),
    path('incident-courses/', IncidentCourseListView.as_view(), name='incident_course_list'),
    # path('documents/<int:pk>/delete/', DocumentDeleteView.as_view(), name='document_delete'),

    # Audit API endpoints
    path('api/audit/history/', audit_history_api, name='audit_history_api'),
    path('api/audit/search/', audit_search_api, name='audit_search_api'),
    
    # User search API
    path('api/users/search/', api_search_users, name='api_search_users'),
    path('api/users/by-ids/', api_get_users_by_ids, name='api_get_users_by_ids'),
    
    # Groups API
    path('api/groups/', api_get_groups, name='api_get_groups'),
    path('api/groups/<int:group_id>/users/', api_get_group_users, name='api_get_group_users'),
    
    # Category lessons API
    path('api/categories/<int:category_id>/lessons/', api_get_category_lessons, name='api_get_category_lessons'),
    
    # ИПР
    path('ipr/', IPRListView.as_view(), name='ipr_list'),
    path('ipr/add/', IPRCreateView.as_view(), name='ipr_add'),
    path('ipr/<int:pk>/edit/', IPRUpdateView.as_view(), name='ipr_edit'),
    
    # Модули ИПР
    path('ipr/modules/<int:user_id>/', IPRModuleListView.as_view(), name='ipr_module_list'),
    path('ipr/modules/<int:user_id>/add/', IPRModuleCreateView.as_view(), name='ipr_module_add'),
    path('ipr/modules/<int:pk>/edit/', IPRModuleUpdateView.as_view(), name='ipr_module_edit'),
    path('ipr/modules/<int:pk>/info/', IPRModuleDetailView.as_view(), name='ipr_module_info'),
    path('ipr/modules/<int:pk>/start/', IPRModuleStartView.as_view(), name='ipr_module_start'),
    path('ipr/modules/<int:pk>/complete/', IPRModuleCompleteView.as_view(), name='ipr_module_complete'),
    path('ipr/modules/<int:pk>/pause/', IPRModulePauseView.as_view(), name='ipr_module_pause'),
    path('ipr/modules/<int:pk>/resume/', IPRModuleResumeView.as_view(), name='ipr_module_resume'),
]
