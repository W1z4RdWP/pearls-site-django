from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Count, Exists, OuterRef
from django.contrib import messages
from django.views.generic import DetailView, TemplateView
from django.core.paginator import Paginator
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

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



def get_questions(request, quiz_id: int = None, is_start: bool = False) -> HttpResponse:
    """
    Функция получения вопроса для тестирования. В зависимости от is_start определяется, является ли запрос стартовым.
    """
    if request.method == 'POST' or is_start:
        # Если is_start=True, quiz_id берется из URL
        if is_start and not quiz_id:
            return redirect('quizzes')
        
        # Проверяем ограничения попыток при старте теста
        if is_start and request.user.is_authenticated:
            quiz = get_object_or_404(Quiz, id=quiz_id)
            
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
            elif not from_control_panel:
                # Если course_slug не передан И тест не запускается из панели управления, 
                # проверяем связь теста с курсом через модели
                from django.db import models
                # Ищем курсы, связанные с этим тестом
                related_courses = Course.objects.filter(
                    models.Q(final_quiz=quiz) | models.Q(course_quizzes=quiz)
                ).distinct()
                
                if related_courses.exists():
                    # Проверяем статус курса для пользователя
                    for course in related_courses:
                        user_course = UserCourse.objects.filter(user=request.user, course=course).first()
                        if not user_course:
                            user_course = UserCourse.objects.create(user=request.user, course=course, status='available')
                        
                        # Блокируем доступ к тесту, если курс не начат
                        if user_course.status not in ['started', 'completed']:
                            return render(request, 'courses/quiz_start_required.html', {'course': course})
            
            # Проверяем блокировку теста для этого пользователя
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

            # Получаем следующий вопрос
            question = _get_subsequent_question(quiz_id, current_question_id)
        else:
            # Сброс сессии при старте нового теста
            request.session['quiz_id'] = quiz_id
            request.session['score'] = 0
            request.session['current_question_id'] = None
            
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

        # Подготавливаем данные для типа MATCH
        questions = {}
        match_answers = {}
        if question.question_type == Question.MATCH:
            # Группируем ответы по парам (каждые 2 ответа - это пара вопрос-ответ)
            answers_list = list(answers)
            for i in range(0, len(answers_list), 2):
                if i < len(answers_list):
                    # Четные элементы - это вопросы
                    question_answer = answers_list[i]
                    question_key = str(question_answer.id)
                    questions[question_key] = question_answer.text

                if i + 1 < len(answers_list):
                    # Нечетные элементы - это ответы
                    answer_answer = answers_list[i + 1]
                    match_answers[str(answer_answer.id)] = answer_answer.text

            # Для типа MATCH переопределяем answers только ответами
            answers = match_answers

        # Получаем информацию о попытках для отображения
        attempts_info = {}
        if request.user.is_authenticated:
            quiz_obj = Quiz.objects.get(id=quiz_id)
            if quiz_obj.attempt_limit > 0:
                # Считаем неудачные попытки (как в course_detail.html)
                failed_attempts = QuizResult.objects.filter(
                    user=request.user,
                    quiz_title=quiz_obj.name,
                    passed=False
                ).count()
                attempts_info = {
                    'failed_attempts': failed_attempts,
                    'attempt_limit': quiz_obj.attempt_limit,
                    'attempts_left': quiz_obj.attempt_limit - failed_attempts
                }

        context = {
            'question': question,
            'answers': answers,
            'is_last': is_last,
            'current_question_number': current_index,
            'total_questions': total_questions,
            'progress_percent': progress_percent,
            'attempts_info': attempts_info,
            'question_type': question.question_type
        }

        # Добавляем questions только для типа MATCH
        if question.question_type == Question.MATCH:
            context['questions'] = questions

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
                    questions[question_key] = question_answer.text

                if i + 1 < len(answers_list):
                    # Нечетные элементы - это ответы
                    answer_answer = answers_list[i + 1]
                    answers[str(answer_answer.id)] = answer_answer.text

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
            for question_id, question_text in questions.items():
                user_answer_id = user_matches.get(question_id, '')
                correct_answer_id = correct_matches.get(question_id, '')
                user_answer_text = answers.get(user_answer_id, 'Неизвестный ответ')
                correct_answer_text = answers.get(correct_answer_id, 'Неизвестный ответ')
                is_question_correct = (user_answer_id == correct_answer_id)
                
                match_results.append({
                    'question_id': question_id,
                    'question_text': question_text,
                    'user_answer_id': user_answer_id,
                    'user_answer_text': user_answer_text,
                    'correct_answer_id': correct_answer_id,
                    'correct_answer_text': correct_answer_text,
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

    questions_count = Question.objects.filter(quiz=quiz).count() # Количество вопросов в тесте всего
    text_questions_count = Question.objects.filter(question_type='text').filter(quiz=quiz).count() # количество открытых вопросов в тесте
    score = request.session.get('score', 0)
    is_all_question_text = False
    if questions_count == text_questions_count:
        is_all_question_text = True
        percent_score = 100
    else: 
        # Исключаем из подсчета только текстовые вопросы (match включаем, т.к. они автоматически проверяются)
        auto_checkable_questions = questions_count - text_questions_count
        percent_score = int((score / auto_checkable_questions) * 100) if auto_checkable_questions > 0 else 0

    passed = percent_score >= quiz.pass_threshold # Проходной балл из настроек теста
    
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
    
    quiz_result = QuizResult.objects.create(
        user=request.user,
        quiz_title=quiz.name,
        course=course,
        score=score,
        total_questions=questions_count - text_questions_count, # Всего вопросов без учёта открытых (match включаем)
        percent=percent_score,
        passed=passed
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
    if request.user.is_authenticated and not passed and quiz.attempt_limit > 0:
        from .models import QuizLock
        
        # Считаем количество неуспешных попыток в рамках этого курса
        failed_attempts = QuizResult.objects.filter(
            user=request.user,
            quiz_title=quiz.name,
            course=course,
            passed=False
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
            UserAnswer.objects.create(
                user=request.user,
                quiz_result=quiz_result,
                question=q,
                selected_answer=None,
                is_correct=None,
                answer_text=ans_data.get('answer_text', '')
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
            
            # Проверяем, что все тесты курса пройдены в рамках этого курса
            completed_quizzes = QuizResult.objects.filter(
                user=request.user,
                course=course,
                quiz_title__in=[q.name for q in course.quizzes.all()],
                passed=True
            ).count()
            total_quizzes = course.quizzes.count()
            
            # Завершаем курс только если все уроки И все тесты пройдены
            if completed_lessons >= total_lessons and completed_quizzes >= total_quizzes:
                # Начисляем очки за тест только если он не был пройден ранее И тест не запускается из панели управления
                if not previous_quiz_result and not from_control_panel:
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
                            # Начисляем баллы за завершение курса только если тест не запускается из панели управления
                            if not from_control_panel:
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
                        # Начисляем баллы за завершение курса только если тест не запускается из панели управления
                        if not from_control_panel:
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
                # Если не все уроки завершены, начисляем только очки за тест (если не из панели управления)
                if not previous_quiz_result and not from_control_panel:
                    award_dascoin_points(request.user, 10, f"Прохождение теста {quiz.name}")
                if percent_score == 100:
                    award_achievement(request.user, 'perfect_score', 'Идеальный результат', 'Получили 100% за прохождение теста')
                # Если тест запускался из панели управления, возвращаемся туда
                if from_control_panel:
                    return redirect('quizzes:quizzes')
                return redirect('courses:course_detail', slug=course.slug)
        else:
            # Если пользователь не проходит этот курс, начисляем только очки за тест (если не из панели управления)
            if not previous_quiz_result and not from_control_panel:
                award_dascoin_points(request.user, 10, f"Прохождение теста {quiz.name}")
            if percent_score == 100:
                award_achievement(request.user, 'perfect_score', 'Идеальный результат', 'Получили 100% за прохождение теста')
            # Если тест запускался из панели управления, возвращаемся туда
            if from_control_panel:
                return redirect('quizzes:quizzes')
    elif course and not passed:
        # Проверяем, является ли этот тест финальным для курса
        if course.final_quiz == quiz:
            # Считаем количество неуспешных попыток для этого теста в рамках курса
            failed_attempts = QuizResult.objects.filter(
                user=request.user,
                course=course,
                quiz_title=quiz.name,
                passed=False
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
        
        # Если тест запускался из панели управления, возвращаемся туда
        if from_control_panel:
            return redirect('quizzes:quizzes')
        return redirect('quizzes:quiz_start', quiz_id=quiz.id)
    elif passed:
        # Если тест не привязан к курсу, но пройден - начисляем очки только если не был пройден ранее И не из панели управления
        if not previous_quiz_result and not from_control_panel:
            award_dascoin_points(request.user, 10, f"Прохождение теста {quiz.name}")
        if percent_score == 100:
            award_achievement(request.user, 'perfect_score', 'Идеальный результат', 'Получили 100% за прохождение теста')

    context = {
        'score': score,
        'questions_count': questions_count,
        'percent_score': percent_score,
        'quiz_title': quiz.name,
        'is_all_question_text': is_all_question_text,
    }
    course_slug = request.session.pop('course_slug', None)
    request.session.pop('from_control_panel', None)  # Очищаем параметр из панели управления
    if course_slug:
        context['course_slug'] = course_slug
    
    _reset_quiz(request)
    return render(request, 'quizzes/finish.html', context)

def _reset_quiz(request) -> HttpRequest:
    keys = ['quiz_id', 'current_question_id', 'score']
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
    
    context = {
        'quiz': quiz,
        'course': course,
        'best_result': best_result,
        'last_attempt': last_attempt,
        'passed': best_result.passed,
        'pass_threshold': quiz.pass_threshold,
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
    fields = ['name', 'attempt_limit', 'pass_threshold']
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
                    if question_data['type'] in ['single', 'multiple', 'match']:
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
    fields = ['name', 'attempt_limit', 'pass_threshold']
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
        context['questions'] = questions
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
                                    questions_dict[question_num]['answers'][answer_num] = {'text': '', 'correct': False}
                                
                                if answer_field == 'text':
                                    questions_dict[question_num]['answers'][answer_num]['text'] = value
                                elif answer_field == 'correct':
                                    questions_dict[question_num]['answers'][answer_num]['correct'] = True
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
                        
                        if question_data['type'] in ['single', 'multiple', 'match']:
                            for answer_num, answer_data in question_data['answers'].items():
                                if answer_data['text'].strip():
                                    # Для single вопросов правильность определяется через correct_answer
                                    is_correct = answer_data['correct']
                                    if question_data['type'] == 'single' and question_data['correct_answer']:
                                        is_correct = (answer_num == question_data['correct_answer'])
                                    
                                    Answer.objects.create(
                                        question=question,
                                        text=answer_data['text'],
                                        is_correct=is_correct
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
        
        # Получаем количество попыток пользователя
        attempts_count = QuizAttempt.objects.filter(
            user=self.request.user, 
            quiz=quiz
        ).count()
        
        # Получаем курс из сессии, если он есть
        course_slug = self.request.session.get('course_slug')
        course = None

        if course_slug:
            course = Course.objects.filter(slug=course_slug).first()
        
        if not course:
            # Если курс не найден в сессии, ищем через final_quiz (fallback)
            course = Course.objects.filter(final_quiz=quiz).first()
        
        # Если тест финальный и у пользователя есть прогресс по курсу - проверяем сброшен ли он
        course_progress_reset = False
        if course:
            user_course = UserCourse.objects.filter(user=self.request.user, course=course).first()
            if user_course:
                # Проверяем есть ли проваленные попытки финального теста
                failed_attempts = QuizResult.objects.filter(
                    user=self.request.user,
                    quiz_title=quiz.name,
                    passed=False
                ).exists()
                course_progress_reset = failed_attempts
        
        context['attempts_count'] = attempts_count
        context['course'] = course
        context['course_progress_reset'] = course_progress_reset
        return context
