from django.urls import path
from django.http import HttpResponseRedirect
from django.urls import reverse

from . import views
from .views import DashboardView

app_name = 'builder'

urlpatterns = [
    path('', lambda request: HttpResponseRedirect(reverse('builder:lesson_master')) if not (request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser)) else DashboardView.as_view()(request), name='dashboard'),
    path('content/', views.LessonMasterDetailView.as_view(), name='lesson_master'),
    path('lesson/<int:pk>/', views.LessonMasterDetailView.as_view(), name='lesson_detail'),
    path('lesson/<int:pk>/delete/', views.LessonDeleteView.as_view(), name='lesson_delete'),
    path('lesson/<int:pk>/edit/', views.LessonUpdateView.as_view(), name='lesson_edit'),
    path('add/', views.LessonCreateView.as_view(), name='lesson_add'),
    path('add/<int:category_id>/', views.LessonCreateView.as_view(), name='lesson_add_with_category'),
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/add/', views.CategoryCreateView.as_view(), name='category_add'),
    path('categories/<int:pk>/edit/', views.CategoryUpdateView.as_view(), name='category_edit'),
    path('categories/<int:pk>/delete/', views.CategoryDeleteView.as_view(), name='category_delete'),
    path('categories/ajax_add_root/', views.ajax_add_root_category, name='category_ajax_add_root'),
    path('categories/ajax_add_sub/', views.ajax_add_subcategory, name='category_ajax_add_sub'),
    path('categories/ajax_rename/', views.ajax_rename_category, name='category_ajax_rename'),
    path('categories/reorder/', views.reorder_categories, name='reorder_categories'),
    path('documents/', views.DocumentListView.as_view(), name='documents'),
    path('incidents/', views.IncidentListView.as_view(), name='incidents'),
    path('incidents/add/', views.IncidentCreateView.as_view(), name='incident_add'),
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
    # path('dictionary/', views.DictionaryListView.as_view(), name='dictionary_list'),
    path('dictionary/<int:pk>/', views.DictionaryDetailView.as_view(), name='dictionary_detail'),
    path('dictionary/reorder/', views.dictionary_reorder, name='dictionary_reorder'),
]
