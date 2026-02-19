import json
import logging

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.urls import reverse
from django.utils.text import slugify

from gamification.models import DascoinTransaction
from myapp.models import QuizResult

audit_logger = logging.getLogger('api_audit')
logger = logging.getLogger('django')

PAGINATE_TRANSACTIONS_BY = 20


@login_required
@require_http_methods(["GET"])
def api_transactions(request):
    """API: история транзакций DASCOIN текущего пользователя (фильтрация, пагинация, статистика)."""
    user = request.user
    queryset = DascoinTransaction.objects.filter(user=user).order_by('-created_at')

    # Фильтрация по типу транзакции
    current_filter = request.GET.get('type', '')
    if current_filter in ('award', 'deduct', 'set', 'correction'):
        queryset = queryset.filter(transaction_type=current_filter)

    total_transactions = queryset.count()

    # Статистика по типам (всегда по всем транзакциям пользователя, без фильтра)
    all_transactions = DascoinTransaction.objects.filter(user=user)
    stats = {
        'award': all_transactions.filter(transaction_type='award').count(),
        'deduct': all_transactions.filter(transaction_type='deduct').count(),
        'set': all_transactions.filter(transaction_type='set').count(),
        'correction': all_transactions.filter(transaction_type='correction').count(),
    }

    # Пагинация
    page = request.GET.get('page', '1')
    try:
        page = max(1, int(page))
    except (ValueError, TypeError):
        page = 1

    paginator = Paginator(queryset, PAGINATE_TRANSACTIONS_BY)
    if page > paginator.num_pages and paginator.num_pages > 0:
        page = paginator.num_pages
    page_obj = paginator.get_page(page)

    transactions = [
        {
            'id': t.id,
            'created_at': t.created_at.strftime('%d.%m.%Y'),
            'created_at_time': t.created_at.strftime('%H:%M'),
            'transaction_type': t.transaction_type,
            'transaction_type_display': t.get_transaction_type_display(),
            'points_change': t.points_change,
            'points_before': t.points_before,
            'points_after': t.points_after,
            'reason': t.reason or None,
            'admin_user': (
                t.admin_user.get_full_name() or t.admin_user.username
            ) if t.admin_user else None,
        }
        for t in page_obj
    ]

    audit_logger.info(
        'Смотрит историю транзакций DASCOIN (API)',
        extra={
            'user': user.email or user.username,
        },
    )

    return JsonResponse({
        'transactions': transactions,
        'total_transactions': total_transactions,
        'current_filter': current_filter,
        'stats': stats,
        'pagination': {
            'page': page_obj.number,
            'num_pages': paginator.num_pages,
            'has_previous': page_obj.has_previous(),
            'has_next': page_obj.has_next(),
            'previous_page_number': page_obj.previous_page_number() if page_obj.has_previous() else None,
            'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None,
            'total_count': paginator.count,
            'start_index': page_obj.start_index(),
            'end_index': page_obj.end_index(),
        },
    })


@login_required
@require_http_methods(["POST"])
def api_password_change(request):
    """API: смена пароля текущего пользователя (требует старый пароль)."""
    
    try:
        data = json.loads(request.body)
        old_password = data.get('old_password', '').strip()
        new_password1 = data.get('new_password1', '').strip()
        new_password2 = data.get('new_password2', '').strip()
        
        user = request.user
        
        # Проверка старого пароля
        if not user.check_password(old_password):
            return JsonResponse({'error': 'Неверный текущий пароль.'}, status=400)
        
        # Валидация
        if not new_password1:
            return JsonResponse({'error': 'Новый пароль не может быть пустым.'}, status=400)
        
        if new_password1 != new_password2:
            return JsonResponse({'error': 'Пароли не совпадают.'}, status=400)
        
        if len(new_password1) < 8:
            return JsonResponse({'error': 'Пароль должен содержать минимум 8 символов.'}, status=400)
        
        # Используем PasswordChangeForm для валидации
        from django.contrib.auth.forms import PasswordChangeForm
        form = PasswordChangeForm(user=user, data={
            'old_password': old_password,
            'new_password1': new_password1,
            'new_password2': new_password2,
        })
        
        if form.is_valid():
            form.save()
            return JsonResponse({
                'success': True,
                'message': 'Пароль успешно изменён.'
            })
        else:
            # Собираем ошибки формы
            errors = {}
            for field, field_errors in form.errors.items():
                errors[field] = field_errors
            return JsonResponse({'error': 'Ошибка валидации пароля.', 'errors': errors}, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Неверный формат JSON.'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def api_quiz_attempts_report(request):
    """API: отчёт по попыткам тестов и заданий текущего пользователя."""
    try:
        from quizzes.models import Quiz, Question, HomeworkSubmission
        from courses.models import Lesson
        
        user = request.user
        
        # Получаем все результаты тестов пользователя
        all_results = QuizResult.objects.filter(user=user).order_by('-completed_at')
        
        # Группируем результаты по названию теста
        quiz_results_dict = {}
        for result in all_results:
            quiz_title = result.quiz_title
            if quiz_title not in quiz_results_dict:
                quiz_results_dict[quiz_title] = []
            quiz_results_dict[quiz_title].append(result)
        
        # Формируем список отчётов
        report_data = []
        
        for quiz_title, results in quiz_results_dict.items():
            # Находим Quiz по названию
            quiz = Quiz.objects.filter(name=quiz_title).first()
            
            if not quiz:
                continue
            
            # Проверяем, есть ли открытые вопросы в тесте
            has_open_questions = Question.objects.filter(
                quiz=quiz,
                question_type='text'
            ).exists()
            
            # Определяем, какой результат показывать
            if has_open_questions:
                # Если есть открытые вопросы - показываем проверенные попытки
                reviewed_results = [r for r in results if r.status == 'reviewed']
                if reviewed_results:
                    # Берём самую новую проверенную попытку (первая в списке, т.к. results отсортированы по дате убывания)
                    result = reviewed_results[0]
                else:
                    # Если нет проверенных, пропускаем этот тест
                    continue
            else:
                # Если нет открытых вопросов - показываем лучшую попытку
                # Проверяем, что есть результаты с percent
                results_with_percent = [r for r in results if r.percent is not None]
                if not results_with_percent:
                    continue
                result = max(results_with_percent, key=lambda r: r.percent)
            
            # Определяем статус
            if has_open_questions:
                if result.status == 'reviewed':
                    status = 'Пройден' if result.passed else 'Не пройден'
                elif result.status == 'pending':
                    status = 'На проверке'
                else:
                    status = 'Завершен'
            else:
                status = 'Пройден' if result.passed else 'Не пройден'
            
            # Получаем курс
            course_name = result.course.title if result.course else 'Не указан'
            course_slug = result.course.slug if result.course else None
            
            # Определяем тип теста
            quiz_type = 'Тест'  # По умолчанию - тест в материалах курса
            if result.course:
                # Проверяем, является ли тест финальным тестом курса
                if result.course.final_quiz and result.course.final_quiz.id == quiz.id:
                    quiz_type = 'Финальный тест курса'
                else:
                    # Проверяем, является ли тест финальным тестом урока
                    lesson_with_quiz = Lesson.objects.filter(final_quiz=quiz).first()
                    if lesson_with_quiz:
                        quiz_type = 'Финальный тест урока'
            
            # Подсчитываем правильные ответы
            # score может быть дробным из-за частичных баллов за открытые вопросы
            # Округляем до ближайшего целого для отображения
            correct_count = round(result.score) if result.score is not None else 0
            total_count = result.total_questions if result.total_questions is not None else 0
            
            # Формируем URL для лучшего результата теста
            quiz_url = None
            if quiz.id and course_slug:
                try:
                    quiz_url = reverse('quizzes:quiz_best_result', kwargs={'quiz_id': quiz.id}) + f'?course_slug={course_slug}'
                except Exception:
                    # Если не удалось сформировать URL, оставляем None
                    quiz_url = None
            
            report_data.append({
                'item_type': 'quiz',
                'quiz_name': quiz_title,
                'quiz_id': quiz.id,
                'course_name': course_name,
                'course_slug': course_slug,
                'quiz_type': quiz_type,
                'correct_count': correct_count,
                'total_count': total_count,
                'percent': round(result.percent, 1) if result.percent is not None else 0,
                'status': status,
                'status_slug': slugify(status),
                'completed_at': result.completed_at.isoformat() if result.completed_at else None,
                'quiz_url': quiz_url,
            })
        
        # Добавляем отправленные на проверку задания
        homework_submissions = HomeworkSubmission.objects.filter(user=user).select_related('homework', 'course')
        
        for submission in homework_submissions:
            # Определяем статус задания
            if submission.status == 'pending':
                status = 'Ожидает проверки'
            elif submission.status == 'correct':
                status = 'Правильно'
            elif submission.status == 'incorrect':
                status = 'Не правильно'
            else:
                status = submission.get_status_display()
            
            # Получаем курс
            course_name = submission.course.title if submission.course else 'Не указан'
            course_slug = submission.course.slug if submission.course else None
            
            report_data.append({
                'item_type': 'homework',
                'quiz_name': submission.homework.name,
                'quiz_id': None,
                'homework_id': submission.homework.id,
                'submission_id': submission.id,
                'course_name': course_name,
                'course_slug': course_slug,
                'quiz_type': 'Задание',
                'correct_count': None,
                'total_count': None,
                'percent': None,
                'status': status,
                'status_slug': slugify(status),
                'completed_at': submission.submitted_at.isoformat() if submission.submitted_at else None,
                'quiz_url': None,
            })
        
        # Сортируем по дате завершения (новые первыми)
        report_data.sort(key=lambda x: x['completed_at'] or '', reverse=True)
        
        audit_logger.info(
            'Смотрит отчёт по попыткам тестов и заданий (API)',
            extra={
                'user': user.email or user.username,
            },
        )
        
        return JsonResponse({
            'report_data': report_data,
            'total_count': len(report_data),
        })
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(
            f'Ошибка при получении отчёта по попыткам тестов (API): {str(e)}\n{error_traceback}',
            exc_info=True,
        )
        return JsonResponse({'error': f'Ошибка при получении данных: {str(e)}'}, status=500)
