import json

from django.core.cache import cache
from django.db.models import Max
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.generic import CreateView, DeleteView, ListView, TemplateView, UpdateView
from django.contrib import messages
from django.http import HttpResponse, JsonResponse

from builder.audit_logger import AuditLoggerMixin, log_actualize, log_create, serialize_model_data
from builder.models import CategoryName, DictionarySection, LessonVersion, LessonDraft
from builder.utils import (filter_categories_and_lessons_for_user, get_category_tree_data, 
                            get_compact_fio, get_responsible_user_for_lesson, user_has_category_access)
from courses.models import Lesson, UserLessonTrajectory
from myapp.models import UserCourse
from users.models import Role
from courses.forms import LessonForm
from builder.forms import LessonDraftForm
import difflib
from html import escape

import logging

logger = logging.getLogger(__name__)




@method_decorator(login_required(login_url='users:login'), name='dispatch')
class LessonMasterDetailView(TemplateView):
    """Мастер-страница БЗ: дерево категорий/уроков, версии, фильтрация и доступы."""
    template_name = 'builder/master_detail.html'

    def dispatch(self, request, *args, **kwargs):
        # Разрешаем просмотр всем аутентифицированным, но только staff/superuser могут редактировать
        if not request.user.is_authenticated:
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Корневые категории
        root_cats = CategoryName.objects.filter(parent__isnull=True)
        # Формируем дерево для каждой корневой категории
        context['categories'] = [get_category_tree_data(cat.id) for cat in root_cats]
        uncategorized_lessons = Lesson.objects.filter(category__isnull=True)
        user = self.request.user
        is_readonly = not (user.is_staff or user.is_superuser)
        context['is_readonly'] = is_readonly
        context['dictionary_sections'] = DictionarySection.objects.all().order_by('order', 'name')
        # Список ответственных всегда в context
        from django.contrib.auth import get_user_model
        User = get_user_model()
        context['responsibles'] = User.objects.filter(profile__role__responsible_user__isnull=False)
        context['roles'] = Role.objects.all().order_by('name')
        context['responsible_id_default'] = None
        # Применяем фильтрацию для readonly пользователей
        if is_readonly:
            context['categories'], context['uncategorized_lessons'] = filter_categories_and_lessons_for_user(
                user, context['categories'], uncategorized_lessons
            )
        else:
            context['uncategorized_lessons'] = uncategorized_lessons
        # Проверяем pk в URL и lesson_id в GET-параметрах
        pk = self.kwargs.get('pk') or self.request.GET.get('lesson_id')
        if pk:
            try:
                selected_lesson = Lesson.objects.get(pk=pk)
                # Для readonly пользователей проверяем доступ к уроку
                if is_readonly:
                    # Проверяем, есть ли урок в доступных для пользователя
                    user_courses = UserCourse.objects.filter(user=user).select_related('course')
                    allowed_courses = [uc.course for uc in user_courses if uc.status in ['available', 'started', 'completed']]
                    allowed_lesson_ids = set()
                    for course in allowed_courses:
                        trajectory = UserLessonTrajectory.objects.filter(user=user, course=course).first()
                        if trajectory:
                            allowed_lesson_ids.update(trajectory.lessons.values_list('id', flat=True))
                        else:
                            allowed_lesson_ids.update(course.lessons.values_list('id', flat=True))
                    
                    # --- ДОБАВЛЯЕМ уроки, назначенные пользователю напрямую ---
                    from courses.models import UserLesson
                    assigned_lesson_ids = UserLesson.objects.filter(user=user).values_list('lesson_id', flat=True)
                    allowed_lesson_ids.update(assigned_lesson_ids)
                    
                    # --- ДОБАВЛЯЕМ доступ через группы (категория и все родители) ---
                    group_access = False
                    cat = selected_lesson.category
                    while cat and not group_access:
                        if user_has_category_access(user, cat):
                            group_access = True
                        cat = cat.parent if cat else None
                    if selected_lesson.id not in allowed_lesson_ids and not group_access:
                        selected_lesson = None
                context['selected_lesson'] = selected_lesson
                # --- История версий ---
                lesson_versions = selected_lesson.versions.order_by('-version') if selected_lesson else []
            except Lesson.DoesNotExist:
                selected_lesson = None
                context['selected_lesson'] = None
                lesson_versions = []
            context['lesson_versions'] = lesson_versions
            if selected_lesson:
                # Подготавливаем JSON для версий
                versions_data = []
                for v in lesson_versions:
                    versions_data.append({
                        'version': v.version,  # Оставляем как число для корректного сравнения в JS
                        'title': v.title,
                        'content': v.content,
                        'video_id': v.video_id or ''
                    })
                context['lesson_versions_json'] = json.dumps(versions_data, ensure_ascii=False)
                # --- История актуализаций ---
                actualization_history = []
                for v in lesson_versions:
                    actualization_history.append({
                        'version': v.version,
                        'created_at': v.updated_at,
                        'next_update': v.next_update,
                        'update_period_days': v.update_period_days,
                        'responsible_role': getattr(getattr(v.updated_by, 'profile', None), 'role', None),
                        'responsible_fio': get_compact_fio(v.updated_by) if v.updated_by else None,
                    })
                # Берем информацию из последней версии (с максимальным номером)
                latest_version = lesson_versions.first() if lesson_versions else None
                context['actualization_info'] = {
                    'next_update': latest_version.next_update if latest_version else None,
                    'responsible_role': getattr(getattr(latest_version.updated_by, 'profile', None), 'role', None) if latest_version else None,
                }
                # Новый: id ответственного по умолчанию
                if latest_version and latest_version.updated_by:
                    context['responsible_id_default'] = latest_version.updated_by.id
                    # Проверяем, является ли текущий пользователь ответственным за урок
                    context['user_is_responsible_for_lesson'] = (
                        latest_version.updated_by == self.request.user
                    )
                else:
                    context['user_is_responsible_for_lesson'] = False
                # Добавляем информацию о предыдущей роли для автозаполнения
                if latest_version and latest_version.updated_by and latest_version.updated_by.profile and latest_version.updated_by.profile.role:
                    context['previous_role_id'] = latest_version.updated_by.profile.role.id
                    context['previous_role_name'] = latest_version.updated_by.profile.role.name
                else:
                    context['previous_role_id'] = None
                    context['previous_role_name'] = None
                context['actualization_history'] = actualization_history
                from django.utils import timezone
                context['today'] = timezone.now().date()
                
                # Проверяем наличие активных черновиков
                pending_draft = LessonDraft.objects.filter(lesson=selected_lesson, status='pending').first()
                context['pending_draft'] = pending_draft
            else:
                context['lesson_versions_json'] = json.dumps([], ensure_ascii=False)
                context['actualization_info'] = None
                context['actualization_history'] = []
                context['today'] = None
                context['user_is_responsible_for_lesson'] = False
        else:
            context['selected_lesson'] = None
            context['lesson_versions'] = []
            context['lesson_versions_json'] = json.dumps([], ensure_ascii=False)
            context['actualization_info'] = None
            context['actualization_history'] = []
            context['today'] = None
            context['user_is_responsible_for_lesson'] = False
        return context
    
    def get(self, request, *args, **kwargs):
        """
        GET:
        - При ?ajax=1 отдаёт detail-блок урока (без кэширования).
        - В остальных случаях отдаёт полную страницу без серверного page-cache.
        """
        # AJAX-блок детализации урока — НЕ кэшируем, всегда собираем свежий контекст
        if request.GET.get('ajax') == '1':
            from django.template.loader import render_to_string
            context = self.get_context_data(**kwargs)
            ajax_context = {
                'lesson': context.get('selected_lesson'),
                'lesson_versions': context.get('lesson_versions'),
                'lesson_versions_json': context.get('lesson_versions_json', json.dumps([], ensure_ascii=False)),
                'is_readonly': context.get('is_readonly'),
                'actualization_history': context.get('actualization_history'),
                'actualization_info': context.get('actualization_info'),
                'today': context.get('today'),
                'responsibles': context.get('responsibles'),
                'roles': context.get('roles'),
                'responsible_id_default': context.get('responsible_id_default'),
                'previous_role_id': context.get('previous_role_id'),
                'previous_role_name': context.get('previous_role_name'),
                'user_is_responsible_for_lesson': context.get('user_is_responsible_for_lesson', False),
                'pending_draft': context.get('pending_draft'),
            }
            return HttpResponse(
                render_to_string('builder/includes/_lesson_detail_block.html', ajax_context, request=request)
            )

        # Полная страница БЗ — без server-side кэширования
        return super().get(request, *args, **kwargs)




class LessonCreateView(CreateView, AuditLoggerMixin):
    model = Lesson
    fields = ['title', 'content', 'courses', 'category', 'required_time', 'final_quiz']
    template_name = 'builder/lesson_form.html'
    success_url = reverse_lazy('builder:lesson_master')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        category_id = self.kwargs.get('category_id')
        if category_id:
            category = get_object_or_404(CategoryName, pk=category_id)
            initial['category'] = category
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category_id = self.kwargs.get('category_id')
        if category_id:
            context['preselected_category'] = get_object_or_404(CategoryName, pk=category_id)
        # Сохраняем URL возврата в контексте для использования в шаблоне
        return_url = self.request.GET.get('return_url')
        if return_url:
            context['return_url'] = return_url
        return context

    def form_valid(self, form):
        """
        При создании урока порядковый номер (order) назначается автоматически:
        - если выбрана категория — последний среди уроков в этой категории
        - если категория не выбрана — последний среди уроков без категории
        """
        lesson = form.save(commit=False)
        if lesson.category:
            max_order = Lesson.objects.filter(category=lesson.category).aggregate(Max('order'))['order__max'] or 0
        else:
            max_order = Lesson.objects.filter(category__isnull=True).aggregate(Max('order'))['order__max'] or 0
        lesson.order = max_order + 1
        lesson.save()
        form.save_m2m()  # Сохраняем связи many-to-many с курсами
        
        # Логируем создание урока
        self.log_create_action(lesson, "Создан новый урок")
        
        # --- Создаём первую версию ---
        from django.utils import timezone
        today = timezone.now().date()
        # Для первой версии используем того, кто создал урок
        lesson_version = LessonVersion.objects.create(
            lesson=lesson,
            version=1,
            title=lesson.title,
            content=lesson.content,
            video_id=lesson.video_id,
            updated_by=self.request.user,
            next_update=today + timezone.timedelta(days=90),  # Стандартный период 90 дней
            update_period_days=90
        )
        
        # Логируем создание первой версии
        log_create(self.request.user, lesson_version, self.request, 
                  comment="Создана первая версия урока")
        
        return super().form_valid(form)


    def get_success_url(self):
        # Проверяем наличие параметра возврата
        return_url = self.request.GET.get('return_url')
        if return_url:
            # Декодируем URL и возвращаемся обратно
            from urllib.parse import unquote
            decoded_url = unquote(return_url)
            return decoded_url
        # Если параметра нет, возвращаемся в мастер уроков
        return f"{reverse('builder:lesson_master')}?new_lesson={self.object.id}"




class LessonUpdateView(UpdateView, AuditLoggerMixin):
    model = Lesson
    fields = ['title', 'content', 'order', 'courses', 'category', 'required_time', 'final_quiz']
    template_name = 'builder/lesson_form.html'
    success_url = reverse_lazy('builder:lesson_master')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)
    
    def get_object(self, queryset=None):
        """Сохраняем старые значения для аудита"""
        obj = super().get_object(queryset)
        # Сохраняем старые значения в атрибуте объекта
        self.old_values = serialize_model_data(obj)
        return obj

    def form_valid(self, form):
        # Логируем изменения урока
        self.log_update_action(self.object, self.old_values, "Обновлен урок")
        
        response = super().form_valid(form)
        lesson = self.object
        
        # --- Определяем следующий номер версии ---
        last_version = LessonVersion.objects.filter(lesson=lesson).order_by('-version').first()
        next_version = (last_version.version + 1) if last_version else 1
        
        # --- Определяем период обновления и дату следующего обновления ---
        from django.utils import timezone
        today = timezone.now().date()
        period = last_version.update_period_days if last_version else 90
        
        # Определяем ответственного пользователя
        responsible_user = get_responsible_user_for_lesson(last_version) if last_version else self.request.user
        
        lesson_version = LessonVersion.objects.create(
            lesson=lesson,
            version=next_version,
            title=lesson.title,
            content=lesson.content,
            video_id=lesson.video_id,
            updated_by=responsible_user,
            next_update=today + timezone.timedelta(days=period),
            update_period_days=period
        )
        
        # Логируем создание новой версии
        log_create(self.request.user, lesson_version, self.request,
                  comment=f"Создана версия {next_version} при обновлении урока")
        
        return response

    def get_success_url(self):
        from django.urls import reverse
        return f"{reverse('builder:lesson_master')}?edited_lesson={self.object.id}"




class LessonDeleteView(DeleteView, AuditLoggerMixin):
    model = Lesson
    template_name = 'builder/lesson_confirm_delete.html'
    success_url = reverse_lazy('builder:lesson_master')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        """Логируем удаление урока"""
        self.object = self.get_object()
        # Логируем удаление урока
        self.log_delete_action(self.object, "Удален урок")
        return super().delete(request, *args, **kwargs)




class UpdateControlStandaloneView(TemplateView):
    """
    Централизованный мониторинг актуальности уроков.
    """
    template_name = 'builder/lesson_update_control_form.html'

    def dispatch(self, request, *args, **kwargs):
        is_staff_or_admin = request.user.is_staff or request.user.is_superuser
        is_mentor = hasattr(request.user, 'profile') and request.user.profile.is_mentor_user
        
        if not request.user.is_authenticated or not (is_staff_or_admin or is_mentor):
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from courses.models import Lesson, UserLesson
        from django.utils import timezone
        
        user = self.request.user
        is_staff_or_admin = user.is_staff or user.is_superuser
        is_mentor = hasattr(user, 'profile') and user.profile.is_mentor_user
        
        # Для staff/superuser показываем все уроки, для наставников - только доступные
        if is_staff_or_admin:
            lessons = Lesson.objects.select_related('category').all()
        else:
            # Для наставников получаем уроки через курсы и назначенные напрямую
            allowed_lesson_ids = set()
            
            # Уроки из назначенных курсов
            user_courses = UserCourse.objects.filter(user=user).select_related('course')
            allowed_courses = [uc.course for uc in user_courses if uc.status in ['available', 'started', 'completed']]
            for course in allowed_courses:
                trajectory = UserLessonTrajectory.objects.filter(user=user, course=course).first()
                if trajectory:
                    allowed_lesson_ids.update(trajectory.lessons.values_list('id', flat=True))
                else:
                    allowed_lesson_ids.update(course.lessons.values_list('id', flat=True))
            
            # Уроки, назначенные напрямую
            assigned_lesson_ids = UserLesson.objects.filter(user=user).values_list('lesson_id', flat=True)
            allowed_lesson_ids.update(assigned_lesson_ids)
            
            lessons = Lesson.objects.select_related('category').filter(id__in=allowed_lesson_ids)
        today = timezone.now().date()
        
        # По умолчанию — за весь период (пустые даты). Параметр all_dates=1 тоже сбрасывает фильтр по датам.
        all_dates = self.request.GET.get('all_dates') == '1'
        if all_dates:
            created_from = ''
            created_to = ''
        else:
            created_from = self.request.GET.get('created_from', '')
            created_to = self.request.GET.get('created_to', '')
        title_query = self.request.GET.get('title', '').strip()
        rows = []
        for lesson in lessons:
            versions = list(lesson.versions.order_by('-version'))
            if not versions:
                last_update = None
                period_between = None
                next_update = None
                responsible = None
            else:
                last = versions[0]
                last_update = last.updated_at.date() if last.updated_at else None
                next_update = last.next_update
                responsible = last.updated_by
                if last_update and next_update:
                    period_between = (next_update - last_update).days
                else:
                    period_between = None
            # Дата создания — из поля модели Lesson
            
            created = lesson.created_at.date() if lesson.created_at else None
            rows.append({
                'lesson_id': lesson.id,
                'created': created,
                'title': lesson.title,
                'category': lesson.category.name if lesson.category else '—',
                'last_update': last_update,
                'period_between': period_between,
                'next_update': next_update,
                'responsible': responsible,
                'responsible_id': responsible.id if responsible else None,
                'responsible_fio': get_compact_fio(responsible) if responsible else '—',
                'responsible_position': responsible.profile.role.name if responsible and responsible.profile and responsible.profile.role else '—',
                'is_overdue': next_update and next_update < today,
                'no_next': not next_update,
            })
        # Фильтрация
        show_overdue = self.request.GET.get('overdue')
        show_no_next = self.request.GET.get('no_next')
        show_no_responsible = self.request.GET.get('no_responsible')
        # Если нет GET-параметров — все фильтры включены по умолчанию
        if show_overdue is None and show_no_next is None and show_no_responsible is None and not self.request.GET:
            show_overdue = True
            show_no_next = True
            show_no_responsible = True
        else:
            show_overdue = show_overdue == '1'
            show_no_next = show_no_next == '1'
            show_no_responsible = show_no_responsible == '1'
        responsible_position = self.request.GET.get('responsible')
        filtered = rows
        # Фильтр по дате создания
        from datetime import datetime
        if created_from:
            dt_from = datetime.strptime(created_from, '%Y-%m-%d').date()
            filtered = [r for r in filtered if r['created'] and r['created'] >= dt_from]
        if created_to:
            dt_to = datetime.strptime(created_to, '%Y-%m-%d').date()
            filtered = [r for r in filtered if r['created'] and r['created'] <= dt_to]
        if show_overdue and show_no_next and show_no_responsible:
            filtered = [r for r in filtered if r['is_overdue'] or r['no_next'] or r['responsible_fio'] == '—']
        elif show_overdue and show_no_next:
            filtered = [r for r in filtered if r['is_overdue'] or r['no_next']]
        elif show_overdue and show_no_responsible:
            filtered = [r for r in filtered if r['is_overdue'] or r['responsible_fio'] == '—']
        elif show_no_next and show_no_responsible:
            filtered = [r for r in filtered if r['no_next'] or r['responsible_fio'] == '—']
        elif show_overdue:
            filtered = [r for r in filtered if r['is_overdue']]
        elif show_no_next:
            filtered = [r for r in filtered if r['no_next']]
        elif show_no_responsible:
            filtered = [r for r in filtered if r['responsible_fio'] == '—']
        if responsible_position:
            filtered = [r for r in filtered if r['responsible_position'] == responsible_position]
        if title_query:
            filtered = [r for r in filtered if title_query.lower() in r['title'].lower()]
        
        # Список должностей для фильтра
        from users.models import Role
        roles = Role.objects.all().order_by('name')
        
        # Должность текущего пользователя для кнопки "Мои к актуализации"
        user_role_name = None
        if hasattr(user, 'profile') and user.profile and user.profile.role:
            user_role_name = user.profile.role.name
        
        context['update_rows'] = filtered
        context['roles'] = roles
        context['show_overdue'] = show_overdue
        context['show_no_next'] = show_no_next
        context['show_no_responsible'] = show_no_responsible
        context['selected_responsible'] = responsible_position
        context['created_from'] = created_from
        context['created_to'] = created_to
        context['title_query'] = title_query
        context['user_role_name'] = user_role_name
        return context


    def post(self, request, *args, **kwargs):
        # Здесь обработай данные формы, сохрани изменения, и верни ответ
        # Например, просто рендерим ту же страницу с сообщением
        context = self.get_context_data(**kwargs)
        # Можно добавить обработку данных из request.POST
        context['success'] = True
        return self.render_to_response(context)




@login_required
def actualize_version(request):
    """
    POST: lesson_id, period, next_update, responsible_id
    Создаёт новую версию LessonVersion для урока (копирует поля из последней, увеличивает номер, next_update и ответственный — из формы)
    """
    import json
    import logging
    from django.utils import timezone
    from builder.models import LessonVersion
    from django.http import JsonResponse
    
    logger = logging.getLogger(__name__)
    logger.info(f"actualize_version called by user {request.user.username}")
    
    # Проверка прав доступа: staff/superuser имеют полный доступ
    # is_mentor_user может актуализировать только если он является ответственным за урок
    is_staff_or_admin = request.user.is_staff or request.user.is_superuser
    is_mentor = hasattr(request.user, 'profile') and request.user.profile.is_mentor_user
    
    if not is_staff_or_admin and not is_mentor:
        logger.warning(f"Access denied for user {request.user.username}")
        return JsonResponse({'error': 'Доступ запрещен'}, status=403)
    if request.method != 'POST':
        logger.warning(f"Invalid method {request.method} for user {request.user.username}")
        return JsonResponse({'error': 'Метод не разрешен'}, status=405)
    try:
        data = json.loads(request.body.decode('utf-8'))
        lesson_id = int(data.get('lesson_id'))
        period = int(data.get('period', 90))
        next_update_str = data.get('next_update')
        responsible_id = data.get('responsible_id')
        
        logger.info(f"Received data: lesson_id={lesson_id}, period={period}, next_update={next_update_str}, responsible_id={responsible_id}")
        
        # Валидация данных
        if not lesson_id:
            return JsonResponse({'error': 'lesson_id обязателен'}, status=400)
        if period < 1 or period > 180:
            return JsonResponse({'error': 'period должен быть от 1 до 180 дней'}, status=400)
    except Exception as e:
        logger.error(f"JSON parsing error: {e}")
        return JsonResponse({'error': f'Ошибка парсинга JSON: {str(e)}'}, status=400)
    from courses.models import Lesson
    try:
        lesson = Lesson.objects.get(pk=lesson_id)
        logger.info(f"Lesson found: {lesson.id} - {lesson.title}")
    except Lesson.DoesNotExist:
        logger.error(f"Lesson not found: {lesson_id}")
        return JsonResponse({'error': 'Урок не найден'}, status=404)
    
    last_version = lesson.versions.order_by('-version').first()
    if not last_version:
        logger.error(f"No versions found for lesson {lesson_id}")
        return JsonResponse({'error': 'У урока нет версий'}, status=400)
    
    # Для is_mentor_user (не staff/superuser) проверяем, что он является ответственным за урок
    if is_mentor and not is_staff_or_admin:
        responsible_user = last_version.updated_by
        if responsible_user != request.user:
            logger.warning(f"Access denied for mentor {request.user.username}: not responsible for lesson {lesson_id}")
            return JsonResponse({'error': 'Вы не являетесь ответственным за данный урок'}, status=403)
    
    logger.info(f"Last version: {last_version.version}")
    today = timezone.now().date()
    new_version = last_version.version + 1

    # Парсим дату next_update (YYYY-MM-DD или DD.MM.YYYY)
    from datetime import datetime, timedelta
    next_update = None
    if next_update_str:
        try:
            if '-' in next_update_str:
                next_update = datetime.strptime(next_update_str, '%Y-%m-%d').date()
            else:
                next_update = datetime.strptime(next_update_str, '%d.%m.%Y').date()
            logger.info(f"Parsed next_update: {next_update}")
        except Exception as e:
            logger.warning(f"Failed to parse next_update '{next_update_str}': {e}, using calculated date")
            next_update = today + timedelta(days=period)
    else:
        next_update = today + timedelta(days=period)
        logger.info(f"No next_update provided, using calculated date: {next_update}")
    
    logger.info(f"Final next_update: {next_update}")

    # Определяем ответственного пользователя по роли
    from django.contrib.auth import get_user_model
    from users.models import Role
    User = get_user_model()
    try:
        if responsible_id:
            # Получаем роль и находим ответственного пользователя
            try:
                role = Role.objects.get(id=responsible_id)
                logger.info(f"Role found: {role.id} - {role.name}")
                updated_by = role.responsible_user if role.responsible_user else request.user
                logger.info(f"Responsible user: {updated_by.username if updated_by else 'None'}")
            except Role.DoesNotExist:
                logger.error(f"Role not found: {responsible_id}")
                return JsonResponse({'error': 'Роль не найдена'}, status=400)
        else:
            updated_by = request.user
            logger.info(f"Using request user as responsible: {updated_by.username}")
    except Exception as e:
        logger.error(f"Error getting role: {e}")
        return JsonResponse({'error': f'Ошибка получения роли: {str(e)}'}, status=400)

    try:
        logger.info(f"Creating LessonVersion: lesson={lesson.id}, version={new_version}, updated_by={updated_by.id if updated_by else 'None'}")
        
        lv = LessonVersion.objects.create(
            lesson=lesson,
            version=new_version,
            title=last_version.title,
            content=last_version.content,
            video_id=last_version.video_id,
            updated_by=updated_by,
            next_update=next_update,
            update_period_days=period
        )
        
        # Логируем актуализацию урока
        log_actualize(request.user, lv, request, comment="Актуализация урока через AJAX")
        
        logger.info(f"LessonVersion created successfully: id={lv.id}")
        response_data = {'ok': True, 'new_version': lv.version, 'next_update': lv.next_update.strftime('%d.%m.%Y')}
        logger.info(f"Returning success response: {response_data}")
        return JsonResponse(response_data)
    except Exception as e:
        import traceback
        error_msg = f"Ошибка создания LessonVersion: {e}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        logger.error(f"Returning error response: {error_msg}")
        return JsonResponse({'error': error_msg}, status=500)


@login_required
def create_lesson_draft(request, lesson_id):
    """
    Создает черновик урока для редактирования наставниками и администраторами.
    Доступ: is_mentor_user, staff или superuser
    """
    is_mentor = hasattr(request.user, 'profile') and request.user.profile.is_mentor_user
    is_staff = request.user.is_staff or request.user.is_superuser
    
    if not (is_mentor or is_staff):
        return render(request, '403.html', status=403)
    
    lesson = get_object_or_404(Lesson, id=lesson_id)
    
    # Проверяем, есть ли уже активный черновик (pending)
    existing_draft = LessonDraft.objects.filter(lesson=lesson, status='pending').first()
    if existing_draft:
        # Если черновик уже существует, перенаправляем на редактирование
        return redirect('builder:lesson_draft_edit', pk=existing_draft.id)
    
    # Создаем новый черновик, копируя данные из урока
    draft = LessonDraft.objects.create(
        lesson=lesson,
        title=lesson.title,
        content=lesson.content,
        video_id=lesson.video_id,
        order=lesson.order,
        category=lesson.category,
        required_time=lesson.required_time,
        final_quiz=lesson.final_quiz,
        created_by=request.user,
        status='pending'
    )
    # Копируем связи с курсами
    draft.courses.set(lesson.courses.all())
    
    messages.success(request, 'Черновик урока создан. Теперь вы можете редактировать его.')
    return redirect('builder:lesson_draft_edit', pk=draft.id)


@method_decorator(login_required(login_url='users:login'), name='dispatch')
class LessonDraftUpdateView(UpdateView, AuditLoggerMixin):
    """
    Редактирование черновика урока.
    Доступ: только для наставников (is_mentor_user) и только для своих черновиков или pending черновиков
    """
    model = LessonDraft
    form_class = LessonDraftForm
    template_name = 'builder/lesson_draft_form.html'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return render(request, '403.html', status=403)
        
        # Проверяем права доступа
        is_mentor = hasattr(request.user, 'profile') and request.user.profile.is_mentor_user
        is_staff = request.user.is_staff or request.user.is_superuser
        
        if not (is_mentor or is_staff):
            return render(request, '403.html', status=403)
        
        draft = self.get_object()
        
        # Наставники могут редактировать только свои черновики или pending черновики
        if is_mentor and not is_staff:
            if draft.status != 'pending' or (draft.created_by != request.user):
                return render(request, '403.html', status=403)
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        """Передаем пользователя в форму для настройки полей"""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_success_url(self):
        messages.success(self.request, 'Черновик урока сохранен.')
        return reverse('builder:lesson_draft_edit', kwargs={'pk': self.object.id})
    
    def form_valid(self, form):
        # Если пользователь - наставник (не staff/superuser), сохраняем только content
        is_mentor = hasattr(self.request.user, 'profile') and self.request.user.profile.is_mentor_user
        is_staff = self.request.user.is_staff or self.request.user.is_superuser
        
        if is_mentor and not is_staff:
            # Для наставников сохраняем content и submit_comment, остальные поля берем из instance
            draft = form.save(commit=False)
            # Восстанавливаем значения из исходного объекта для всех полей кроме content и submit_comment
            original = self.get_object()
            draft.title = original.title
            draft.video_id = original.video_id
            draft.order = original.order
            draft.category = original.category
            draft.required_time = original.required_time
            draft.final_quiz = original.final_quiz
            # submit_comment уже сохранен через form.save(commit=False)
            draft.save()
            # Сохраняем связи many-to-many (курсы) из исходного объекта
            draft.courses.set(original.courses.all())
            draft.saved_at_least_once = True
            draft.save(update_fields=['saved_at_least_once'])
        else:
            # Для staff/superuser сохраняем все изменения
            self.object = form.save(commit=False)
            self.object.saved_at_least_once = True
            self.object.save()
            form.save_m2m()
            return redirect(self.get_success_url())
        
        return redirect(self.get_success_url())


@method_decorator(login_required(login_url='users:login'), name='dispatch')
class LessonDraftReviewView(TemplateView):
    """
    Просмотр diff черновика с оригинальным уроком и принятие/отклонение изменений.
    Доступ: только для staff/superuser
    """
    model = LessonDraft
    template_name = 'builder/lesson_draft_review.html'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)
    
    def get_object(self):
        """Получает объект черновика по pk из URL"""
        pk = self.kwargs.get('pk')
        return get_object_or_404(LessonDraft, pk=pk)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        draft = self.get_object()
        lesson = draft.lesson
        
        context['draft'] = draft
        context['lesson'] = lesson
        
        # Вычисляем diff для текстовых полей
        title_diff = self._get_text_diff(lesson.title, draft.title)
        content_diff = self._get_html_diff(lesson.content or '', draft.content or '')
        
        # Сравниваем другие поля
        changes = {
            'title_diff': title_diff if lesson.title != draft.title else None,
            'content_diff': content_diff if (lesson.content or '') != (draft.content or '') else None,
            'video_id': {'old': lesson.video_id or '', 'new': draft.video_id or ''} if lesson.video_id != draft.video_id else None,
            'order': {'old': lesson.order, 'new': draft.order} if lesson.order != draft.order else None,
            'category': {'old': lesson.category, 'new': draft.category} if lesson.category != draft.category else None,
            'required_time': {'old': lesson.required_time, 'new': draft.required_time} if lesson.required_time != draft.required_time else None,
            'final_quiz': {'old': lesson.final_quiz, 'new': draft.final_quiz} if lesson.final_quiz != draft.final_quiz else None,
        }
        
        # Сравниваем курсы
        lesson_courses = set(lesson.courses.all())
        draft_courses = set(draft.courses.all())
        if lesson_courses != draft_courses:
            changes['courses'] = {
                'old': list(lesson_courses),
                'new': list(draft_courses),
                'added': list(draft_courses - lesson_courses),
                'removed': list(lesson_courses - draft_courses),
            }
        else:
            changes['courses'] = None
        
        context['changes'] = changes
        return context
    
    def _get_text_diff(self, old_text, new_text):
        """Вычисляет diff для обычного текста и возвращает список словарей с типом строки"""
        old_lines = old_text.splitlines(keepends=True)
        new_lines = new_text.splitlines(keepends=True)
        diff = difflib.unified_diff(old_lines, new_lines, lineterm='', n=3)
        result = []
        for line in diff:
            line_type = 'context'
            if line.startswith('+') and not line.startswith('+++'):
                line_type = 'added'
            elif line.startswith('-') and not line.startswith('---'):
                line_type = 'removed'
            elif line.startswith('@@'):
                line_type = 'header'
            result.append({'type': line_type, 'text': line})
        return result
    
    def _strip_html_tags(self, html_content):
        """Извлекает чистый текст из HTML, сохраняя структуру абзацев"""
        from html.parser import HTMLParser
        from io import StringIO
        
        class MLStripper(HTMLParser):
            def __init__(self):
                super().__init__()
                self.reset()
                self.strict = False
                self.convert_charrefs = True
                self.text = StringIO()
                self.in_block = False
                
            def handle_starttag(self, tag, attrs):
                # Добавляем перенос строки для блочных элементов
                if tag in ('p', 'div', 'br', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'tr'):
                    if self.text.getvalue() and not self.text.getvalue().endswith('\n'):
                        self.text.write('\n')
                        
            def handle_endtag(self, tag):
                if tag in ('p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'ul', 'ol', 'table'):
                    if self.text.getvalue() and not self.text.getvalue().endswith('\n'):
                        self.text.write('\n')
                        
            def handle_data(self, d):
                self.text.write(d)
                
            def get_data(self):
                return self.text.getvalue()
        
        s = MLStripper()
        try:
            s.feed(html_content or '')
        except:
            return html_content or ''
        return s.get_data().strip()
    
    def _get_html_diff(self, old_html, new_html):
        """
        Вычисляет diff для HTML контента и возвращает список сегментов для inline отображения.
        Каждый сегмент имеет тип: 'unchanged', 'added', 'removed'
        """
        # Извлекаем чистый текст
        old_text = self._strip_html_tags(old_html)
        new_text = self._strip_html_tags(new_html)
        
        # Если тексты одинаковые (только HTML изменился), не показываем diff
        if old_text == new_text:
            return None
        
        # Разбиваем на слова, сохраняя пробелы и переносы
        import re
        
        def tokenize(text):
            """Разбивает текст на токены (слова, пробелы, пунктуация)"""
            # Разбиваем по границам слов, сохраняя разделители
            tokens = re.findall(r'\S+|\s+', text)
            return tokens
        
        old_tokens = tokenize(old_text)
        new_tokens = tokenize(new_text)
        
        # Используем SequenceMatcher для поиска различий
        matcher = difflib.SequenceMatcher(None, old_tokens, new_tokens)
        
        result = []
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                text = ''.join(old_tokens[i1:i2])
                if text.strip():  # Добавляем только непустые сегменты
                    result.append({'type': 'unchanged', 'text': text})
                elif text:  # Пробелы тоже добавляем
                    result.append({'type': 'unchanged', 'text': text})
            elif tag == 'replace':
                old_part = ''.join(old_tokens[i1:i2])
                new_part = ''.join(new_tokens[j1:j2])
                if old_part.strip():
                    result.append({'type': 'removed', 'text': old_part})
                if new_part.strip():
                    result.append({'type': 'added', 'text': new_part})
            elif tag == 'delete':
                old_part = ''.join(old_tokens[i1:i2])
                if old_part.strip():
                    result.append({'type': 'removed', 'text': old_part})
            elif tag == 'insert':
                new_part = ''.join(new_tokens[j1:j2])
                if new_part.strip():
                    result.append({'type': 'added', 'text': new_part})
        
        return result if result else None
    
    def post(self, request, *args, **kwargs):
        """Обработка принятия или отклонения черновика"""
        draft = self.get_object()
        action = request.POST.get('action')
        comment = request.POST.get('comment', '')
        
        if action == 'approve':
            # Применяем изменения к оригинальному уроку
            lesson = draft.lesson
            
            # Применяем все изменения из черновика
            # Важно: сохраняем контент напрямую из черновика, чтобы сохранить все форматирование
            # Используем update() для прямого обновления в БД, минуя возможную обработку полей модели
            Lesson.objects.filter(pk=lesson.pk).update(
                title=draft.title,
                content=draft.content,  # Сохраняем HTML с полным форматированием напрямую в БД
                video_id=draft.video_id,
                order=draft.order,
                category=draft.category,
                required_time=draft.required_time,
                final_quiz=draft.final_quiz
            )
            
            # Обновляем связи с курсами (many-to-many)
            lesson.courses.clear()
            lesson.courses.set(draft.courses.all())
            
            # Обновляем объект из БД, чтобы получить актуальные данные
            lesson.refresh_from_db()
            
            # Обновляем связи с курсами (many-to-many)
            lesson.courses.clear()
            lesson.courses.set(draft.courses.all())
            
            # --- Создаём новую версию урока (LessonVersion) ---
            from django.utils import timezone
            
            # Определяем следующий номер версии
            last_version = LessonVersion.objects.filter(lesson=lesson).order_by('-version').first()
            next_version = (last_version.version + 1) if last_version else 1
            
            # Определяем период обновления и дату следующего обновления
            today = timezone.now().date()
            period = last_version.update_period_days if last_version else 90
            
            # Определяем ответственного пользователя (сохраняем из последней версии или используем того, кто создал черновик)
            responsible_user = get_responsible_user_for_lesson(last_version) if last_version else draft.created_by
            
            lesson_version = LessonVersion.objects.create(
                lesson=lesson,
                version=next_version,
                title=lesson.title,
                content=lesson.content,
                video_id=lesson.video_id,
                updated_by=responsible_user,
                next_update=today + timezone.timedelta(days=period),
                update_period_days=period,
                comment=f"Применены изменения из черновика #{draft.id}"
            )
            
            # Логируем создание новой версии
            log_create(request.user, lesson_version, request,
                      comment=f"Создана версия {next_version} при применении черновика #{draft.id}")
            
            # Обновляем статус черновика
            draft.status = 'approved'
            draft.reviewed_by = request.user
            draft.reviewed_at = timezone.now()
            draft.review_comment = comment
            draft.save()
            
            messages.success(request, 'Изменения приняты и применены к уроку.')
            
        elif action == 'reject':
            # Отклоняем черновик
            from django.utils import timezone
            draft.status = 'rejected'
            draft.reviewed_by = request.user
            draft.reviewed_at = timezone.now()
            draft.review_comment = comment
            draft.save()
            
            messages.info(request, 'Черновик отклонен.')
        else:
            messages.error(request, 'Неизвестное действие.')
            return redirect('builder:lesson_draft_review', pk=draft.id)
        
        return redirect('builder:lesson_master')


@method_decorator(login_required(login_url='users:login'), name='dispatch')
class LessonDraftHistoryListView(ListView):
    """
    Список всех черновиков, созданных текущим пользователем.
    С фильтрацией по статусу и поиском по названию урока.
    """
    model = LessonDraft
    template_name = 'builder/lesson_draft_history_list.html'
    context_object_name = 'drafts'
    paginate_by = 20
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        """Фильтруем черновики по текущему пользователю и параметрам поиска"""
        if self.request.user.profile.is_mentor_user and not (self.request.user.is_staff or self.request.user.is_superuser):
            queryset = LessonDraft.objects.filter(created_by=self.request.user).select_related(
                'lesson', 'created_by', 'reviewed_by', 'category'
            ).prefetch_related('courses').order_by('-created_at')
        else:
            queryset = LessonDraft.objects.all()
        
        # Фильтр по статусу
        status = self.request.GET.get('status', '')
        if status in ['pending', 'approved', 'rejected']:
            queryset = queryset.filter(status=status)
        
        # Фильтрация своих черновиков
        is_draft_owner = self.request.GET.get('is_draft_owner', '')
        if is_draft_owner:
            queryset = queryset.exclude(created_by=self.request.user)
        
        # Поиск по названию урока
        search_query = self.request.GET.get('search', '').strip()
        if search_query:
            queryset = queryset.filter(lesson__title__icontains=search_query)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_status'] = self.request.GET.get('status', '')
        context['current_is_draft_owner_filter'] = self.request.GET.get('is_draft_owner', '')
        context['search_query'] = self.request.GET.get('search', '')
        return context


@method_decorator(login_required(login_url='users:login'), name='dispatch')
class LessonDraftHistoryDetailView(TemplateView):
    """
    Детальный просмотр черновика для пользователя, который его создал.
    Показывает diff изменений, комментарий проверяющего и результат.
    """
    template_name = 'builder/lesson_draft_history_detail.html'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return render(request, '403.html', status=403)
        
        # Проверяем доступ к черновику
        pk = kwargs.get('pk')
        if pk:
            draft = get_object_or_404(LessonDraft, pk=pk)
            if draft.created_by != request.user and not (request.user.is_staff or request.user.is_superuser):
                return render(request, '403.html', status=403)
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_object(self):
        """Получает объект черновика по pk из URL"""
        pk = self.kwargs.get('pk')
        return get_object_or_404(LessonDraft, pk=pk)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        draft = self.get_object()
        lesson = draft.lesson
        
        context['draft'] = draft
        context['lesson'] = lesson
        
        # Получаем версию урока, если есть
        try:
            latest_version = LessonVersion.objects.filter(lesson=lesson).order_by('-version').first()
            context['lesson_version'] = latest_version
        except:
            context['lesson_version'] = None
        
        # Вычисляем diff для текстовых полей
        title_diff = self._get_text_diff(lesson.title, draft.title)
        content_diff = self._get_html_diff(lesson.content or '', draft.content or '')
        
        # Сравниваем другие поля
        changes = {
            'title_diff': title_diff if lesson.title != draft.title else None,
            'content_diff': content_diff if (lesson.content or '') != (draft.content or '') else None,
            'video_id': {'old': lesson.video_id or '', 'new': draft.video_id or ''} if lesson.video_id != draft.video_id else None,
            'order': {'old': lesson.order, 'new': draft.order} if lesson.order != draft.order else None,
            'category': {'old': lesson.category, 'new': draft.category} if lesson.category != draft.category else None,
            'required_time': {'old': lesson.required_time, 'new': draft.required_time} if lesson.required_time != draft.required_time else None,
            'final_quiz': {'old': lesson.final_quiz, 'new': draft.final_quiz} if lesson.final_quiz != draft.final_quiz else None,
        }
        
        # Сравниваем курсы
        lesson_courses = set(lesson.courses.all())
        draft_courses = set(draft.courses.all())
        if lesson_courses != draft_courses:
            changes['courses'] = {
                'old': list(lesson_courses),
                'new': list(draft_courses),
                'added': list(draft_courses - lesson_courses),
                'removed': list(lesson_courses - draft_courses),
            }
        else:
            changes['courses'] = None
        
        context['changes'] = changes
        return context
    
    def _get_text_diff(self, old_text, new_text):
        """Вычисляет diff для обычного текста и возвращает список словарей с типом строки"""
        old_lines = old_text.splitlines(keepends=True)
        new_lines = new_text.splitlines(keepends=True)
        diff = difflib.unified_diff(old_lines, new_lines, lineterm='', n=3)
        result = []
        for line in diff:
            line_type = 'context'
            if line.startswith('+') and not line.startswith('+++'):
                line_type = 'added'
            elif line.startswith('-') and not line.startswith('---'):
                line_type = 'removed'
            elif line.startswith('@@'):
                line_type = 'header'
            result.append({'type': line_type, 'text': line})
        return result
    
    def _strip_html_tags(self, html_content):
        """Извлекает чистый текст из HTML, сохраняя структуру абзацев"""
        from html.parser import HTMLParser
        from io import StringIO
        
        class MLStripper(HTMLParser):
            def __init__(self):
                super().__init__()
                self.reset()
                self.strict = False
                self.convert_charrefs = True
                self.text = StringIO()
                self.in_block = False
                
            def handle_starttag(self, tag, attrs):
                if tag in ('p', 'div', 'br', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'tr'):
                    if self.text.getvalue() and not self.text.getvalue().endswith('\n'):
                        self.text.write('\n')
                        
            def handle_endtag(self, tag):
                if tag in ('p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'ul', 'ol', 'table'):
                    if self.text.getvalue() and not self.text.getvalue().endswith('\n'):
                        self.text.write('\n')
                        
            def handle_data(self, data):
                self.text.write(data)
                
            def get_text(self):
                return self.text.getvalue()
        
        stripper = MLStripper()
        stripper.feed(html_content)
        return stripper.get_text()
    
    def _get_html_diff(self, old_html, new_html):
        """Вычисляет diff для HTML контента"""
        old_text = self._strip_html_tags(old_html)
        new_text = self._strip_html_tags(new_html)
        
        old_lines = old_text.splitlines(keepends=True)
        new_lines = new_text.splitlines(keepends=True)
        
        matcher = difflib.SequenceMatcher(None, old_lines, new_lines)
        result = []
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                for line in old_lines[i1:i2]:
                    result.append({'type': 'unchanged', 'text': line})
            elif tag == 'delete':
                for line in old_lines[i1:i2]:
                    result.append({'type': 'removed', 'text': line})
            elif tag == 'insert':
                for line in new_lines[j1:j2]:
                    result.append({'type': 'added', 'text': line})
            elif tag == 'replace':
                for line in old_lines[i1:i2]:
                    result.append({'type': 'removed', 'text': line})
                for line in new_lines[j1:j2]:
                    result.append({'type': 'added', 'text': line})
        
        return result

