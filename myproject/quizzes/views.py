from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse
from django.db.models import Count, Exists, OuterRef
from .models import Quiz, Question, Answer
from typing import Optional

def start_quiz_view(request) -> HttpResponse:
    topics = Quiz.objects.annotate(questions_count=Count('question'))
    return render(request, 'quizzes/start.html', {'topics': topics})

def get_questions(request, is_start=False) -> HttpResponse:
    if request.method == 'POST':
        if is_start:
            quiz_id = request.POST.get('quiz_id')
            if not quiz_id:
                return redirect('quizzes')
            
            request.session['quiz_id'] = quiz_id
            request.session['score'] = 0
            request.session['current_question_id'] = None
            question = _get_first_question(quiz_id)
        else:
            quiz_id = request.session.get('quiz_id')
            if not quiz_id:
                return redirect('quizzes')
            
            question = _get_subsequent_question(quiz_id, request.session.get('current_question_id'))
        
        if not question:
            return redirect('get-finish')
        
        request.session['current_question_id'] = question.id
        answers = Answer.objects.filter(question=question)
        is_last = not Question.objects.filter(quiz_id=quiz_id, id__gt=question.id).exists()
        
        return render(request, 'quizzes/question.html', {
            'question': question,
            'answers': answers,
            'is_last': is_last
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
            
            return render(request, 'quizzes/answer.html', {
                'submitted_answer': submitted_answer,
                'correct_answer': correct_answer,
                'is_correct': submitted_answer.is_correct
            })
        
        except (Answer.DoesNotExist, KeyError):
            return redirect('quizzes')
    
    return redirect('quizzes')

def get_finish(request) -> HttpResponse:
    quiz_id = request.session.get('quiz_id')
    if not quiz_id:
        return redirect('quizzes')
    
    questions_count = Question.objects.filter(quiz_id=quiz_id).count()
    score = request.session.get('score', 0)
    percent_score = int((score / questions_count) * 100) if questions_count > 0 else 0
    
    context = {
        'score': score,
        'questions_count': questions_count,
        'percent_score': percent_score
    }
    
    _reset_quiz(request)
    return render(request, 'quizzes/finish.html', context)

def _reset_quiz(request) -> HttpRequest:
    keys = ['quiz_id', 'current_question_id', 'score']
    for key in keys:
        if key in request.session:
            del request.session[key]
    return request