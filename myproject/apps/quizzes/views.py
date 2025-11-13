from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Count, Exists, OuterRef, Max, Q
from datetime import timedelta
from django.contrib import messages
from django.views.generic import DetailView, TemplateView
from django.core.paginator import Paginator
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User

from myapp.models import QuizResult, UserCourse, UserAnswer, UserProgress
from courses.models import Course
from .models import Quiz, Question, Answer, QuizAttempt
from .utils import DataMixin
from gamification.utils import award_dascoin_points, award_achievement, award_course_badge
from courses.utils import issue_certificate
from typing import Optional
import logging
from django.utils import timezone


audit_logger = logging.getLogger('audit')

class StartQuizView(LoginRequiredMixin, UserPassesTestMixin, DataMixin, TemplateView):
    """
    Класс представление для рендера стартовой страницы тестов.
    Доступ разрешен только авторизованным пользователям с административными правами.

    Атрибуты:
     - template_name - путь к шаблону;
     - get_context_data() - в шаблон передается переменная topics, которая возвращает количество вопросов в каждом тесте
    """
    template_name = 'quizzes/quiz_control_panel.html'
    login_url = 'users:login'  # URL для перенаправления неавторизованных пользователей
    permission_denied_message = "Доступ разрешен только администраторам сайта"

    def test_func(self):
        """Проверка административных привилегий"""
        return self.request.user.is_authenticated and self.request.user.is_staff


    def get_context_data(self, **kwargs):        
        context = super().get_context_data(**kwargs)
        quizzes = Quiz.objects.annotate(questions_count=Count('question')).order_by('-id')
        paginator = Paginator(quizzes, 5)  # Показывать 10 тестов на странице
        page_number = self.request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        context = self.get_mixin_context(context, topics=page_obj)
        context['page_obj'] = page_obj  # Для управления пагинацией в шаблоне
        context = self.get_mixin_context(context)
        return context



@require_http_methods(["GET"])
def search_quizzes_ajax(request):
    """
    AJAX endpoint для поиска тестов по названию
    Возвращает JSON с результатами поиска без пагинации
    При пустом запросе возвращает все тесты (с ограничением в 100)
    """
    search_term = request.GET.get('q', '').strip()

    # Поиск по названию (case-insensitive) или все тесты при пустом запросе
    if search_term:
        quizzes = Quiz.objects.filter(
            name__icontains=search_term
        ).annotate(
            questions_count=Count('question')
        ).order_by('-id').values(
            'id', 'name', 'questions_count', 'attempt_limit', 'pass_threshold'
        )
    else:
        # При пустом запросе возвращаем все тесты с ограничением
        quizzes = Quiz.objects.all().annotate(
            questions_count=Count('question')
        ).order_by('-id').values(
            'id', 'name', 'questions_count', 'attempt_limit', 'pass_threshold'
        )[:100]  # Ограничение на 100 тестов

    # Преобразуем QuerySet в список для JSON
    results = list(quizzes)

    return JsonResponse({
        'success': True,
        'results': results,
        'count': len(results)
    })
    

def get_questions(request, quiz_id: int = None, is_start: bool = False) -> HttpResponse:
    """
    Функция получения вопроса для тестирования. В зависимости от is_start определяется, является ли запрос стартовым.
    """
    if request.method == 'POST' or is_start:
        # Если is_start=True, quiz_id берется из URL
        if is_start and not quiz_id:
            return redirect('quizzes')
        
        # Получаем объект quiz для стартового вопроса
        if is_start:
            quiz = get_object_or_404(Quiz, id=quiz_id)
        
        # Проверяем ограничения попыток при старте теста
        if is_start and request.user.is_authenticated:
            
            # Проверяем доступ к курсу, если тест связан с курсом
            course_slug = request.GET.get('course_slug')
            from_control_panel = request.GET.get('from_control_panel')
            
            # Сохраняем параметр from_control_panel в сессии для использования в get_finish
            if from_control_panel:
                request.session['from_control_panel'] = True
            
            if course_slug:
                try:
                    course = Course.objects.get(slug=course_slug)
                    # Получаем UserCourse для проверки статуса
                    user_course = UserCourse.objects.filter(user=request.user, course=course).first()
                    if not user_course:
                        # Создаем UserCourse если его нет
                        user_course = UserCourse.objects.create(user=request.user, course=course, status='available')
                    
                    # Блокируем доступ к тесту, если курс не начат - редиректим на страницу курса с подсветкой
                    if user_course.status not in ['started', 'completed']:
                        from django.urls import reverse
                        from urllib.parse import urlencode
                        url = reverse('courses:course_detail', kwargs={'slug': course.slug})
                        params = urlencode({'highlight_start': '1', 'quiz_blocked': quiz.id})
                        return redirect(f'{url}?{params}')
                except Course.DoesNotExist:
                    pass
            else:
                # Если course_slug не передан, проверяем связь теста с курсом через модели
                # НО НЕ при запуске из панели управления
                if not from_control_panel:
                    from django.db import models
                    # Ищем курсы, связанные с этим тестом
                    related_courses = Course.objects.filter(
                        models.Q(final_quiz=quiz) | models.Q(course_quizzes=quiz)
                    ).distinct()
                    
                    if related_courses.exists():
                        # Берем первый связанный курс для определения контекста
                        course = related_courses.first()
                        # Сохраняем курс в сессии для использования в других частях приложения
                        request.session['course_slug'] = course.slug
                        
                        # Проверяем статус курса для пользователя
                        for course in related_courses:
                            user_course = UserCourse.objects.filter(user=request.user, course=course).first()
                            if not user_course:
                                user_course = UserCourse.objects.create(user=request.user, course=course, status='available')
                            
                            # Блокируем доступ к тесту, если курс не начат
                            if user_course.status not in ['started', 'completed']:
                                return render(request, 'courses/quiz_start_required.html', {'course': course})
                else:
                    # При запуске из панели управления очищаем курс из сессии
                    if 'course_slug' in request.session:
                        del request.session['course_slug']
            
            # Проверяем блокировку теста для этого пользователя
            # НО НЕ для администраторов, запускающих тест из панели управления
            if not from_control_panel:
                from .models import QuizLock
                quiz_lock, created = QuizLock.objects.get_or_create(
                    user=request.user,
                    quiz=quiz,
                    defaults={'is_locked': False}
                )
                
                if quiz_lock.is_locked:
                    return redirect('quizzes:attempt_limit_exceeded', quiz_id=quiz.id)
                
            # Создаем новую попытку
            attempts_count = QuizAttempt.objects.filter(user=request.user, quiz=quiz).count()
            QuizAttempt.objects.create(
                user=request.user,
                quiz=quiz,
                attempt_number=attempts_count + 1
            )
        
        # Если не стартовая страница, получаем quiz_id из сессии
        if not is_start:
            quiz_id = request.session.get('quiz_id')
            current_question_id = request.session.get('current_question_id')
            if not quiz_id or not current_question_id:
                return redirect('quizzes')
            
            # Получаем объект quiz для последующих вопросов
            quiz_obj = get_object_or_404(Quiz, id=quiz_id)

            # Получаем следующий вопрос
            question = _get_subsequent_question(quiz_id, current_question_id)
        else:
            # Для стартового вопроса quiz_obj уже определен выше как quiz
            quiz_obj = quiz
            
            # Сброс сессии при старте нового теста
            request.session['quiz_id'] = quiz_id
            request.session['score'] = 0
            request.session['current_question_id'] = None
            
            # Новая логика времени: накапливаем время только на страницах вопросов
            request.session['quiz_accumulated_time'] = 0  # в секундах
            request.session['question_start_time'] = None  # будет установлено при загрузке вопроса
            
            # Сохраняем course_slug если он передан в GET параметрах
            course_slug = request.GET.get('course_slug')
            if course_slug:
                request.session['course_slug'] = course_slug
            
            # Получаем первый вопрос
            question = _get_first_question(quiz_id)
            audit_logger.info(
            f'Приступил к прохождению теста с id={quiz_id}. Тест: {Quiz.objects.get(id=quiz_id).name}', 
            extra={
                'user': request.user.username if request.user.is_authenticated else 'Anonymous'
            }
        )

        if not question:
            audit_logger.info(
            f'Заверишл тест "{Quiz.objects.get(id=quiz_id).name}" (quiz_id: {quiz_id})', 
            extra={
                'user': request.user.username if request.user.is_authenticated else 'Anonymous'
            }
        )
            return redirect('quizzes:get-finish')
        
        # Обновление сессии
        request.session['current_question_id'] = question.id
        
        # Убеждаемся что quiz_obj определен (на случай если не попали ни в один блок выше)
        try:
            quiz_obj
        except NameError:
            quiz_obj = get_object_or_404(Quiz, id=quiz_id)
        
        # Для типа MATCH получаем в исходном порядке (пары не должны перемешиваться)
        # Для типа SEQUENCE получаем в исходном порядке, но потом перемешаем для отображения
        # Для остальных типов - в случайном порядке
        if question.question_type == Question.MATCH:
            answers = Answer.objects.filter(question=question).order_by('id')
        elif question.question_type == Question.SEQUENCE:
            answers = Answer.objects.filter(question=question).order_by('id')
        else:
            answers = Answer.objects.filter(question=question).order_by('?')
        
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

        # Подготавливаем данные для типов MATCH и SEQUENCE
        questions = {}
        match_answers = {}
        sequence_answers = {}
        
        if question.question_type == Question.SEQUENCE:
            # Для типа SEQUENCE получаем ответы и перемешиваем их для отображения
            answers_list = list(answers)
            import random
            shuffled_answers = answers_list.copy()
            random.shuffle(shuffled_answers)
            
            # Формируем словарь с перемешанными ответами
            for idx, ans in enumerate(shuffled_answers):
                sequence_answers[str(ans.id)] = {
                    'text': ans.text,
                    'image': ans.image.url if ans.image else None,
                    'display_order': idx + 1
                }
            
            # Переопределяем answers для шаблона
            answers = sequence_answers
        elif question.question_type == Question.MATCH:
            # Группируем ответы по парам (каждые 2 ответа - это пара вопрос-ответ)
            answers_list = list(answers)
            
            # Извлекаем вопросы (четные позиции) и ответы (нечетные позиции)
            questions_items = []
            answers_items = []
            
            for i in range(0, len(answers_list), 2):
                if i < len(answers_list):
                    # Четные элементы - это вопросы
                    question_answer = answers_list[i]
                    questions_items.append(question_answer)

                if i + 1 < len(answers_list):
                    # Нечетные элементы - это ответы
                    answer_answer = answers_list[i + 1]
                    answers_items.append(answer_answer)
            
            # Рандомизируем только ответы (перетаскиваемые элементы)
            import random
            random.shuffle(answers_items)
            
            # Формируем словари с информацией о тексте и изображении
            for q_ans in questions_items:
                questions[str(q_ans.id)] = {
                    'text': q_ans.text,
                    'image': q_ans.image.url if q_ans.image else None
                }
            
            for a_ans in answers_items:
                match_answers[str(a_ans.id)] = {
                    'text': a_ans.text,
                    'image': a_ans.image.url if a_ans.image else None
                }

            # Для типа MATCH переопределяем answers только ответами
            answers = match_answers

        # Получаем информацию о попытках для отображения
        attempts_info = {}
        if request.user.is_authenticated and quiz_obj.attempt_limit > 0:
            # Считаем неудачные попытки (исключаем те, что помечены как исключенные из лимита)
            failed_attempts = QuizResult.objects.filter(
                user=request.user,
                quiz_title=quiz_obj.name,
                passed=False,
                excluded_from_limit=False
            ).count()
            attempts_info = {
                'failed_attempts': failed_attempts,
                'attempt_limit': quiz_obj.attempt_limit,
                'attempts_left': quiz_obj.attempt_limit - failed_attempts
            }

        # Устанавливаем время начала работы над вопросом
        request.session['question_start_time'] = timezone.now().isoformat()
        request.session.modified = True
        
        # Вычисляем оставшееся время для таймера
        accumulated_time = request.session.get('quiz_accumulated_time', 0)
        time_limit_seconds = quiz_obj.time_limit * 60 if quiz_obj.time_limit > 0 else 0
        remaining_time_seconds = int(max(0, time_limit_seconds - accumulated_time)) if time_limit_seconds > 0 else 0
        
        # Отладочный вывод
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Timer debug: quiz_id={quiz_obj.id}, time_limit={quiz_obj.time_limit}, "
                   f"accumulated={accumulated_time}, remaining={remaining_time_seconds}")
        
        context = {
            'question': question,
            'answers': answers,
            'is_last': is_last,
            'current_question_number': current_index,
            'total_questions': total_questions,
            'progress_percent': progress_percent,
            'attempts_info': attempts_info,
            'question_type': question.question_type,
            'quiz': quiz_obj,
            'remaining_time_seconds': remaining_time_seconds,  # для JS таймера
            'accumulated_time': accumulated_time,  # для отображения
        }

        # Добавляем questions только для типа MATCH
        if question.question_type == Question.MATCH:
            context['questions'] = questions
        elif question.question_type == Question.SEQUENCE:
            # Для SEQUENCE сохраняем правильный порядок в сессии
            correct_order = list(Answer.objects.filter(question=question).order_by('id').values_list('id', flat=True))
            if 'sequence_correct_orders' not in request.session:
                request.session['sequence_correct_orders'] = {}
            request.session['sequence_correct_orders'][str(question.id)] = correct_order
            request.session.modified = True

        return render(request, 'quizzes/question.html', context)
    
    return redirect(request.META['HTTP_REFERER'])

def _get_first_question(quiz_id: int) -> Optional[Question]:
    return Question.objects.filter(quiz_id=quiz_id).order_by('id').first()

def _get_subsequent_question(quiz_id: int, current_id: int) -> Optional[Question]:
    return Question.objects.filter(
        quiz_id=quiz_id,
        id__gt=current_id
    ).order_by('id').first()




def get_answer(request) -> HttpResponse:
    if request.method == 'POST':
        current_question_id = request.session.get('current_question_id')
        quiz_id = request.session.get('quiz_id')
        question = get_object_or_404(Question, id=current_question_id)
        is_correct = False

        # Накапливаем время, потраченное на текущий вопрос
        question_start_time_str = request.session.get('question_start_time')
        if question_start_time_str:
            from datetime import datetime
            try:
                question_start_time = datetime.fromisoformat(question_start_time_str)
                current_time = timezone.now()
                time_spent = (current_time - question_start_time).total_seconds()
                
                accumulated_time = request.session.get('quiz_accumulated_time', 0)
                request.session['quiz_accumulated_time'] = accumulated_time + time_spent
                request.session['question_start_time'] = None  # Сбрасываем
                request.session.modified = True
            except (ValueError, TypeError):
                pass

        # Получаем или инициализируем словарь ответов пользователя в сессии
        quiz_answers = request.session.get('quiz_answers', {})

        if question.question_type == Question.MULTIPLE:
            submitted_ids = request.POST.getlist('answer_ids')
            submitted_ids = [int(id) for id in submitted_ids]
            correct_answers = Answer.objects.filter(question=question, is_correct=True)
            correct_ids = set(correct_answers.values_list('id', flat=True))
            submitted_set = set(submitted_ids)
            is_correct = (submitted_set == correct_ids and len(submitted_ids) == len(correct_ids))

            # Сохраняем выбранные ответы в сессии
            quiz_answers[str(question.id)] = {
                'selected_ids': submitted_ids,
                'is_correct': is_correct,
                'question_type': 'multiple'
            }

            context = {
                'current_question_number': list(Question.objects.filter(quiz_id=quiz_id).order_by('id').values_list('id', flat=True)).index(current_question_id) + 1,
                'total_questions': Question.objects.filter(quiz_id=quiz_id).count(),
                'progress_percent': int(((list(Question.objects.filter(quiz_id=quiz_id).order_by('id').values_list('id', flat=True)).index(current_question_id) + 1) / Question.objects.filter(quiz_id=quiz_id).count()) * 100),
                'is_correct': is_correct,
                'question': question,
                'submitted_answers': Answer.objects.filter(id__in=submitted_ids),
                'correct_answers': correct_answers,
            }
        elif question.question_type == Question.TEXT:
            user_text = request.POST.get('answer_text', '').strip()
            quiz_answers[str(question.id)] = {
                'answer_text': user_text,
                'question_type': 'text'
            }
            all_questions_ids = list(Question.objects.filter(quiz_id=quiz_id).order_by('id').values_list('id', flat=True))
            current_index = all_questions_ids.index(question.id) + 1
            total_questions = len(all_questions_ids)
            is_last = not Question.objects.filter(quiz_id=quiz_id, id__gt=question.id).exists()
            context = {
                'current_question_number': current_index,
                'total_questions': total_questions,
                'progress_percent': int((current_index / total_questions) * 100),
                'is_correct': False,  # для текстовых не бывает "правильно"
                'question': question,
                'user_text': user_text,
                'is_last': is_last,
            }
        elif question.question_type == Question.SEQUENCE:
            # Для типа последовательность получаем порядок элементов
            user_sequence = []
            sequence_data = request.POST.get('sequence_order', '')
            
            if sequence_data:
                user_sequence = [int(id) for id in sequence_data.split(',') if id.strip()]
            
            # Получаем правильную последовательность из сессии
            correct_sequence = request.session.get('sequence_correct_orders', {}).get(str(question.id), [])
            
            # Проверяем правильность последовательности
            is_correct = (user_sequence == correct_sequence)
            
            # Подсчитываем частичную правильность (для статистики)
            partial_score = 0
            if len(user_sequence) == len(correct_sequence):
                for i in range(len(user_sequence)):
                    if user_sequence[i] == correct_sequence[i]:
                        partial_score += 1
            
            partial_percent = int((partial_score / len(correct_sequence)) * 100) if correct_sequence else 0
            
            # Получаем данные ответов для отображения
            all_answers = Answer.objects.filter(question=question).order_by('id')
            answers_dict = {ans.id: {'text': ans.text, 'image': ans.image.url if ans.image else None} for ans in all_answers}
            
            quiz_answers[str(question.id)] = {
                'user_sequence': user_sequence,
                'correct_sequence': correct_sequence,
                'answers': answers_dict,
                'is_correct': is_correct,
                'partial_score': partial_score,
                'partial_percent': partial_percent,
                'question_type': 'sequence'
            }
            
            all_questions_ids = list(Question.objects.filter(quiz_id=quiz_id).order_by('id').values_list('id', flat=True))
            current_index = all_questions_ids.index(question.id) + 1
            total_questions = len(all_questions_ids)
            is_last = not Question.objects.filter(quiz_id=quiz_id, id__gt=question.id).exists()
            
            context = {
                'current_question_number': current_index,
                'total_questions': total_questions,
                'progress_percent': int((current_index / total_questions) * 100),
                'is_correct': is_correct,
                'question': question,
                'user_sequence': user_sequence,
                'correct_sequence': correct_sequence,
                'answers': answers_dict,
                'partial_score': partial_score,
                'partial_percent': partial_percent,
                'is_last': is_last,
            }
        elif question.question_type == Question.MATCH:
            # Для типа соответствие получаем соответствия вопрос-ответ
            user_matches = {}
            for key, value in request.POST.items():
                if key.startswith('match_') and value:
                    # Формат: match_question_id -> answer_id
                    question_id = key.replace('match_', '')
                    answer_id = value
                    user_matches[question_id] = answer_id

            # Получаем правильные соответствия
            correct_matches = {}
            all_answers = Answer.objects.filter(question=question)

            # Вопросы (неперетаскиваемые элементы справа)
            questions = {}
            # Ответы (перетаскиваемые элементы слева)
            answers = {}

            # Группируем ответы по парам (каждые 2 ответа - это пара вопрос-ответ)
            answers_list = list(all_answers)
            for i in range(0, len(answers_list), 2):
                if i < len(answers_list):
                    # Четные элементы - это вопросы
                    question_answer = answers_list[i]
                    question_key = str(question_answer.id)
                    questions[question_key] = {
                        'text': question_answer.text,
                        'image': question_answer.image.url if question_answer.image else None
                    }

                if i + 1 < len(answers_list):
                    # Нечетные элементы - это ответы
                    answer_answer = answers_list[i + 1]
                    answers[str(answer_answer.id)] = {
                        'text': answer_answer.text,
                        'image': answer_answer.image.url if answer_answer.image else None
                    }

            # Правильные соответствия - группируем ответы по парам (каждые 2 ответа - это пара вопрос-ответ)
            question_to_answer = {}
            answers_list = list(all_answers)

            for i in range(0, len(answers_list), 2):
                if i + 1 < len(answers_list):
                    question_answer = answers_list[i]
                    answer_answer = answers_list[i + 1]

                    # Если оба ответа отмечены как правильные, то это правильная пара
                    if question_answer.is_correct and answer_answer.is_correct:
                        question_to_answer[str(question_answer.id)] = str(answer_answer.id)

            # Если не нашли пары через is_correct, используем простую логику:
            # предполагаем, что правильные соответствия - это когда ответ соответствует вопросу
            if not question_to_answer:
                for i in range(0, len(answers_list), 2):
                    if i + 1 < len(answers_list):
                        question_answer = answers_list[i]
                        answer_answer = answers_list[i + 1]
                        question_to_answer[str(question_answer.id)] = str(answer_answer.id)

            correct_matches = question_to_answer

            # Проверяем правильность ответов пользователя
            is_correct = True
            for question_id, expected_answer_id in correct_matches.items():
                user_answer_id = user_matches.get(question_id)
                if user_answer_id != expected_answer_id:
                    is_correct = False
                    break

            quiz_answers[str(question.id)] = {
                'user_matches': user_matches,
                'correct_matches': correct_matches,
                'questions': questions,
                'answers': answers,
                'is_correct': is_correct,
                'question_type': 'match'
            }

            all_questions_ids = list(Question.objects.filter(quiz_id=quiz_id).order_by('id').values_list('id', flat=True))
            current_index = all_questions_ids.index(question.id) + 1
            total_questions = len(all_questions_ids)
            is_last = not Question.objects.filter(quiz_id=quiz_id, id__gt=question.id).exists()
            
            # Получаем данные для отображения результатов
            ans_data = quiz_answers[str(question.id)]
            user_matches = ans_data['user_matches']
            correct_matches = ans_data['correct_matches']
            questions = ans_data['questions']
            answers = ans_data['answers']

            # Подготавливаем данные для шаблона - создаем список с полной информацией о каждом вопросе
            match_results = []
            for question_id, question_data in questions.items():
                user_answer_id = user_matches.get(question_id, '')
                correct_answer_id = correct_matches.get(question_id, '')
                user_answer_data = answers.get(user_answer_id, {'text': 'Неизвестный ответ', 'image': None})
                correct_answer_data = answers.get(correct_answer_id, {'text': 'Неизвестный ответ', 'image': None})
                is_question_correct = (user_answer_id == correct_answer_id)
                
                match_results.append({
                    'question_id': question_id,
                    'question_text': question_data['text'],
                    'question_image': question_data['image'],
                    'user_answer_id': user_answer_id,
                    'user_answer_text': user_answer_data['text'],
                    'user_answer_image': user_answer_data['image'],
                    'correct_answer_id': correct_answer_id,
                    'correct_answer_text': correct_answer_data['text'],
                    'correct_answer_image': correct_answer_data['image'],
                    'is_correct': is_question_correct,
                })

            context = {
                'current_question_number': current_index,
                'total_questions': total_questions,
                'progress_percent': int((current_index / total_questions) * 100),
                'is_correct': ans_data['is_correct'],
                'question': question,
                'user_matches': user_matches,
                'correct_matches': correct_matches,
                'questions': questions,
                'answers': answers,
                'match_results': match_results,
                'is_last': is_last,
            }
        else:
            submitted_answer_id = request.POST.get('answer_id')
            if submitted_answer_id:
                submitted_answer = get_object_or_404(Answer, id=submitted_answer_id)
                is_correct = submitted_answer.is_correct

                # Сохраняем выбранный ответ в сессии
                quiz_answers[str(question.id)] = {
                    'selected_id': int(submitted_answer_id),
                    'is_correct': is_correct,
                    'question_type': 'single'
                }

                # Получаем правильные ответы (может быть несколько)
                correct_answers = Answer.objects.filter(question=question, is_correct=True)
                
                context = {
                    'current_question_number': list(Question.objects.filter(quiz_id=quiz_id).order_by('id').values_list('id', flat=True)).index(current_question_id) + 1,
                    'total_questions': Question.objects.filter(quiz_id=quiz_id).count(),
                    'progress_percent': int(((list(Question.objects.filter(quiz_id=quiz_id).order_by('id').values_list('id', flat=True)).index(current_question_id) + 1) / Question.objects.filter(quiz_id=quiz_id).count()) * 100),
                    'is_correct': is_correct,
                    'question': question,
                    'submitted_answer': submitted_answer,
                    'correct_answers': correct_answers,
                    
                }
            else:
                return redirect('quizzes')

        # Сохраняем обновлённые ответы в сессии
        request.session['quiz_answers'] = quiz_answers
        request.session.modified = True

        # Обновление счета (опционально, если нужен быстрый счёт)
        if is_correct:
            request.session['score'] = request.session.get('score', 0) + 1
            request.session.modified = True

        return render(request, 'quizzes/answer.html', context)
    
    return redirect('quizzes')



def get_finish(request) -> HttpResponse:
    if not request.user.is_authenticated:
        return redirect('users:login')

    quiz_id = request.session.get('quiz_id')
    if not quiz_id:
        return redirect('quizzes')
    
    quiz = get_object_or_404(Quiz, id=quiz_id)

    # Проверяем лимит времени
    time_exceeded = not _check_time_limit(request, quiz)
    
    questions_count = Question.objects.filter(quiz=quiz).count() # Количество вопросов в тесте всего
    text_questions_count = Question.objects.filter(question_type='text').filter(quiz=quiz).count() # количество открытых вопросов в тесте
    score = request.session.get('score', 0)
    is_all_question_text = False
    has_text_questions = text_questions_count > 0
    
    # Если в тесте есть открытые вопросы, тест получает статус 'pending' (ожидает проверки)
    quiz_status = 'pending' if has_text_questions else 'completed'
    
    if questions_count == text_questions_count:
        is_all_question_text = True
        # Для тестов только с открытыми вопросами процент устанавливается в 0 до проверки
        percent_score = 0
    else: 
        # Исключаем из подсчета только текстовые вопросы (match включаем, т.к. они автоматически проверяются)
        auto_checkable_questions = questions_count - text_questions_count
        percent_score = int((score / auto_checkable_questions) * 100) if auto_checkable_questions > 0 else 0

    # Для тестов с открытыми вопросами passed устанавливается в False до проверки наставником
    passed = (percent_score >= quiz.pass_threshold) and not has_text_questions and not time_exceeded # Проходной балл из настроек теста
    
    # Получаем курс для сохранения в результате
    course_slug = request.session.get('course_slug')
    from_control_panel = request.session.get('from_control_panel', False)
    course = None
    if course_slug:
        course = Course.objects.filter(slug=course_slug).first()
    
    # Проверяем, был ли тест уже пройден ранее в рамках этого курса
    previous_quiz_result = QuizResult.objects.filter(
        user=request.user,
        quiz_title=quiz.name,
        course=course,
        passed=True
    ).first()
    
    # Для тестов с TEXT вопросами сохраняем полное количество вопросов
    # score будет пересчитан наставником после проверки
    total_questions_to_save = questions_count if has_text_questions else (questions_count - text_questions_count)
    
    quiz_result = QuizResult.objects.create(
        user=request.user,
        quiz_title=quiz.name,
        course=course,
        score=score,
        total_questions=total_questions_to_save,
        percent=percent_score,
        passed=passed,
        status=quiz_status
    )
    
    # Отмечаем текущую попытку как завершенную
    if request.user.is_authenticated:
        current_attempt = QuizAttempt.objects.filter(
            user=request.user, 
            quiz=quiz, 
            completed_at__isnull=True
        ).first()
        if current_attempt:
            current_attempt.completed_at = timezone.now()
            current_attempt.save()
    
    # Проверяем, нужно ли заблокировать тест
    # НО НЕ для администраторов, запускающих тест из панели управления
    from_control_panel = request.session.get('from_control_panel', False)
    if request.user.is_authenticated and not passed and quiz.attempt_limit > 0 and not from_control_panel:
        from .models import QuizLock
        
        # Считаем количество неуспешных попыток в рамках этого курса (исключаем те, что помечены как исключенные из лимита)
        failed_attempts = QuizResult.objects.filter(
            user=request.user,
            quiz_title=quiz.name,
            course=course,
            passed=False,
            excluded_from_limit=False
        ).count()
        
        # Если достигли лимита - блокируем тест
        if failed_attempts >= quiz.attempt_limit:
            quiz_lock, created = QuizLock.objects.get_or_create(
                user=request.user,
                quiz=quiz,
                defaults={'is_locked': True, 'locked_at': timezone.now()}
            )
            if not created:
                quiz_lock.is_locked = True
                quiz_lock.locked_at = timezone.now()
                quiz_lock.save()
            
            # Списываем 15 баллов DASCOIN за блокировку теста
            from gamification.utils import deduct_dascoin_points
            deduct_dascoin_points(
                user=request.user,
                points=15,
                reason=f"Блокировка теста '{quiz.name}' за неуспешное прохождение"
            )

    # --- СОХРАНЯЕМ ОТВЕТЫ ПОЛЬЗОВАТЕЛЯ ---
    quiz_answers = request.session.get('quiz_answers', {})
    for q in Question.objects.filter(quiz=quiz):
        ans_data = quiz_answers.get(str(q.id))
        if not ans_data:
            continue
        if ans_data['question_type'] == 'multiple':
            for ans_id in ans_data['selected_ids']:
                ans = Answer.objects.get(id=ans_id)
                UserAnswer.objects.create(
                    user=request.user,
                    quiz_result=quiz_result,
                    question=q,
                    selected_answer=ans,
                    is_correct=ans.is_correct and ans_data['is_correct']
                )
        elif ans_data['question_type'] == 'text':
            answer_text = ans_data.get('answer_text', '')
            UserAnswer.objects.create(
                user=request.user,
                quiz_result=quiz_result,
                question=q,
                selected_answer=None,
                is_correct=None,
                answer_text=answer_text
            )
        elif ans_data['question_type'] == 'match':
            # Для типа соответствие сохраняем соответствия как текст
            matches_text = '; '.join([f"{q_id}:{a_id}" for q_id, a_id in ans_data.get('user_matches', {}).items()])
            UserAnswer.objects.create(
                user=request.user,
                quiz_result=quiz_result,
                question=q,
                selected_answer=None,
                is_correct=ans_data.get('is_correct', False),
                answer_text=matches_text
            )
        elif ans_data['question_type'] == 'sequence':
            # Для типа последовательность сохраняем порядок элементов как текст
            sequence_text = ','.join([str(ans_id) for ans_id in ans_data.get('user_sequence', [])])
            UserAnswer.objects.create(
                user=request.user,
                quiz_result=quiz_result,
                question=q,
                selected_answer=None,
                is_correct=ans_data.get('is_correct', False),
                answer_text=sequence_text
            )
        else:
            ans = Answer.objects.get(id=ans_data['selected_id'])
            UserAnswer.objects.create(
                user=request.user,
                quiz_result=quiz_result,
                question=q,
                selected_answer=ans,
                is_correct=ans.is_correct
            )
    # --------------------------------------------

    # Если тест имеет статус 'pending' (ожидает проверки), не обрабатываем его как пройденный/непройденный
    # Просто показываем страницу завершения
    if quiz_status == 'pending':
        auto_checkable_count = questions_count - text_questions_count
        context = {
            'score': score,  # Баллы только за автопроверяемые вопросы
            'auto_score': score,  # Явно указываем баллы за автопроверяемые
            'auto_questions_count': auto_checkable_count,  # Количество автопроверяемых вопросов
            'questions_count': questions_count,  # Всего вопросов (для будущего отображения)
            'total_questions': questions_count,  # Всего вопросов
            'text_questions_count': text_questions_count,  # Количество TEXT вопросов
            'percent_score': percent_score,
            'quiz_title': quiz.name,
            'is_all_question_text': is_all_question_text,
            'has_text_questions': has_text_questions,
            'quiz_status': quiz_status,
            'quiz_result': quiz_result,
            'time_exceeded': time_exceeded,
            'time_limit': quiz.time_limit if time_exceeded else None,
        }
        course_slug = request.session.pop('course_slug', None)
        request.session.pop('from_control_panel', None)
        if course_slug:
            context['course_slug'] = course_slug
        
        _reset_quiz(request)
        return render(request, 'quizzes/finish.html', context)

    # Обработка привязки к курсу (используем уже определенный курс из блока выше)
    if not course:
        # Fallback: старая логика если course_slug не указан или курс не найден
        if hasattr(quiz, 'course') and quiz.course:
            course = quiz.course
        else:
            # Проверяем, является ли этот тест финальным для какого-то курса
            course = Course.objects.filter(final_quiz=quiz).first()
            # Если тест используется в нескольких курсах, берем первый попавшийся
            if not course:
                course = quiz.courses.first()
    
    if course and passed:
        # Получаем UserCourse ТОЛЬКО если пользователь действительно проходит этот курс
        user_course = UserCourse.objects.filter(user=request.user, course=course, status='started').first()
        
        if user_course:
            # Проверяем, что все уроки курса завершены
            completed_lessons = UserProgress.objects.filter(
                user=request.user,
                course=course,
                completed=True
            ).count()
            total_lessons = course.lessons.count()
            
            # Проверяем, что все тесты курса пройдены в рамках этого курса (только уникальные по quiz_title)
            completed_quizzes = QuizResult.objects.filter(
                user=request.user,
                course=course,
                quiz_title__in=[q.name for q in course.quizzes.all()],
                passed=True
            ).values('quiz_title').distinct().count()
            total_quizzes = course.quizzes.count()
            
            # Завершаем курс только если все уроки И все тесты пройдены
            if completed_lessons >= total_lessons and completed_quizzes >= total_quizzes:
                # Начисляем очки за тест только если он не был пройден ранее И тест не запускается из панели управления И курс не является инцидентом
                if not previous_quiz_result and not from_control_panel and not course.is_incident:
                    award_dascoin_points(request.user, 10, f"Прохождение теста {quiz.name}")
                
                # Проверяем, есть ли финальный тест
                if course.final_quiz:
                    # Если есть финальный тест, проверяем, пройден ли он
                    final_quiz_passed = QuizResult.objects.filter(
                        user=request.user,
                        course=course,
                        quiz_title=course.final_quiz.name,
                        passed=True
                    ).exists()
                    
                    if final_quiz_passed:
                        # Финальный тест пройден - завершаем курс
                        if user_course.status != 'completed':
                            user_course.status = 'completed'
                            user_course.save()
                            # Начисляем баллы за завершение курса только если тест не запускается из панели управления И курс не является инцидентом
                            if not from_control_panel and not course.is_incident:
                                award_dascoin_points(request.user, course.points, f"Завершение курса {course.title}")
                                award_course_badge(request.user, course)
                                # Выдаем сертификат за курс (если настроено)
                                issue_certificate(request.user, course=course)
                    else:
                        # Финальный тест не пройден - редиректим на страницу с предложением пройти его
                        if percent_score == 100:
                            award_achievement(request.user, 'perfect_score', 'Идеальный результат', 'Получили 100% за прохождение теста')
                        return redirect('courses:redir_to_quiz', course_slug=course.slug)
                else:
                    # Финального теста нет - завершаем курс
                    if user_course.status != 'completed':
                        user_course.status = 'completed'
                        user_course.save()
                        # Начисляем баллы за завершение курса только если тест не запускается из панели управления И курс не является инцидентом
                        if not from_control_panel and not course.is_incident:
                            award_dascoin_points(request.user, course.points, f"Завершение курса {course.title}")
                            award_course_badge(request.user, course)
                            # Выдаем сертификат за курс (если настроено)
                            issue_certificate(request.user, course=course)
                
                if percent_score == 100:
                    award_achievement(request.user, 'perfect_score', 'Идеальный результат', 'Получили 100% за прохождение теста')
                # Если тест запускался из панели управления, возвращаемся туда
                if from_control_panel:
                    return redirect('quizzes:quizzes')
                return redirect('courses:course_detail', slug=course.slug)
            else:
                # Если не все уроки завершены, начисляем только очки за тест (если не из панели управления И курс не является инцидентом)
                if not previous_quiz_result and not from_control_panel and not course.is_incident:
                    award_dascoin_points(request.user, 10, f"Прохождение теста {quiz.name}")
                if percent_score == 100:
                    award_achievement(request.user, 'perfect_score', 'Идеальный результат', 'Получили 100% за прохождение теста')
                # Если тест запускался из панели управления, возвращаемся туда
                if from_control_panel:
                    return redirect('quizzes:quizzes')
                return redirect('courses:course_detail', slug=course.slug)
        else:
            # Если пользователь не проходит этот курс, начисляем только очки за тест (если не из панели управления И курс не является инцидентом)
            if not previous_quiz_result and not from_control_panel and not course.is_incident:
                award_dascoin_points(request.user, 10, f"Прохождение теста {quiz.name}")
            if percent_score == 100:
                award_achievement(request.user, 'perfect_score', 'Идеальный результат', 'Получили 100% за прохождение теста')
            # Если тест запускался из панели управления, возвращаемся туда
            if from_control_panel:
                return redirect('quizzes:quizzes')
    elif course and not passed:
        # Если тест запускается из панели управления - не показываем сообщения об ошибках курса
        if from_control_panel:
            return redirect('quizzes:quizzes')
        
        # Проверяем, является ли этот тест финальным для курса
        if course.final_quiz == quiz:
            # Считаем количество неуспешных попыток для этого теста в рамках курса (исключаем те, что помечены как исключенные из лимита)
            failed_attempts = QuizResult.objects.filter(
                user=request.user,
                course=course,
                quiz_title=quiz.name,
                passed=False,
                excluded_from_limit=False
            ).count()
            
            # Сбрасываем прогресс курса ТОЛЬКО если исчерпаны все попытки
            if quiz.attempt_limit > 0 and failed_attempts >= quiz.attempt_limit:
                # Сбрасываем прогресс курса - отмечаем все уроки как незавершенные
                UserProgress.objects.filter(user=request.user, course=course).update(completed=False)
                
                # Также сбрасываем статус курса на "начат"
                user_course = UserCourse.objects.filter(user=request.user, course=course).first()
                if user_course and user_course.status == 'completed':
                    user_course.status = 'started'
                    user_course.end_date = None
                    user_course.save()
                
                messages.error(request, f"Финальный тест не пройден! Исчерпаны все попытки. Прогресс курса '{course.title}' сброшен. Необходимо повторить материал.")
                return redirect('quizzes:attempt_limit_exceeded', quiz_id=quiz.id)
            else:
                # Обычная неудачная попытка - не сбрасываем прогресс
                attempts_left = quiz.attempt_limit - failed_attempts if quiz.attempt_limit > 0 else "неограниченно"
                attempts_text = f"Осталось попыток: {attempts_left}" if quiz.attempt_limit > 0 else "Попыток неограниченно"
                messages.error(request, f"Финальный тест не пройден! {attempts_text}. Попробуйте снова!")
        else:
            messages.error(request, "Тест не пройден. Попробуйте снова!")
        
        return redirect('quizzes:quiz_start', quiz_id=quiz.id)
    elif passed:
        # Если тест не привязан к курсу, но пройден - начисляем очки только если не был пройден ранее И не из панели управления
        if not previous_quiz_result and not from_control_panel:
            award_dascoin_points(request.user, 10, f"Прохождение теста {quiz.name}")
        if percent_score == 100:
            award_achievement(request.user, 'perfect_score', 'Идеальный результат', 'Получили 100% за прохождение теста')

    # Для completed статуса score уже включает баллы за TEXT (если они были оценены)
    # total_questions - это полное количество вопросов
    context = {
        'score': quiz_result.score,  # Используем score из quiz_result (может быть обновлен наставником)
        'questions_count': quiz_result.total_questions,  # Всего вопросов
        'total_questions': quiz_result.total_questions,
        'percent_score': quiz_result.percent,  # Используем percent из quiz_result
        'quiz_title': quiz.name,
        'is_all_question_text': is_all_question_text,
        'has_text_questions': has_text_questions,
        'quiz_status': quiz_status,
        'quiz_result': quiz_result,
        'time_exceeded': time_exceeded,
        'time_limit': quiz.time_limit if time_exceeded else None,
    }
    course_slug = request.session.pop('course_slug', None)
    request.session.pop('from_control_panel', None)  # Очищаем параметр из панели управления
    if course_slug:
        context['course_slug'] = course_slug
    
    _reset_quiz(request)
    return render(request, 'quizzes/finish.html', context)

def _check_time_limit(request, quiz) -> bool:
    """
    Проверяет, не превышено ли накопленное время на прохождение теста.
    Возвращает True если время не превышено, False если превышено.
    """
    if quiz.time_limit == 0:
        return True  # Без ограничения по времени
    
    accumulated_time = request.session.get('quiz_accumulated_time', 0)  # в секундах
    time_limit_seconds = quiz.time_limit * 60  # конвертируем минуты в секунды
    
    return accumulated_time <= time_limit_seconds

def _reset_quiz(request) -> HttpRequest:
    keys = ['quiz_id', 'current_question_id', 'score', 'quiz_accumulated_time', 'question_start_time', 'quiz_answers', 'sequence_correct_orders']
    for key in keys:
        if key in request.session:
            del request.session[key]
    return request




def quiz_best_result(request, quiz_id: int) -> HttpResponse:
    """
    Отображает лучший результат теста для пользователя в рамках курса.
    Если тест пройден выше проходного балла - показывает дату сдачи,
    если ниже - показывает последнюю попытку.
    """
    if not request.user.is_authenticated:
        return redirect('users:login')
    
    quiz = get_object_or_404(Quiz, id=quiz_id)
    course_slug = request.GET.get('course_slug')
    
    if not course_slug:
        return redirect('quizzes')
    
    course = get_object_or_404(Course, slug=course_slug)
    
    # Получаем лучший результат теста для этого пользователя в рамках курса
    best_result = QuizResult.objects.filter(
        user=request.user,
        quiz_title=quiz.name,
        course=course
    ).order_by('-percent', '-completed_at').first()
    
    if not best_result:
        # Если результатов нет, перенаправляем на начало теста
        return redirect('quizzes:quiz_start', quiz_id=quiz_id)
    
    # Получаем последнюю попытку для отображения даты
    last_attempt = QuizResult.objects.filter(
        user=request.user,
        quiz_title=quiz.name,
        course=course
    ).order_by('-completed_at').first()
    
    # Проверяем, есть ли в тесте открытые вопросы
    has_text_questions = Question.objects.filter(quiz=quiz, question_type=Question.TEXT).exists()
    
    # Проверяем, ожидает ли последняя попытка проверки наставником
    pending = False
    if has_text_questions and last_attempt and last_attempt.status == 'pending':
        pending = True

    context = {
        'quiz': quiz,
        'course': course,
        'best_result': best_result,
        'last_attempt': last_attempt,
        'passed': best_result.passed,
        'pass_threshold': quiz.pass_threshold,
        'has_text_questions': has_text_questions,
        'pending': pending,
        'mentor_comment': best_result.mentor_comment if best_result.mentor_comment else None,
        'reviewed_by': best_result.reviewed_by if best_result.reviewed_by else None,
    }
    
    return render(request, 'quizzes/quiz_best_result.html', context)




def start_quiz_handler(request):
    if request.method == 'POST':
        quiz_id = request.POST.get('quiz_id')
        if not quiz_id:
            return redirect('quizzes')
        
        # Сохраняем в сессии и перенаправляем на тест
        request.session['quiz_id'] = int(quiz_id)
        request.session['score'] = 0
        request.session['current_question_id'] = None
        return redirect('quizzes:quiz_start', quiz_id=quiz_id)
    
    return redirect('quizzes')


from django.views.generic import CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import JsonResponse
from django.urls import reverse_lazy

class QuizCreateView(UserPassesTestMixin, CreateView):
    """
    Создание нового теста с вопросами и ответами.
    """
    model = Quiz
    fields = ['name', 'attempt_limit', 'pass_threshold', 'time_limit']
    template_name = 'quizzes/quiz_form.html'
    success_url = '/builder/trajectory-management/'

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    def form_valid(self, form):
        # Проверяем, что это AJAX запрос для предотвращения дублирования
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            try:
                # Проверяем, не существует ли уже тест с таким именем
                quiz_name = form.cleaned_data.get('name')
                if Quiz.objects.filter(name=quiz_name).exists():
                    return JsonResponse({
                        'success': False, 
                        'error': f'Тест с названием "{quiz_name}" уже существует'
                    })
                
                # Создаем тест
                quiz = form.save()
            except Exception as e:
                return JsonResponse({
                    'success': False, 
                    'error': f'Ошибка при создании теста: {str(e)}'
                })
        else:
            # Если это не AJAX запрос, используем стандартное поведение
            return super().form_valid(form)
        
        # Обрабатываем вопросы и ответы
        try:
            # Парсим данные вопросов из формы
            questions_dict = {}
            for key, value in self.request.POST.items():
                if key.startswith('questions['):
                    try:
                        # Извлекаем номер вопроса и тип данных
                        # Формат: questions[1][text], questions[1][type], questions[1][answers][1][text], etc.
                        parts = key.replace('questions[', '').replace(']', '').split('[')
                        question_num = int(parts[0])
                        
                        if question_num not in questions_dict:
                            questions_dict[question_num] = {'text': '', 'type': 'single', 'answers': {}, 'correct_answer': None}
                        
                        if len(parts) == 2:
                            if parts[1] == 'text':
                                questions_dict[question_num]['text'] = value
                            elif parts[1] == 'type':
                                questions_dict[question_num]['type'] = value
                            elif parts[1] == 'correct_answer':
                                questions_dict[question_num]['correct_answer'] = int(value)
                        elif len(parts) == 4 and parts[1] == 'answers':
                            answer_num = int(parts[2])
                            answer_field = parts[3]
                            
                            if answer_num not in questions_dict[question_num]['answers']:
                                questions_dict[question_num]['answers'][answer_num] = {'text': '', 'correct': False}
                            
                            if answer_field == 'text':
                                questions_dict[question_num]['answers'][answer_num]['text'] = value
                            elif answer_field == 'correct':
                                questions_dict[question_num]['answers'][answer_num]['correct'] = True
                    except (ValueError, IndexError) as e:
                        # Пропускаем некорректные данные
                        continue
        except Exception as e:
            return JsonResponse({
                'success': False, 
                'error': f'Ошибка при обработке вопросов: {str(e)}'
            })
        
        # Создаем вопросы и ответы
        try:
            for question_num, question_data in questions_dict.items():
                if question_data['text'].strip():  # Проверяем, что текст вопроса не пустой
                    # Создаем вопрос
                    question = Question.objects.create(
                        quiz=quiz,
                        text=question_data['text'],
                        question_type=question_data['type']
                    )
                    
                    # Создаем ответы (только для вопросов с вариантами ответов)
                    if question_data['type'] in ['single', 'multiple', 'match', 'sequence']:
                        for answer_num, answer_data in question_data['answers'].items():
                            if answer_data['text'].strip():  # Проверяем, что текст ответа не пустой
                                # Для single вопросов правильность определяется через correct_answer
                                is_correct = answer_data['correct']
                                if question_data['type'] == 'single' and question_data['correct_answer']:
                                    is_correct = (answer_num == question_data['correct_answer'])
                                
                                Answer.objects.create(
                                    question=question,
                                    text=answer_data['text'],
                                    is_correct=is_correct
                                )
        except Exception as e:
            # Если произошла ошибка при создании вопросов, удаляем созданный тест
            quiz.delete()
            return JsonResponse({
                'success': False, 
                'error': f'Ошибка при создании вопросов: {str(e)}'
            })
        
        # Возвращаем JSON ответ для AJAX запроса
        return JsonResponse({
            'success': True, 
            'id': quiz.id, 
            'name': quiz.name,
            'questions_count': quiz.question_set.count()
        }, content_type='application/json')


class QuizEditView(UserPassesTestMixin, UpdateView):
    """
    Редактирование существующего теста с вопросами и ответами.
    """
    model = Quiz
    fields = ['name', 'attempt_limit', 'pass_threshold', 'time_limit']
    template_name = 'quizzes/quiz_edit.html'
    success_url = reverse_lazy('quizzes:quizzes')
    pk_url_kwarg = 'quiz_id'

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        quiz = self.get_object()
        
        # Получаем все вопросы с ответами
        questions = Question.objects.filter(quiz=quiz).prefetch_related('answer_set')
        
        # Для вопросов типа match подготавливаем пары
        questions_with_pairs = []
        for question in questions:
            question_data = {
                'question': question,
                'match_pairs': []
            }
            
            if question.question_type == 'match':
                answers = list(question.answer_set.all().order_by('id'))
                # Группируем ответы по парам
                for i in range(0, len(answers), 2):
                    if i + 1 < len(answers):
                        question_data['match_pairs'].append({
                            'pair_number': (i // 2) + 1,
                            'question_answer': answers[i],
                            'answer_answer': answers[i + 1],
                            'question_index': i + 1,
                            'answer_index': i + 2
                        })
            
            questions_with_pairs.append(question_data)
        
        context['questions'] = questions
        context['questions_with_pairs'] = questions_with_pairs
        context['question_types'] = Question.QUESTION_TYPES
        
        return context

    def form_valid(self, form):
        # Если это AJAX запрос
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            try:
                quiz = form.save()
                
                # Удаляем все существующие вопросы и ответы
                Question.objects.filter(quiz=quiz).delete()
                
                # Обрабатываем новые вопросы и ответы (аналогично созданию)
                questions_dict = {}
                for key, value in self.request.POST.items():
                    if key.startswith('questions['):
                        try:
                            parts = key.replace('questions[', '').replace(']', '').split('[')
                            question_num = int(parts[0])
                            
                            if question_num not in questions_dict:
                                questions_dict[question_num] = {'text': '', 'type': 'single', 'answers': {}, 'correct_answer': None}
                            
                            if len(parts) == 2:
                                if parts[1] == 'text':
                                    questions_dict[question_num]['text'] = value
                                elif parts[1] == 'type':
                                    questions_dict[question_num]['type'] = value
                                elif parts[1] == 'correct_answer':
                                    questions_dict[question_num]['correct_answer'] = int(value)
                            elif len(parts) == 4 and parts[1] == 'answers':
                                answer_num = int(parts[2])
                                answer_field = parts[3]
                                
                                if answer_num not in questions_dict[question_num]['answers']:
                                    questions_dict[question_num]['answers'][answer_num] = {'text': '', 'correct': False, 'image': None}
                                
                                if answer_field == 'text':
                                    questions_dict[question_num]['answers'][answer_num]['text'] = value
                                elif answer_field == 'correct':
                                    questions_dict[question_num]['answers'][answer_num]['correct'] = True
                        except (ValueError, IndexError):
                            continue
                
                # Обрабатываем загруженные файлы
                for key, file in self.request.FILES.items():
                    if key.startswith('questions['):
                        try:
                            parts = key.replace('questions[', '').replace(']', '').split('[')
                            if len(parts) == 4 and parts[1] == 'answers' and parts[3] == 'image':
                                question_num = int(parts[0])
                                answer_num = int(parts[2])
                                
                                if question_num in questions_dict and answer_num in questions_dict[question_num]['answers']:
                                    questions_dict[question_num]['answers'][answer_num]['image'] = file
                        except (ValueError, IndexError):
                            continue

                # Создаем новые вопросы и ответы
                for question_num, question_data in questions_dict.items():
                    if question_data['text'].strip():
                        question = Question.objects.create(
                            quiz=quiz,
                            text=question_data['text'],
                            question_type=question_data['type']
                        )
                        
                        if question_data['type'] in ['single', 'multiple', 'match', 'sequence']:
                            for answer_num, answer_data in question_data['answers'].items():
                                # Для match и sequence типа текст может быть пустым если есть изображение
                                if answer_data['text'].strip() or answer_data.get('image'):
                                    # Для single вопросов правильность определяется через correct_answer
                                    is_correct = answer_data['correct']
                                    if question_data['type'] == 'single' and question_data['correct_answer']:
                                        is_correct = (answer_num == question_data['correct_answer'])
                                    
                                    Answer.objects.create(
                                        question=question,
                                        text=answer_data['text'],
                                        is_correct=is_correct,
                                        image=answer_data.get('image')
                                    )

                return JsonResponse({
                    'success': True,
                    'message': 'Тест успешно обновлен'
                })
                
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': f'Ошибка при обновлении теста: {str(e)}'
                })
        
        return super().form_valid(form)


class QuizDeleteView(UserPassesTestMixin, DeleteView):
    """
    Удаление теста.
    """
    model = Quiz
    success_url = reverse_lazy('quizzes:quizzes')
    pk_url_kwarg = 'quiz_id'

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser


class AttemptLimitExceededView(LoginRequiredMixin, DetailView):
    """
    Страница превышения лимита попыток для теста.
    """
    model = Quiz
    template_name = 'quizzes/attempt_limit_exceeded.html'
    context_object_name = 'quiz'
    pk_url_kwarg = 'quiz_id'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        quiz = self.get_object()
        
        # Получаем курс из сессии, если он есть
        course_slug = self.request.session.get('course_slug')
        course = None

        if course_slug:
            course = Course.objects.filter(slug=course_slug).first()
        
        if not course:
            # Если курс не найден в сессии, ищем через final_quiz (fallback)
            course = Course.objects.filter(final_quiz=quiz).first()
        
        # Получаем количество неудачных попыток (как в логике блокировки)
        failed_attempts = QuizResult.objects.filter(
            user=self.request.user,
            quiz_title=quiz.name,
            course=course,
            passed=False,
            excluded_from_limit=False
        ).count()
        
        # Используем количество неудачных попыток для отображения
        attempts_count = failed_attempts
        
        # Если тест финальный и у пользователя есть прогресс по курсу - проверяем сброшен ли он
        course_progress_reset = False
        if course:
            user_course = UserCourse.objects.filter(user=self.request.user, course=course).first()
            if user_course:
                # Проверяем есть ли проваленные попытки финального теста (исключаем те, что помечены как исключенные из лимита)
                failed_attempts = QuizResult.objects.filter(
                    user=self.request.user,
                    quiz_title=quiz.name,
                    passed=False,
                    excluded_from_limit=False
                ).exists()
                course_progress_reset = failed_attempts
        
        context['attempts_count'] = attempts_count
        context['course'] = course
        context['course_progress_reset'] = course_progress_reset
        return context


class PendingQuizzesView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """
    Страница со списком тестов, ожидающих проверки наставником.
    Доступ только для администраторов и наставников.
    """
    template_name = 'quizzes/pending_quizzes.html'
    login_url = 'users:login'
    
    def test_func(self):
        """Проверка прав доступа"""
        if not self.request.user.is_authenticated:
            return False
        # Доступ для staff/superuser или наставников
        return (self.request.user.is_staff or 
                self.request.user.is_superuser or
                (hasattr(self.request.user, 'profile') and 
                 self.request.user.profile.is_mentor_user))
    
    def get_context_data(self, **kwargs):
        import datetime
        context = super().get_context_data(**kwargs)
        
        # Получаем фильтр из GET-параметров
        status_filter = self.request.GET.get('status', 'pending')
        
        # Фильтр по дате создания
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')

        # Фильтр по наставнику
        mentor_id = self.request.GET.get('mentor', '')
        
        # Фильтр по просроченным тестам
        is_overdue_filter = self.request.GET.get('is_overdue_filter', '')
        
        # Если нет параметров в GET запросе (первичная загрузка), устанавливаем дефолтные значения
        if not self.request.GET:
            # По умолчанию период с начала 2025 года до сегодняшней даты
            date_from = '2025-01-01'
            date_to = timezone.now().date().strftime('%Y-%m-%d')
            status_filter = 'pending'
        elif not date_from and not date_to:
            # Если статус changed, но даты не указаны, устанавливаем дефолтные
            if status_filter == 'reviewed':
                # Для проверенных - последние 30 дней
                date_to = timezone.now().date().strftime('%Y-%m-%d')
                date_from = (timezone.now().date() - timedelta(days=30)).strftime('%Y-%m-%d')
            else:
                # Для ожидающих проверки - с начала 2025 года
                date_from = '2025-01-01'
                date_to = timezone.now().date().strftime('%Y-%m-%d')
        
        # Фильтруем результаты тестов по статусу
        if status_filter == 'reviewed':
            # Только проверенные
            base_query = QuizResult.objects.filter(
                status='reviewed'
            )
        else:
            # По умолчанию только ожидающие проверки
            base_query = QuizResult.objects.filter(
                status='pending'
            )
        
        # Фильтрация по группам для наставников (не staff/superuser)
        if (hasattr(self.request.user, 'profile') and 
            self.request.user.profile.is_mentor_user and 
            not self.request.user.is_staff and 
            not self.request.user.is_superuser):
            # Получаем группы наставника
            mentor_groups = self.request.user.groups.all()
            if mentor_groups.exists():
                # Показываем только результаты тестов пользователей из групп наставника
                base_query = base_query.filter(user__groups__in=mentor_groups).distinct()
            else:
                # Если у наставника нет групп, показываем пустой список
                base_query = base_query.none()
        
        # Фильтр по дате прохождения
        if date_from:
            date_from_parsed = datetime.datetime.strptime(date_from, '%Y-%m-%d').date()
            date_from_datetime = timezone.make_aware(datetime.datetime.combine(date_from_parsed, datetime.time.min))
            base_query = base_query.filter(completed_at__gte=date_from_datetime)
        if date_to:
            date_to_parsed = datetime.datetime.strptime(date_to, '%Y-%m-%d').date()
            date_to_datetime = timezone.make_aware(datetime.datetime.combine(date_to_parsed, datetime.time.max))
            base_query = base_query.filter(completed_at__lte=date_to_datetime)

        # Фильтр по наставнику
        if mentor_id:
            base_query = base_query.filter(course__responsible_mentor_id=mentor_id)

        # Фильтр по просроченным тестам
        if is_overdue_filter:
            # Получаем текущее время
            now = timezone.now()
            # Фильтруем результаты, у которых есть курс с mentors_time_to_check и дедлайн просрочен
            # Дедлайн = completed_at + mentors_time_to_check дней
            # Получаем все результаты с курсами, у которых есть mentors_time_to_check
            results_with_courses = base_query.filter(
                course__isnull=False,
                course__mentors_time_to_check__isnull=False,
                course__mentors_time_to_check__gt=0
            ).select_related('course')
            
            # Фильтруем в Python, так как Django ORM не поддерживает умножение F на timedelta напрямую
            overdue_result_ids = []
            for result in results_with_courses:
                if result.completed_at and result.course.mentors_time_to_check:
                    deadline = result.completed_at + timedelta(days=result.course.mentors_time_to_check)
                    if deadline < now:
                        overdue_result_ids.append(result.id)
            
            # Применяем фильтр по ID просроченных результатов
            if overdue_result_ids:
                base_query = base_query.filter(id__in=overdue_result_ids)
            else:
                # Если нет просроченных результатов, возвращаем пустой queryset
                base_query = base_query.none()

        # Получаем список всех наставников из всех результатов (до фильтрации по наставнику)
        # Это нужно для того, чтобы в выпадающем списке были все наставники, а не только те, что в текущих результатах
        all_mentors_query = QuizResult.objects.filter(
            course__responsible_mentor__isnull=False
        ).values_list('course__responsible_mentor', flat=True).distinct()
        
        # Объекты User наставников
        mentors = User.objects.filter(id__in=all_mentors_query).order_by('first_name', 'last_name', 'username')
        
        # Для наставников (не staff/superuser) ограничиваем список наставников только собой
        if (hasattr(self.request.user, 'profile') and 
            self.request.user.profile.is_mentor_user and 
            not self.request.user.is_staff and 
            not self.request.user.is_superuser):
            mentors = mentors.filter(id=self.request.user.id)

        # Получаем только лучшие попытки для каждой комбинации (user, quiz_title, course)
        # Сначала получаем все результаты, затем фильтруем лучшие попытки
        # Сортируем по user, quiz_title, затем по course (с учетом NULL), затем по percent и completed_at
        all_results = base_query.select_related('user', 'course', 'course__responsible_mentor').order_by(
            'user_id', 'quiz_title', 'course_id', '-percent', '-completed_at'
        )
        
        # Группируем по (user, quiz_title, course) и берем первую (лучшую) попытку
        seen = set()
        best_result_ids = []
        for result in all_results:
            # Используем None для course_id, если курс не указан
            course_id = result.course_id if result.course_id else None
            key = (result.user_id, result.quiz_title, course_id)
            if key not in seen:
                seen.add(key)
                best_result_ids.append(result.id)
        
        # Фильтруем только лучшие попытки
        pending_results = base_query.filter(
            id__in=best_result_ids
        ).select_related('user', 'course', 'course__responsible_mentor').order_by('-completed_at')
        
        paginator = Paginator(pending_results, 20)
        page_number = self.request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        
        context['pending_results'] = page_obj
        context['page_obj'] = page_obj
        context['status_filter'] = status_filter
        context['now'] = timezone.now()
        
        # Передаем текущие значения фильтров в контекст
        context['date_from'] = date_from if date_from else ''
        context['date_to'] = date_to if date_to else ''
        context['mentors'] = mentors
        context['selected_mentor_id'] = mentor_id if mentor_id else ''
        context['is_overdue_filter'] = bool(is_overdue_filter)
        
        return context




class ReviewQuizView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """
    Страница для оценки открытых ответов теста наставником.
    Доступ только для администраторов и наставников.
    """
    model = QuizResult
    template_name = 'quizzes/review_quiz.html'
    context_object_name = 'quiz_result'
    pk_url_kwarg = 'result_id'
    login_url = 'users:login'
    
    def test_func(self):
        """Проверка прав доступа"""
        if not self.request.user.is_authenticated:
            return False
        
        # Доступ для staff/superuser
        if self.request.user.is_staff or self.request.user.is_superuser:
            return True
        
        # Доступ для наставников, но только для тестов пользователей из их групп
        if (hasattr(self.request.user, 'profile') and 
            self.request.user.profile.is_mentor_user):
            # Получаем объект результата теста
            result_id = self.kwargs.get('result_id')
            if result_id:
                try:
                    quiz_result = QuizResult.objects.get(id=result_id)
                    # Проверяем, что пользователь теста состоит в группах наставника
                    mentor_groups = self.request.user.groups.all()
                    if mentor_groups.exists():
                        user_groups = quiz_result.user.groups.all()
                        # Проверяем пересечение групп
                        return mentor_groups.filter(id__in=user_groups).exists()
                except QuizResult.DoesNotExist:
                    return False
        
        return False
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        quiz_result = self.get_object()
        
        # Получаем тест
        from quizzes.models import Quiz
        quiz = Quiz.objects.filter(name=quiz_result.quiz_title).first()
        
        # Получаем все ответы пользователя на открытые вопросы
        text_answers = UserAnswer.objects.filter(
            quiz_result=quiz_result,
            question__question_type=Question.TEXT
        ).select_related('question', 'user').order_by('question__id')
        
        # Получаем все ответы пользователя (для отображения полной информации)
        all_answers = UserAnswer.objects.filter(
            quiz_result=quiz_result
        ).select_related('question', 'selected_answer').order_by('question__id')
        
        # Группируем ответы по вопросам (особенно важно для MULTIPLE типа)
        grouped_answers = {}
        for answer in all_answers:
            if answer.question not in grouped_answers:
                grouped_answers[answer.question] = []
            grouped_answers[answer.question].append(answer)
        
        context['quiz'] = quiz
        context['text_answers'] = text_answers
        context['all_answers'] = all_answers
        context['grouped_answers'] = grouped_answers
        
        return context
    
    def post(self, request, *args, **kwargs):
        """Обработка оценки открытых ответов"""
        quiz_result = self.get_object()
        
        # Получаем оценки для каждого открытого вопроса
        text_answers = UserAnswer.objects.filter(
            quiz_result=quiz_result,
            question__question_type=Question.TEXT
        )
        
        total_text_score = 0.0
        for answer in text_answers:
            score_key = f'score_{answer.id}'
            score_value = request.POST.get(score_key, '0')
            
            # Преобразуем оценку в float
            try:
                score = float(score_value)
                # Ограничиваем значение от 0 до 1
                score = max(0, min(1, score))
            except ValueError:
                score = 0.0
            
            answer.score_points = score
            answer.is_correct = score > 0  # Считаем правильным, если балл > 0
            answer.save()
            
            total_text_score += score
        
        # Получаем комментарий наставника
        mentor_comment = request.POST.get('mentor_comment', '')
        
        # Пересчитываем общий результат теста с учетом оценок открытых вопросов
        from quizzes.models import Quiz
        quiz = Quiz.objects.filter(name=quiz_result.quiz_title).first()
        
        if quiz:
            # Считаем общее количество вопросов
            total_questions = Question.objects.filter(quiz=quiz).count()
            text_questions_count = Question.objects.filter(quiz=quiz, question_type=Question.TEXT).count()
            auto_checkable_count = total_questions - text_questions_count
            
            # Получаем баллы за автопроверяемые вопросы
            auto_score = quiz_result.score
            
            # Общий балл = баллы за автопроверяемые + баллы за открытые
            total_score = auto_score + total_text_score
            
            # Пересчитываем процент
            if total_questions > 0:
                percent_score = int((total_score / total_questions) * 100)
            else:
                percent_score = 0
            
            # Определяем, прошел ли пользователь тест
            passed = percent_score >= quiz.pass_threshold
            
            # Обновляем результат теста
            quiz_result.score = total_score  # Обновляем score с учетом баллов за TEXT вопросы
            quiz_result.percent = percent_score
            quiz_result.passed = passed
            quiz_result.status = 'reviewed'
            quiz_result.reviewed_by = request.user
            quiz_result.reviewed_at = timezone.now()
            quiz_result.mentor_comment = mentor_comment
            quiz_result.save()
            
            # Создаем уведомление для пользователя об оценке теста
            try:
                from notifications.models import Notification
                Notification.create_quiz_reviewed_notification(quiz_result)
            except Exception as e:
                # Логируем ошибку, но не прерываем процесс
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Ошибка создания уведомления об оценке теста: {e}")
            
            # Начисляем баллы и выдаем сертификаты, если тест пройден
            if passed:
                course = quiz_result.course
                from_control_panel = False  # Это проверка наставником, не из панели управления
                
                # Проверяем, был ли тест уже пройден ранее в рамках этого курса
                previous_quiz_result = QuizResult.objects.filter(
                    user=quiz_result.user,
                    quiz_title=quiz.name,
                    course=course,
                    passed=True,
                    completed_at__lt=quiz_result.completed_at
                ).first()
                
                if course:
                    # Получаем UserCourse ТОЛЬКО если пользователь действительно проходит этот курс
                    user_course = UserCourse.objects.filter(user=quiz_result.user, course=course, status='started').first()
                    
                    if user_course:
                        # Проверяем, что все уроки курса завершены
                        completed_lessons = UserProgress.objects.filter(
                            user=quiz_result.user,
                            course=course,
                            completed=True
                        ).count()
                        total_lessons = course.lessons.count()
                        
                        # Проверяем, что все тесты курса пройдены в рамках этого курса
                        completed_quizzes = QuizResult.objects.filter(
                            user=quiz_result.user,
                            course=course,
                            quiz_title__in=[q.name for q in course.quizzes.all()],
                            passed=True
                        ).count()
                        total_quizzes = course.quizzes.count()
                        
                        # Завершаем курс только если все уроки И все тесты пройдены
                        if completed_lessons >= total_lessons and completed_quizzes >= total_quizzes:
                            # Начисляем очки за тест только если он не был пройден ранее И курс не является инцидентом
                            if not previous_quiz_result and not course.is_incident:
                                award_dascoin_points(quiz_result.user, 10, f"Прохождение теста {quiz.name}")
                            
                            # Проверяем, есть ли финальный тест
                            if course.final_quiz:
                                # Если есть финальный тест, проверяем, пройден ли он
                                final_quiz_passed = QuizResult.objects.filter(
                                    user=quiz_result.user,
                                    course=course,
                                    quiz_title=course.final_quiz.name,
                                    passed=True
                                ).exists()
                                
                                if final_quiz_passed:
                                    # Финальный тест пройден - завершаем курс
                                    if user_course.status != 'completed':
                                        user_course.status = 'completed'
                                        user_course.save()
                                        # Начисляем баллы только если курс не является инцидентом
                                        if not course.is_incident:
                                            award_dascoin_points(quiz_result.user, course.points, f"Завершение курса {course.title}")
                                            award_course_badge(quiz_result.user, course)
                                            issue_certificate(quiz_result.user, course=course)
                            else:
                                # Финального теста нет - завершаем курс
                                if user_course.status != 'completed':
                                    user_course.status = 'completed'
                                    user_course.save()
                                    # Начисляем баллы только если курс не является инцидентом
                                    if not course.is_incident:
                                        award_dascoin_points(quiz_result.user, course.points, f"Завершение курса {course.title}")
                                        award_course_badge(quiz_result.user, course)
                                        issue_certificate(quiz_result.user, course=course)
                            
                            if percent_score == 100:
                                award_achievement(quiz_result.user, 'perfect_score', 'Идеальный результат', 'Получили 100% за прохождение теста')
                        else:
                            # Если не все уроки завершены, начисляем только очки за тест (если курс не является инцидентом)
                            if not previous_quiz_result and not course.is_incident:
                                award_dascoin_points(quiz_result.user, 10, f"Прохождение теста {quiz.name}")
                            if percent_score == 100:
                                award_achievement(quiz_result.user, 'perfect_score', 'Идеальный результат', 'Получили 100% за прохождение теста')
                    else:
                        # Если пользователь не проходит этот курс, начисляем только очки за тест (если курс не является инцидентом)
                        if not previous_quiz_result and not course.is_incident:
                            award_dascoin_points(quiz_result.user, 10, f"Прохождение теста {quiz.name}")
                        if percent_score == 100:
                            award_achievement(quiz_result.user, 'perfect_score', 'Идеальный результат', 'Получили 100% за прохождение теста')
                elif not previous_quiz_result:
                    # Если тест не привязан к курсу, но пройден - начисляем очки только если не был пройден ранее
                    award_dascoin_points(quiz_result.user, 10, f"Прохождение теста {quiz.name}")
                    if percent_score == 100:
                        award_achievement(quiz_result.user, 'perfect_score', 'Идеальный результат', 'Получили 100% за прохождение теста')
        
        messages.success(request, f'Оценка теста "{quiz_result.quiz_title}" для пользователя {quiz_result.user.username} сохранена.')
        return redirect('quizzes:pending_quizzes')
