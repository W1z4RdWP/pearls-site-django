from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, ListView, UpdateView, View

from builder.audit_logger import AuditLoggerMixin, serialize_model_data
from builder.forms import IncidentForm
from builder.models import Incident
from courses.models import Course, UserLessonTrajectory
from myapp.models import UserCourse, UserProgress


import logging

logger = logging.getLogger(__name__)



class IncidentListView(ListView):
    """
    Список инцидентов с фильтрацией и быстрым просмотром.
    """
    model = Incident
    template_name = 'builder/incidents.html'
    context_object_name = 'incidents'
    ordering = ['-created_at']

    def dispatch(self, request, *args, **kwargs):
        # Только staff/superuser
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        from django.utils import timezone
        import datetime
        
        queryset = super().get_queryset()
        
        # Оптимизация: предзагрузка ManyToMany полей
        queryset = queryset.prefetch_related('assigned_to', 'violators').select_related('user')
        
        # Фильтр по дате создания
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        date_from_datetime = None
        date_to_datetime = None
        
        # Если нет параметров в GET запросе (первичная загрузка), устанавливаем дефолтные значения
        if not self.request.GET:
            # Устанавливаем период с начала 2025 года до сегодняшней даты
            date_from = '2025-01-01'
            date_to = timezone.now().date().strftime('%Y-%m-%d')
        
        if date_from:
            date_from_parsed = datetime.datetime.strptime(date_from, '%Y-%m-%d').date()
            date_from_datetime = timezone.make_aware(datetime.datetime.combine(date_from_parsed, datetime.time.min))
            queryset = queryset.filter(created_at__gte=date_from_datetime)
        if date_to:
            date_to_parsed = datetime.datetime.strptime(date_to, '%Y-%m-%d').date()
            date_to_datetime = timezone.make_aware(datetime.datetime.combine(date_to_parsed, datetime.time.max))
            queryset = queryset.filter(created_at__lte=date_to_datetime)
        
        # Фильтр по статусу
        statuses = self.request.GET.getlist('status')
        
        # Если нет параметров в GET запросе (первичная загрузка), устанавливаем дефолтные статусы
        if not self.request.GET:
            statuses = ['new', 'accepted', 'assigned', 'studies_completed']
        
        if statuses:
            queryset = queryset.filter(status__in=statuses)
        
        # Фильтр по типу
        incident_type = self.request.GET.get('incident_type')
        if incident_type:
            queryset = queryset.filter(incident_type=incident_type)
        
        # Добавляем аннотации для подсчета назначенных и завершивших курс пользователей
        # Считаем только пользователей из assigned_to (сигнал синхронизирует доступ к курсу)
        # Исключаем админов, суперпользователей и авторов курса
        queryset = queryset.annotate(
            assigned_users_count=Count(
                'assigned_to',
                distinct=True,
                filter=Q(
                    course__isnull=False,
                    assigned_to__is_staff=False,
                    assigned_to__is_superuser=False
                ) & ~Q(assigned_to=F('course__author'))
            ),
            completed_users_count=Count(
                'assigned_to',
                distinct=True,
                filter=Q(
                    course__isnull=False,
                    course__usercourse__status='completed',
                    course__usercourse__user=F('assigned_to'),
                    assigned_to__is_staff=False,
                    assigned_to__is_superuser=False
                ) & ~Q(assigned_to=F('course__author'))
            )
        )
        
        # Обновляем статусы инцидентов с неоцененными открытыми ответами
        # Делаем это только для инцидентов с курсами, чтобы не делать лишних запросов
        # Проверяем до применения фильтров по статусу, чтобы не пропустить инциденты
        from builder.signals import check_and_update_incident_studies_completed_status
        from builder.models import Incident
        
        # Получаем все инциденты с курсами, которые могут иметь неоцененные ответы
        # Проверяем только те, которые могут быть в текущем queryset (по датам)
        incidents_to_check = Incident.objects.filter(
            course__isnull=False,
            status__in=['new', 'accepted', 'assigned', 'studies_completed']
        )
        
        # Применяем фильтры по дате, если они есть
        if date_from_datetime:
            incidents_to_check = incidents_to_check.filter(created_at__gte=date_from_datetime)
        if date_to_datetime:
            incidents_to_check = incidents_to_check.filter(created_at__lte=date_to_datetime)
        
        # Обновляем статусы
        for incident in incidents_to_check:
            try:
                check_and_update_incident_studies_completed_status(incident)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Ошибка при проверке статуса инцидента {incident.id}: {e}")
        
        return queryset

    def get_context_data(self, **kwargs):
        from django.utils import timezone
        
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Incident.STATUS_CHOICES
        context['incident_type_choices'] = Incident.INCIDENT_TYPE_CHOICES
        context['now'] = timezone.now()  # Текущая дата и время для проверки просроченных дедлайнов
        
        # Если нет параметров в GET запросе (первичная загрузка), устанавливаем дефолтные значения
        if not self.request.GET:
            context['selected_statuses'] = ['new', 'accepted', 'assigned', 'studies_completed']
            context['selected_incident_type'] = ''
            context['date_from'] = '2025-01-01'
            context['date_to'] = timezone.now().date().strftime('%Y-%m-%d')
        else:
            # Передаем текущие значения фильтров в контекст
            context['selected_statuses'] = self.request.GET.getlist('status', [])
            context['selected_incident_type'] = self.request.GET.get('incident_type', '')
            context['date_from'] = self.request.GET.get('date_from', '')
            context['date_to'] = self.request.GET.get('date_to', '')
        
        return context



class IncidentCreateView(CreateView, AuditLoggerMixin):
    """
    Создание инцидента (ручное или автоматическое).
    """
    model = Incident
    form_class = IncidentForm
    template_name = 'builder/incident_form.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)


    def get_success_url(self):
        """
        Возвращает URL для редиректа после успешного создания инцидента.
        Перенаправляет на страницу редактирования созданного инцидента.
        """
        return reverse('builder:incident_edit', kwargs={'pk': self.object.pk})


    def form_valid(self, form):
        # Устанавливаем статус "Принят" для нового инцидента
        form.instance.status = 'accepted'
        response = super().form_valid(form)
        # Логируем создание инцидента
        self.log_create_action(self.object, "Создан новый инцидент")
        return response




class IncidentUpdateView(UpdateView, AuditLoggerMixin):
    """
    Редактирование инцидента.
    """
    model = Incident
    form_class = IncidentForm
    template_name = 'builder/incident_form.html'
    success_url = reverse_lazy('builder:incidents')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        # Сохраняем старый список назначенных пользователей до сохранения формы
        old_assigned_users = set(self.object.assigned_to.all())
        
        # Получаем новый список назначенных пользователей из формы (до сохранения)
        new_assigned_users = set(form.cleaned_data.get('assigned_to', []))
        
        # Определяем, какие пользователи были удалены и добавлены
        removed_users = old_assigned_users - new_assigned_users
        added_users = new_assigned_users - old_assigned_users
        
        # Сохраняем форму
        response = super().form_valid(form)
        
        # Если у инцидента есть связанный курс, обновляем назначения курса
        if self.object.course:
            course = self.object.course
            
            # Удаляем назначение курса для пользователей, которые были удалены из списка назначенных
            for user in removed_users:
                UserCourse.objects.filter(user=user, course=course).delete()
            
            # Назначаем курс новым пользователям
            for user in added_users:
                UserCourse.objects.get_or_create(
                    user=user,
                    course=course,
                    defaults={'status': 'available', 'deadline': self.object.deadline}
                )
        
        # Логируем обновление инцидента
        self.log_update_action(self.object, "Инцидент обновлён")
        return response




@method_decorator(login_required, name='dispatch')
class IncidentDeclineView(View, AuditLoggerMixin):
    """
    Отклонение или возобновление инцидента.
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        incident_id = kwargs.get('pk')
        incident = get_object_or_404(Incident, pk=incident_id)
        
        # Сохраняем старые значения для аудита
        old_values = serialize_model_data(incident)
        
        if incident.status == 'declined':
            # Возобновляем инцидент - возвращаем предыдущий статус
            if incident.previous_status:
                incident.status = incident.previous_status
                incident.previous_status = None
                comment = f"Инцидент возобновлён. Статус изменён на '{incident.get_status_display()}'"
            else:
                # Если предыдущий статус не сохранён, устанавливаем 'new'
                incident.status = 'new'
                incident.previous_status = None
                comment = "Инцидент возобновлён. Статус изменён на 'Новый'"
        else:
            # Отклоняем инцидент - сохраняем текущий статус и устанавливаем 'declined'
            previous_status_display = dict(Incident.STATUS_CHOICES).get(incident.status, incident.status)
            incident.previous_status = incident.status
            incident.status = 'declined'
            comment = f"Инцидент отклонён. Предыдущий статус: '{previous_status_display}'"
        
        incident.save(update_fields=['status', 'previous_status', 'updated_at'])
        
        # Логируем действие
        self.log_update_action(incident, old_values, comment)
        
        return redirect('builder:incidents')




@method_decorator(login_required, name='dispatch')
class CreateCourseFromIncidentView(View):
    """
    Создание курса-инцидента из инцидента.
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        incident_id = kwargs.get('pk')
        try:
            incident = get_object_or_404(Incident, pk=incident_id)
            
            # Проверяем, не создан ли уже курс для этого инцидента
            if incident.course:
                return redirect('courses:course_detail', slug=incident.course.slug)
            
            # Создаем курс с названием инцидента
            course = Course.objects.create(
                title=incident.title,
                description='', # Не выводить описание инцидента в описание курса-инцидента
                author=request.user,
                is_incident=True,
                responsible_mentor=incident.responsible_mentor,
                mentors_time_to_check=incident.mentors_time_to_check or 2
            )
            
            # Связываем инцидент с курсом и обновляем статус
            incident.course = course
            incident.status = 'assigned'
            incident.save(update_fields=['course', 'status', 'updated_at'])

            if incident.course and not incident.status == 'assigned':
                incident.status = 'assigned'
                incident.save(update_fields=['course', 'status', 'updated_at'])
            
            # Автоназначение курса отключено - назначение происходит вручную через кнопки в деталке курса
            
            # Перенаправляем на страницу курса
            return redirect('courses:course_detail', slug=course.slug)
        except Exception as e:
            # В случае ошибки перенаправляем обратно на форму инцидента с сообщением об ошибке
            from django.contrib import messages
            import traceback
            messages.error(request, f'Ошибка при создании курса: {str(e)}')
            if incident_id:
                return redirect('builder:incident_edit', pk=incident_id)
            return redirect('builder:incidents')




class IncidentDetailListView(ListView):
    """
    Список по прогрессу пользователей по всем инцидентам
    """
    model = Incident
    template_name = 'builder/incident_detail.html'
    context_object_name = 'incidents'
    ordering = ['-created_at']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        from django.utils import timezone
        import datetime
        
        queryset = super().get_queryset()
        # Оптимизация: предзагрузка ManyToMany полей и связанных объектов
        queryset = queryset.prefetch_related('assigned_to', 'violators').select_related('user', 'responsible_mentor', 'expert', 'course')
        
        # Фильтр по названию инцидента (поиск)
        search = self.request.GET.get('search', '').strip()
        if search:
            queryset = queryset.filter(title__icontains=search)
        
        # Фильтр по дате создания
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        
        # Если нет параметров в GET запросе (первичная загрузка), устанавливаем дефолтные значения
        if not self.request.GET:
            # Устанавливаем период с начала 2025 года до сегодняшней даты
            date_from = '2025-01-01'
            date_to = timezone.now().date().strftime('%Y-%m-%d')
        
        if date_from:
            date_from_parsed = datetime.datetime.strptime(date_from, '%Y-%m-%d').date()
            date_from_datetime = timezone.make_aware(datetime.datetime.combine(date_from_parsed, datetime.time.min))
            queryset = queryset.filter(created_at__gte=date_from_datetime)
        if date_to:
            date_to_parsed = datetime.datetime.strptime(date_to, '%Y-%m-%d').date()
            date_to_datetime = timezone.make_aware(datetime.datetime.combine(date_to_parsed, datetime.time.max))
            queryset = queryset.filter(created_at__lte=date_to_datetime)
        
        return queryset

    def get_context_data(self, **kwargs):
        from django.utils import timezone
        from django.contrib.auth import get_user_model
        from myapp.models import QuizResult
        
        context = super().get_context_data(**kwargs)
        context['now'] = timezone.now()  # Текущая дата и время для проверки просроченных дедлайнов
        
        # Получаем список всех активных пользователей для фильтра
        User = get_user_model()
        context['users'] = User.objects.filter(is_active=True).order_by('last_name', 'first_name')
        
        # Параметры фильтров
        search = self.request.GET.get('search', '').strip()
        selected_user_id = self.request.GET.get('assigned_user', '')
        violator_filter = self.request.GET.get('violator_filter', 'all')  # 'all', 'yes', 'no'
        
        # Если нет параметров в GET запросе (первичная загрузка), устанавливаем дефолтные значения
        if not self.request.GET:
            context['date_from'] = '2025-01-01'
            context['date_to'] = timezone.now().date().strftime('%Y-%m-%d')
            context['search'] = ''
            context['selected_user_id'] = None
            context['violator_filter'] = 'all'
            context['violator_filter_locked'] = False
        else:
            date_from = self.request.GET.get('date_from', '')
            date_to = self.request.GET.get('date_to', '')
            
            # Если violator_filter=yes и даты не указаны, устанавливаем последние 30 дней
            if violator_filter == 'yes' and not date_from and not date_to:
                import datetime
                today = timezone.now().date()
                date_from = (today - datetime.timedelta(days=30)).strftime('%Y-%m-%d')
                date_to = today.strftime('%Y-%m-%d')
            
            context['date_from'] = date_from
            context['date_to'] = date_to
            context['search'] = search
            try:
                context['selected_user_id'] = int(selected_user_id) if selected_user_id else None
            except (ValueError, TypeError):
                context['selected_user_id'] = None
            context['violator_filter'] = violator_filter
            # Блокируем фильтр по нарушителям, если он установлен в 'yes' (переход с кнопки "Нарушители")
            context['violator_filter_locked'] = (violator_filter == 'yes')
        
        # Создаем список всех назначенных пользователей со всех инцидентов
        incident_user_list = []
        selected_user_id = context['selected_user_id']
        violator_filter = context['violator_filter']
        
        for incident in context['incidents']:
            assigned_users = incident.assigned_to.all()
            violators = incident.violators.all()
            
            for user in assigned_users:
                # Фильтр по назначенному пользователю
                if selected_user_id and user.id != selected_user_id:
                    continue
                
                is_violator = user in violators
                
                # Фильтр по нарушителям
                if violator_filter == 'yes' and not is_violator:
                    continue
                if violator_filter == 'no' and is_violator:
                    continue
                
                # Проверяем, назначен ли курс пользователю (если у инцидента есть курс)
                if incident.course:
                    # Если курс не назначен пользователю, пропускаем этого пользователя
                    if not UserCourse.objects.filter(user=user, course=incident.course).exists():
                        continue
                
                # Вычисляем прогресс курса, если он есть
                progress_percent = None
                course_deadline = None
                course_status = None
                user_course = None

                if incident.course:
                    course = incident.course
                    
                    # Получаем UserCourse для получения дедлайна
                    user_course = UserCourse.objects.filter(user=user, course=course).first()
                    if user_course:
                        course_deadline = user_course.deadline
                        course_status = user_course.status
                    
                    # Получаем траекторию пользователя для этого курса
                    trajectory = UserLessonTrajectory.objects.filter(user=user, course=course).first()
                    
                    if trajectory:
                        # Используем уроки из траектории
                        lessons = trajectory.lessons.all().order_by('order')
                        total_lessons = lessons.count()
                        lesson_ids = lessons.values_list('id', flat=True)
                        completed_lessons = UserProgress.objects.filter(
                            user=user,
                            course=course,
                            completed=True,
                            lesson_id__in=lesson_ids
                        ).count()
                    else:
                        # Используем все уроки курса
                        lessons = course.lessons.all().order_by('order')
                        total_lessons = lessons.count()
                        completed_lessons = UserProgress.objects.filter(
                            user=user,
                            course=course,
                            completed=True
                        ).count()
                    
                    # Подсчитываем завершенные тесты в рамках этого курса (только уникальные по quiz_title)
                    completed_quizzes = QuizResult.objects.filter(
                        user=user,
                        course=course,
                        quiz_title__in=[quiz.name for quiz in course.quizzes.all()],
                        passed=True
                    ).values('quiz_title').distinct().count()
                    total_quizzes = course.quizzes.count()
                    
                    # Вычисляем процент прогресса с учетом уроков и тестов
                    total_materials = total_lessons + total_quizzes
                    completed_materials = completed_lessons + completed_quizzes
                    progress_percent = int((completed_materials / total_materials) * 100) if total_materials > 0 else 0
                
                incident_user_list.append({
                    'incident': incident,
                    'user': user,
                    'is_violator': is_violator,
                    'is_expert': False,
                    'progress_percent': progress_percent,
                    'course_deadline': course_deadline,
                    'course_status': course_status,
                    'course_status_display': user_course.get_status_display() if user_course else None
                })
            
            # Добавляем expert, если он существует и не находится в assigned_to
            if incident.expert:
                expert = incident.expert
                # Проверяем, что expert не входит в assigned_to, чтобы не дублировать
                if expert not in assigned_users:
                    # Проверяем фильтры: если они не пропускают expert, добавляем его в список
                    should_add_expert = True
                    
                    # Фильтр по назначенному пользователю
                    if selected_user_id and expert.id != selected_user_id:
                        should_add_expert = False
                    
                    # Expert не является нарушителем (violator_filter не применяется к expert)
                    # Но если фильтр установлен на 'yes' (только нарушители), пропускаем expert
                    if violator_filter == 'yes':
                        should_add_expert = False
                    
                    # Проверяем, назначен ли курс expert (если у инцидента есть курс)
                    if incident.course:
                        # Если курс не назначен expert, пропускаем его
                        if not UserCourse.objects.filter(user=expert, course=incident.course).exists():
                            should_add_expert = False
                    
                    if should_add_expert:
                        # Вычисляем прогресс курса, если он есть
                        progress_percent = None
                        course_deadline = None
                        course_status = None
                        user_course = None
                        if incident.course:
                            course = incident.course
                            
                            # Получаем UserCourse для получения дедлайна
                            user_course = UserCourse.objects.filter(user=expert, course=course).first()
                            if user_course:
                                course_deadline = user_course.deadline
                                course_status = user_course.status
                            
                            # Получаем траекторию пользователя для этого курса
                            trajectory = UserLessonTrajectory.objects.filter(user=expert, course=course).first()
                            
                            if trajectory:
                                # Используем уроки из траектории
                                lessons = trajectory.lessons.all().order_by('order')
                                total_lessons = lessons.count()
                                lesson_ids = lessons.values_list('id', flat=True)
                                completed_lessons = UserProgress.objects.filter(
                                    user=expert,
                                    course=course,
                                    completed=True,
                                    lesson_id__in=lesson_ids
                                ).count()
                            else:
                                # Используем все уроки курса
                                lessons = course.lessons.all().order_by('order')
                                total_lessons = lessons.count()
                                completed_lessons = UserProgress.objects.filter(
                                    user=expert,
                                    course=course,
                                    completed=True
                                ).count()
                            
                            # Подсчитываем завершенные тесты в рамках этого курса (только уникальные по quiz_title)
                            completed_quizzes = QuizResult.objects.filter(
                                user=expert,
                                course=course,
                                quiz_title__in=[quiz.name for quiz in course.quizzes.all()],
                                passed=True
                            ).values('quiz_title').distinct().count()
                            total_quizzes = course.quizzes.count()
                            
                            # Вычисляем процент прогресса с учетом уроков и тестов
                            total_materials = total_lessons + total_quizzes
                            completed_materials = completed_lessons + completed_quizzes
                            progress_percent = int((completed_materials / total_materials) * 100) if total_materials > 0 else 0
                        
                        incident_user_list.append({
                            'incident': incident,
                            'user': expert,
                            'is_violator': False,  # Expert никогда не является нарушителем
                            'is_expert': True,  # Флаг, что это expert
                            'progress_percent': progress_percent,
                            'course_deadline': course_deadline,
                            'course_status': course_status,
                            'course_status_display': user_course.get_status_display() if user_course else None
                        })
        
        context['incident_user_list'] = incident_user_list
        return context
