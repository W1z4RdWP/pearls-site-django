from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpRequest, HttpResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Count, Exists, OuterRef
from django.contrib import messages  # Добавлен импорт

from myapp.models import QuizResult, UserCourse
from courses.models import Course  # Добавлен импорт модели Course
from .models import Quiz, Question, Answer
from typing import Optional


def start_quiz_view(request) -> HttpResponse:
    topics = Quiz.objects.annotate(questions_count=Count('question'))
    return render(request, 'quizzes/start.html', {'topics': topics})

def get_questions(request, quiz_id: int = None, is_start: bool = False) -> HttpResponse:
    if request.method == 'POST' or is_start:
        # Если is_start=True, quiz_id берется из URL
        if is_start and not quiz_id:
            return redirect('quizzes')
        
        # Если не стартовая страница, получаем quiz_id из сессии
        if not is_start:
            quiz_id = request.session.get('quiz_id')
            current_question_id = request.session.get('current_question_id')
            if not quiz_id or not current_question_id:
                return redirect('quizzes')

            # Получаем следующий вопрос
            question = _get_subsequent_question(quiz_id, current_question_id)
        else:
            # Сброс сессии при старте нового теста
            request.session['quiz_id'] = quiz_id
            request.session['score'] = 0
            request.session['current_question_id'] = None
            
            # Получаем первый вопрос
            question = _get_first_question(quiz_id)

        if not question:
            return redirect('get-finish')
        
        # Обновление сессии
        request.session['current_question_id'] = question.id
        answers = Answer.objects.filter(question=question)
        is_last = not Question.objects.filter(
            quiz_id=quiz_id, 
            id__gt=question.id
        ).exists()

        # Расчет прогресса
        all_questions_ids = list(Question.objects.filter(quiz_id=quiz_id)
                               .order_by('id')
                               .values_list('id', flat=True))
        current_index = all_questions_ids.index(question.id) + 1
        total_questions = len(all_questions_ids)
        progress_percent = int((current_index / total_questions) * 100)
        
        return render(request, 'quizzes/question.html', {
            'question': question,
            'answers': answers,
            'is_last': is_last,
            'current_question_number': current_index,
            'total_questions': total_questions,
            'progress_percent': progress_percent
        })
    
    return redirect('quizzes')

def _get_first_question(quiz_id: int) -> Optional[Question]:
    return Question.objects.filter(quiz_id=quiz_id).order_by('id').first()

def _get_subsequent_question(quiz_id: int, current_id: int) -> Optional[Question]:
    return Question.objects.filter(
        quiz_id=quiz_id,
        id__gt=current_id
    ).order_by('id').first()

def get_answer(request) -> HttpResponse:
    if request.method == 'POST':
        submitted_answer_id = request.POST.get('answer_id')
        current_question_id = request.session.get('current_question_id')
        
        try:
            submitted_answer = Answer.objects.get(id=submitted_answer_id)
            correct_answer = Answer.objects.get(
                question_id=current_question_id,
                is_correct=True
            )
            
            if submitted_answer.is_correct:
                request.session['score'] = request.session.get('score', 0) + 1
                request.session.modified = True
            
             # Получаем данные для прогресса
            quiz_id = request.session.get('quiz_id')
            current_question_id = request.session.get('current_question_id')
            all_questions = Question.objects.filter(quiz_id=quiz_id).order_by('id')
            total_questions = all_questions.count()
            current_index = list(all_questions.values_list('id', flat=True)).index(current_question_id) + 1
            progress_percent = int((current_index / total_questions) * 100)

            return render(request, 'quizzes/answer.html', {
                'submitted_answer': submitted_answer,
                'correct_answer': correct_answer,
                'is_correct': submitted_answer.is_correct,
                'current_question_number': current_index,
                'total_questions': total_questions,
                'progress_percent': progress_percent
            })
        
        except (Answer.DoesNotExist, KeyError):
            return redirect('quizzes')
        except (Answer.MultipleObjectsReturned):
            return redirect('error')
    
    return redirect('quizzes')

def get_finish(request) -> HttpResponse:
    if not request.user.is_authenticated:
        return redirect('login')

    quiz_id = request.session.get('quiz_id')
    if not quiz_id:
        return redirect('quizzes')
    
    quiz = get_object_or_404(Quiz, id=quiz_id)
    questions_count = Question.objects.filter(quiz=quiz).count()
    score = request.session.get('score', 0)
    percent_score = int((score / questions_count) * 100) if questions_count > 0 else 0

    # Исправлено: убрано дублирование создания QuizResult
    passed = percent_score >= 80
    quiz_result = QuizResult.objects.create(
        user=request.user,
        quiz_title=quiz.name,
        score=score,
        total_questions=questions_count,
        percent=percent_score,
        passed=passed
    )

    # Обработка привязки к курсу
    if hasattr(quiz, 'course') and quiz.course:  # Проверяем связь с курсом
        course = quiz.course
        if passed:
            UserCourse.objects.filter(
                user=request.user, 
                course=course
            ).update(is_completed=True)
            return redirect('course_detail', slug=course.slug)
        else:
            messages.error(request, "Тест не пройден. Попробуйте снова!")
            return redirect('quiz_start', quiz_id=quiz.id)

    context = {
        'score': score,
        'questions_count': questions_count,
        'percent_score': percent_score,
        'quiz_title': quiz.name
    }
    
    _reset_quiz(request)
    return render(request, 'quizzes/finish.html', context)

def _reset_quiz(request) -> HttpRequest:
    keys = ['quiz_id', 'current_question_id', 'score']
    for key in keys:
        if key in request.session:
            del request.session[key]
    return request

def start_quiz_handler(request):
    if request.method == 'POST':
        quiz_id = request.POST.get('quiz_id')
        if not quiz_id:
            return redirect('quizzes')
        
        request.session['quiz_id'] = quiz_id
        request.session['score'] = 0
        request.session['current_question_id'] = None
        return redirect('get-questions', quiz_id=quiz_id)
    
    return redirect('quizzes')