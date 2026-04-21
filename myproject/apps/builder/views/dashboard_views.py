from django.db.models import Q
from django.shortcuts import render
from django.views.generic import TemplateView


class DashboardView(TemplateView):
    template_name = 'builder/dashboard.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Разрешаем доступ staff/superuser и наставникам
        if not request.user.is_authenticated:
            return render(request, '403.html', status=403)
        
        # Проверяем права доступа
        has_access = (
            request.user.is_staff or 
            request.user.is_superuser or 
            (hasattr(request.user, 'profile') and request.user.profile.is_mentor_user)
        )
        
        if not has_access:
            return render(request, '403.html', status=403)
            
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Проверяем, является ли пользователь наставником (но не staff/superuser)
        is_mentor_only = (hasattr(self.request.user, 'profile') and 
                         self.request.user.profile.is_mentor_user and 
                         not self.request.user.is_staff and 
                         not self.request.user.is_superuser)
        
        # Для наставников не показываем неоцененные ответы
        if not is_mentor_only:
            # Получаем неоцененные TEXT ответы
            from myapp.models import UserAnswer, QuizResult
            from quizzes.models import Question
            
            # Получаем все неоцененные ответы
            unrated_answers_queryset = UserAnswer.objects.filter(
                question__question_type='text',
                is_correct__isnull=True,  # Не оценено
                answer_text__isnull=False,  # Есть текстовый ответ
                answer_text__gt=''  # Не пустой ответ
            ).select_related('user', 'question', 'quiz_result', 'quiz_result__course')
            
            # Получаем все уникальные quiz_result из неоцененных ответов
            quiz_result_ids = unrated_answers_queryset.values_list('quiz_result_id', flat=True).distinct()
            quiz_results = QuizResult.objects.filter(id__in=quiz_result_ids).select_related('user', 'course').order_by(
                'user_id', 'quiz_title', 'course_id', '-percent', '-completed_at'
            )
            
            # Группируем результаты по (user, quiz_title, course) и находим лучшие попытки
            # Лучшая попытка = максимальный percent, при равенстве - последняя по дате
            # Благодаря сортировке первая попытка в каждой группе будет лучшей
            seen = set()
            best_result_ids = []
            for result in quiz_results:
                # Используем None для course_id, если курс не указан
                course_id = result.course_id if result.course_id else None
                key = (result.user_id, result.quiz_title, course_id)
                
                if key not in seen:
                    seen.add(key)
                    best_result_ids.append(result.id)
            
            # Преобразуем в set для более быстрого поиска
            best_result_ids = set(best_result_ids)
            
            # Фильтруем только ответы из лучших попыток
            unrated_answers_best = unrated_answers_queryset.filter(quiz_result_id__in=best_result_ids)
            
            # Общее количество неоцененных ответов из лучших попыток
            context['total_unrated_count'] = unrated_answers_best.count()
            
            # Для отображения ограничиваем до 20 записей для производительности
            unrated_text_answers = unrated_answers_best.order_by('-quiz_result__completed_at')[:20]
            
            # Группируем по пользователям и тестам для удобства
            grouped_answers = {}
            for answer in unrated_text_answers:
                key = f"{answer.user.username}_{answer.quiz_result.id}"
                if key not in grouped_answers:
                    grouped_answers[key] = {
                        'user': answer.user,
                        'quiz_result': answer.quiz_result,
                        'answers': []
                    }
                grouped_answers[key]['answers'].append(answer)
            
            context['unrated_text_answers'] = list(grouped_answers.values())
        else:
            # Для наставников - пустые значения
            context['total_unrated_count'] = 0
            context['unrated_text_answers'] = []
        
        # Топ-5 пользователей по DASCOIN из группы наставника
        if is_mentor_only:
            from django.contrib.auth.models import User
            # Получаем группы наставника
            mentor_department = self.request.user.profile.department
            if mentor_department:
                # Получаем топ-5 пользователей по DASCOIN из групп наставника
                top_users = User.objects.filter(
                    profile__department=mentor_department,
                    profile__is_approved=True
                ).exclude(
                    Q(is_superuser=True) | Q(is_staff=True) | Q(id=self.request.user.id)
                ).select_related('profile').order_by(
                    '-profile__dascoin_points', 'email'
                ).distinct()[:5]
                
                context['top_users_dascoin'] = top_users
            else:
                context['top_users_dascoin'] = []
        else:
            context['top_users_dascoin'] = []
        
        return context
