from datetime import timezone
from django.contrib.auth.models import User
from django.db.models import Max
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DetailView, ListView, UpdateView, View

from builder.models import IPR, IPRModule, IPRModuleIndicator
from builder.audit_logger import AuditLoggerMixin, serialize_model_data
from builder.forms import IPRForm, IPRModuleForm



class IPRListView(ListView):
    """
    Список ИПР с информацией о пользователях и их курсах.
    """
    model = IPR
    template_name = 'builder/ipr_list.html'
    context_object_name = 'iprs'
    ordering = ['-created_at']

    def dispatch(self, request, *args, **kwargs):
        # Только staff/superuser
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('user', 'user__profile', 'user__profile__department')
        
        # Фильтр по статусу (множественный выбор)
        statuses = self.request.GET.getlist('status')
        if statuses:
            queryset = queryset.filter(status__in=statuses)
        else:
            # По умолчанию показываем только активные ИПР
            queryset = queryset.filter(status='active')
        
        # Фильтр по статусу пользователя (is_active)
        user_status = self.request.GET.get('user_status', 'active')
        if user_status == 'active':
            queryset = queryset.filter(user__is_active=True)
        elif user_status == 'inactive':
            queryset = queryset.filter(user__is_active=False)
        # Если user_status == 'all', фильтр не применяется
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = IPR.STATUS_CHOICES
        
        # Варианты фильтра по статусу пользователя
        context['user_status_choices'] = [
            ('all', 'Все'),
            ('active', 'Активные пользователи'),
            ('inactive', 'Неактивные пользователи'),
        ]
        
        # Если нет параметров в GET запросе (первичная загрузка), устанавливаем дефолтные значения
        if not self.request.GET:
            context['selected_statuses'] = ['active']
            context['selected_user_status'] = 'active'
        else:
            # Передаем текущие значения фильтров в контекст
            context['selected_statuses'] = self.request.GET.getlist('status', [])
            context['selected_user_status'] = self.request.GET.get('user_status', 'active')
        
        return context


class IPRCreateView(CreateView, AuditLoggerMixin):
    """
    Создание ИПР.
    """
    model = IPR
    form_class = IPRForm
    template_name = 'builder/ipr_form.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        """
        Возвращает URL для редиректа после успешного создания ИПР.
        Перенаправляет на страницу списка ИПР.
        """
        return reverse('builder:ipr_list')

    def form_valid(self, form):
        # Устанавливаем статус "Активен" для нового ИПР
        form.instance.status = 'active'
        response = super().form_valid(form)
        # Логируем создание ИПР
        self.log_create_action(self.object, "Создан новый ИПР")
        return response


class IPRUpdateView(UpdateView, AuditLoggerMixin):
    """
    Редактирование ИПР.
    """
    model = IPR
    form_class = IPRForm
    template_name = 'builder/ipr_form.html'
    success_url = reverse_lazy('builder:ipr_list')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        # Сохраняем старые значения для аудита
        self.old_values = serialize_model_data(self.object)
        response = super().form_valid(form)
        # Логируем обновление ИПР
        self.log_update_action(self.object, self.old_values, "Обновлен ИПР")
        return response


class IPRModuleListView(ListView):
    """
    Список модулей ИПР для конкретного пользователя.
    """
    model = IPRModule
    template_name = 'builder/ipr_module_list.html'
    context_object_name = 'modules'
    ordering = ['-created_at']

    def dispatch(self, request, *args, **kwargs):
        # Только staff/superuser
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        user_id = self.kwargs.get('user_id')
        queryset = super().get_queryset()
        queryset = queryset.select_related('user', 'user__profile', 'user__profile__department', 'mentor', 'ipr')
        
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_id = self.kwargs.get('user_id')
        
        if user_id:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                user = User.objects.get(id=user_id)
                context['selected_user'] = user
                context['selected_user_fio'] = user.get_full_name() or user.username
                # Получаем ИПР для этого пользователя
                ipr = IPR.objects.filter(user=user).first()
                if ipr:
                    context['ipr'] = ipr
            except User.DoesNotExist:
                pass
        
        return context


class IPRModuleCreateView(CreateView, AuditLoggerMixin):
    """
    Создание модуля ИПР.
    """
    model = IPRModule
    form_class = IPRModuleForm
    template_name = 'builder/ipr_module_form.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        user_id = self.kwargs.get('user_id')
        ipr_id = self.request.GET.get('ipr_id') or self.request.POST.get('ipr')
        
        if user_id:
            kwargs['user_id'] = user_id
        if ipr_id:
            kwargs['ipr_id'] = ipr_id
        
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_id = self.kwargs.get('user_id')
        
        if user_id:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                user = User.objects.get(id=user_id)
                context['selected_user'] = user
                context['selected_user_fio'] = user.get_full_name() or user.username
                # Получаем или создаем ИПР для этого пользователя
                ipr, created = IPR.objects.get_or_create(
                    user=user,
                    defaults={'status': 'active'}
                )
                context['ipr'] = ipr
                # Устанавливаем начальное значение для формы
                if 'form' in context:
                    if not context['form'].initial.get('ipr'):
                        context['form'].initial['ipr'] = ipr.id
            except User.DoesNotExist:
                pass
        
        return context

    def form_valid(self, form):
        user_id = self.kwargs.get('user_id')
        
        # Если передан user_id, убеждаемся, что ИПР существует
        if user_id:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                user = User.objects.get(id=user_id)
                ipr, created = IPR.objects.get_or_create(
                    user=user,
                    defaults={'status': 'active'}
                )
                form.instance.ipr = ipr
                form.instance.user = user
            except User.DoesNotExist:
                pass
        
        # Автоматически заполняем department из профиля пользователя
        if form.instance.user and hasattr(form.instance.user, 'profile') and form.instance.user.profile:
            form.instance.department = form.instance.user.profile.department
        
        # Устанавливаем статус "Новый" при создании
        form.instance.status = 'new'
        # start_date не устанавливаем - будет установлена при нажатии "Начать ИПР"
        form.instance.start_date = None
        
        response = super().form_valid(form)
        # Логируем создание модуля ИПР
        self.log_create_action(self.object, "Создан новый модуль ИПР")
        return response

    def get_success_url(self):
        user_id = self.kwargs.get('user_id')
        if user_id:
            return reverse('builder:ipr_module_list', kwargs={'user_id': user_id})
        return reverse('builder:ipr_list')


class IPRModuleUpdateView(UpdateView, AuditLoggerMixin):
    """
    Редактирование модуля ИПР.
    """
    model = IPRModule
    form_class = IPRModuleForm
    template_name = 'builder/ipr_module_form.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Получаем user_id из объекта модуля
        if self.object and self.object.user:
            kwargs['user_id'] = self.object.user.id
        if self.object and self.object.ipr:
            kwargs['ipr_id'] = self.object.ipr.id
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if self.object and self.object.user:
            context['selected_user'] = self.object.user
            context['selected_user_fio'] = self.object.user.get_full_name() or self.object.user.username
            if self.object.ipr:
                context['ipr'] = self.object.ipr
        
        return context

    def form_valid(self, form):
        # НЕ перезаписываем department из профиля - используем значение из формы
        # Если department не был выбран в форме, оставляем как есть
        
        # Сохраняем старые значения для аудита
        self.old_values = serialize_model_data(self.object)
        response = super().form_valid(form)
        # Логируем обновление модуля ИПР
        self.log_update_action(self.object, self.old_values, "Обновлен модуль ИПР")
        return response

    def get_success_url(self):
        if self.object and self.object.user:
            return reverse('builder:ipr_module_list', kwargs={'user_id': self.object.user.id})
        return reverse('builder:ipr_list')


class IPRModuleDetailView(DetailView):
    """
    Страница с информацией по модулю ИПР.
    """
    model = IPRModule
    template_name = 'builder/ipr_module_info.html'
    context_object_name = 'module'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """Обработка AJAX запроса для сохранения диагностики и целей"""
        self.object = self.get_object()
        
        if request.POST.get('action') == 'save_diagnostics':
            diagnostics = request.POST.get('diagnostics', '').strip()
            self.object.diagnostics = diagnostics
            self.object.save()
            
            return JsonResponse({
                'success': True,
                'diagnostics': diagnostics
            })
        
        if request.POST.get('action') == 'save_goals':
            goals = request.POST.get('goals', '').strip()
            self.object.goals = goals
            self.object.save()
            
            return JsonResponse({
                'success': True,
                'goals': goals
            })
        
        if request.POST.get('action') == 'save_comment':
            comment = request.POST.get('comment', '').strip()
            self.object.comment = comment
            self.object.save()
            
            return JsonResponse({
                'success': True,
                'comment': comment
            })
        
        if request.POST.get('action') == 'add_indicator':
            name = request.POST.get('name', '').strip()
            if not name:
                return JsonResponse({'success': False, 'error': 'Название показателя обязательно'})
            
            # Определяем порядок для нового показателя
            max_order = IPRModuleIndicator.objects.filter(module=self.object).aggregate(Max('order'))['order__max'] or 0
            
            indicator = IPRModuleIndicator.objects.create(
                module=self.object,
                name=name,
                order=max_order + 1
            )
            
            return JsonResponse({
                'success': True,
                'indicator': {
                    'id': indicator.id,
                    'name': indicator.name,
                    'point_a': indicator.point_a or '',
                    'intermediate_point': indicator.intermediate_point or '',
                    'stage_deadline': indicator.stage_deadline.strftime('%Y-%m-%dT%H:%M') if indicator.stage_deadline else '',
                    'point_b': indicator.point_b or '',
                    'fact': indicator.fact or '',
                    'deadline': indicator.deadline.strftime('%Y-%m-%dT%H:%M') if indicator.deadline else '',
                }
            })
        
        if request.POST.get('action') == 'update_indicator':
            indicator_id = request.POST.get('indicator_id')
            try:
                indicator = IPRModuleIndicator.objects.get(id=indicator_id, module=self.object)
            except IPRModuleIndicator.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Показатель не найден'})
            
            indicator.name = request.POST.get('name', '').strip()
            indicator.point_a = request.POST.get('point_a', '').strip() or None
            indicator.intermediate_point = request.POST.get('intermediate_point', '').strip() or None
            indicator.point_b = request.POST.get('point_b', '').strip() or None
            indicator.fact = request.POST.get('fact', '').strip() or None
            
            # Обработка дат
            stage_deadline_str = request.POST.get('stage_deadline', '').strip()
            if stage_deadline_str:
                try:
                    indicator.stage_deadline = timezone.datetime.strptime(stage_deadline_str, '%Y-%m-%dT%H:%M')
                    indicator.stage_deadline = timezone.make_aware(indicator.stage_deadline)
                except ValueError:
                    pass
            else:
                indicator.stage_deadline = None
            
            deadline_str = request.POST.get('deadline', '').strip()
            if deadline_str:
                try:
                    indicator.deadline = timezone.datetime.strptime(deadline_str, '%Y-%m-%dT%H:%M')
                    indicator.deadline = timezone.make_aware(indicator.deadline)
                except ValueError:
                    pass
            else:
                indicator.deadline = None
            
            indicator.save()
            
            return JsonResponse({
                'success': True,
                'indicator': {
                    'id': indicator.id,
                    'name': indicator.name,
                    'point_a': indicator.point_a or '',
                    'intermediate_point': indicator.intermediate_point or '',
                    'stage_deadline': indicator.stage_deadline.strftime('%Y-%m-%dT%H:%M') if indicator.stage_deadline else '',
                    'point_b': indicator.point_b or '',
                    'fact': indicator.fact or '',
                    'deadline': indicator.deadline.strftime('%Y-%m-%dT%H:%M') if indicator.deadline else '',
                }
            })
        
        if request.POST.get('action') == 'delete_indicator':
            indicator_id = request.POST.get('indicator_id')
            try:
                indicator = IPRModuleIndicator.objects.get(id=indicator_id, module=self.object)
                indicator.delete()
                return JsonResponse({'success': True})
            except IPRModuleIndicator.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Показатель не найден'})
        
        if request.POST.get('action') == 'update_module_fields':
            """Обновление полей модуля из таблицы"""
            try:
                # Обновляем руководителя
                supervisor_id = request.POST.get('supervisor', '').strip()
                if supervisor_id:
                    try:
                        supervisor = User.objects.get(id=supervisor_id, is_active=True)
                        self.object.supervisor = supervisor
                    except User.DoesNotExist:
                        pass
                elif supervisor_id == '':
                    self.object.supervisor = None
                
                # Обновляем зав отделением
                department_head_id = request.POST.get('department_head', '').strip()
                if department_head_id:
                    try:
                        department_head = User.objects.get(id=department_head_id, is_active=True)
                        self.object.department_head = department_head
                    except User.DoesNotExist:
                        pass
                elif department_head_id == '':
                    self.object.department_head = None
                
                # Обновляем наставника
                mentor_id = request.POST.get('mentor', '').strip()
                if mentor_id:
                    try:
                        mentor = User.objects.get(id=mentor_id, is_active=True, profile__is_mentor=True)
                        self.object.mentor = mentor
                    except User.DoesNotExist:
                        pass
                elif mentor_id == '':
                    self.object.mentor = None
                
                # Обновляем дату старта
                start_date_str = request.POST.get('start_date', '').strip()
                if start_date_str:
                    try:
                        start_date = timezone.datetime.strptime(start_date_str, '%Y-%m-%d').date()
                        self.object.start_date = start_date
                    except ValueError:
                        pass
                
                # Обновляем дедлайн
                deadline_str = request.POST.get('deadline', '').strip()
                if deadline_str:
                    try:
                        deadline_date = timezone.datetime.strptime(deadline_str, '%Y-%m-%d').date()
                        # Если у дедлайна уже есть время, сохраняем его, иначе устанавливаем 23:59:59
                        if self.object.deadline:
                            deadline = timezone.datetime.combine(deadline_date, self.object.deadline.time())
                        else:
                            deadline = timezone.datetime.combine(deadline_date, timezone.datetime.max.time().replace(microsecond=0))
                        deadline = timezone.make_aware(deadline)
                        self.object.deadline = deadline
                    except ValueError:
                        pass
                else:
                    self.object.deadline = None
                
                self.object.save()
                
                return JsonResponse({
                    'success': True,
                    'supervisor': {
                        'id': self.object.supervisor.id if self.object.supervisor else None,
                        'name': self.object.supervisor.get_full_name() if self.object.supervisor else None
                    },
                    'department_head': {
                        'id': self.object.department_head.id if self.object.department_head else None,
                        'name': self.object.department_head.get_full_name() if self.object.department_head else None
                    },
                    'mentor': {
                        'id': self.object.mentor.id if self.object.mentor else None,
                        'name': self.object.mentor.get_full_name() if self.object.mentor else None
                    },
                    'start_date': self.object.start_date.strftime('%Y-%m-%d') if self.object.start_date else '',
                    'deadline': self.object.deadline.strftime('%Y-%m-%d') if self.object.deadline else ''
                })
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})
        
        return JsonResponse({'success': False, 'error': 'Неизвестное действие'})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        module = self.object
        
        # Определяем статус модуля для кнопки "Начать ИПР"
        # Если статус 'new', значит модуль в статусе "Новый"
        is_new_status = module.status == 'new'
        context['is_new_status'] = is_new_status
        
        # Добавляем показатели модуля
        context['indicators'] = module.indicators.all()
        
        # Добавляем списки пользователей для редактирования
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Все активные пользователи для руководителя и зав отделением
        context['all_users'] = User.objects.filter(is_active=True).order_by('last_name', 'first_name')
        
        # Только наставники для поля наставник
        context['mentors'] = User.objects.filter(
            profile__is_mentor=True,
            is_active=True
        ).order_by('last_name', 'first_name')
        
        return context


@method_decorator(require_POST, name='dispatch')
class IPRModuleStartView(View, AuditLoggerMixin):
    """
    Изменение статуса модуля ИПР с "Новый" на "Активный".
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        from django.utils import timezone
        
        module = get_object_or_404(IPRModule, pk=kwargs['pk'])
        
        # Меняем статус с "нового" на "Активный" и устанавливаем дату старта
        if module.status == 'new':
            module.status = 'active'  # Статус "Активный"
            module.start_date = timezone.now().date()  # Устанавливаем текущую дату
            module.save()
            
            # Логируем изменение статуса
            self.log_update_action(module, {}, f"Модуль ИПР переведен в статус 'Активный'. Дата старта: {module.start_date}")
        
        return redirect('builder:ipr_module_info', pk=module.pk)


@method_decorator(require_POST, name='dispatch')
class IPRModuleCompleteView(View, AuditLoggerMixin):
    """
    Изменение статуса модуля ИПР с "Активный" на "Завершен".
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        from django.utils import timezone
        
        module = get_object_or_404(IPRModule, pk=kwargs['pk'])
        
        # Меняем статус с "Активный" на "Завершен" и устанавливаем дату окончания
        if module.status == 'active':
            module.status = 'completed'  # Статус "Завершен"
            module.end_date = timezone.now().date()  # Устанавливаем текущую дату
            module.save()
            
            # Логируем изменение статуса
            self.log_update_action(module, {}, f"Модуль ИПР переведен в статус 'Завершен'. Дата окончания: {module.end_date}")
        
        return redirect('builder:ipr_module_info', pk=module.pk)


@method_decorator(require_POST, name='dispatch')
class IPRModulePauseView(View, AuditLoggerMixin):
    """
    Изменение статуса модуля ИПР с "Активный" на "Приостановлен".
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        from django.utils import timezone
        
        module = get_object_or_404(IPRModule, pk=kwargs['pk'])
        
        # Меняем статус с "Активный" на "Приостановлен"
        if module.status == 'active':
            module.status = 'paused'  # Статус "Приостановлен"
            module.save()
            
            # Логируем изменение статуса
            self.log_update_action(module, {}, f"Модуль ИПР переведен в статус 'Приостановлен'")
        
        return redirect('builder:ipr_module_info', pk=module.pk)


@method_decorator(require_POST, name='dispatch')
class IPRModuleResumeView(View, AuditLoggerMixin):
    """
    Изменение статуса модуля ИПР с "Приостановлен" на "Активный".
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        from django.utils import timezone
        
        module = get_object_or_404(IPRModule, pk=kwargs['pk'])
        
        # Меняем статус с "Приостановлен" на "Активный"
        if module.status == 'paused':
            module.status = 'active'  # Статус "Активный"
            module.save()
            
            # Логируем изменение статуса
            self.log_update_action(module, {}, f"Модуль ИПР переведен в статус 'Активный' (возобновлен)")
        
        return redirect('builder:ipr_module_info', pk=module.pk)
