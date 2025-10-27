from django.urls import path
from . import views

app_name = 'quizzes'

urlpatterns = [
    path('', views.StartQuizView.as_view(), name='quizzes'),
    path('start-quiz/', views.start_quiz_handler, name='quiz_start_handler'),
    path('start/<int:quiz_id>/', views.get_questions, {'is_start': True}, name='quiz_start'),
    path('get-questions/start', views.get_questions, {'is_start': True}, name='get-questions'),
    path('get-questions', views.get_questions, {'is_start': False}, name='get-questions'),
    path('get-answer', views.get_answer, name='get-answer'),
    path('get-finish', views.get_finish, name='get-finish'),
    path('best-result/<int:quiz_id>/', views.quiz_best_result, name='quiz_best_result'),
    path('search/', views.search_quizzes_ajax, name='quiz_search_ajax'),
    path('create/', views.QuizCreateView.as_view(), name='quiz_create'),
    path('edit/<int:quiz_id>/', views.QuizEditView.as_view(), name='quiz_edit'),
    path('delete/<int:quiz_id>/', views.QuizDeleteView.as_view(), name='quiz_delete'),
    path('limit-exceeded/<int:quiz_id>/', views.AttemptLimitExceededView.as_view(), name='attempt_limit_exceeded'),
]