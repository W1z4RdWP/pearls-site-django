from datetime import datetime
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.db.models import Count, Q, F
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, ListView, UpdateView, View
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.chart import PieChart, BarChart, Reference
from openpyxl.chart.label import DataLabelList
from weasyprint.css.validation.properties import word_break

from builder.audit_logger import AuditLoggerMixin, serialize_model_data
from builder.forms import IncidentForm
from builder.models import Incident
from builder.utils import get_total_incidents_students
from courses.models import Course, UserLessonTrajectory
from myapp.models import UserCourse, UserProgress

import logging

logger = logging.getLogger(__name__)
audit_logger = logging.getLogger('audit')



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
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser or request.user.profile.is_mentor_user):
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        from django.utils import timezone
        import datetime
        
        queryset = super().get_queryset()

        # pyright: reportUnreachable=false
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
        readonly = False
        is_mentor = self.request.user.profile.is_mentor_user
        if is_mentor:
            readonly = True
        context['readonly'] = readonly
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


def _apply_header_style(ws, row_num, col_count):
    """Применяет стили к заголовкам таблицы."""
    for col_num in range(1, col_count + 1):
        cell = ws.cell(row=row_num, column=col_num)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        cell.alignment = Alignment(horizontal='center')


def _set_column_widths(ws, widths):
    """Устанавливает ширину колонок."""
    for col_num, width in enumerate(widths, 1):
        col_letter = get_column_letter(col_num)
        ws.column_dimensions[col_letter].width = width


def _insert_rows(ws, rows):
    """Устанавливает пустые строки"""
    
    return ws.append([])
            
        


@login_required
def incidents_export_excel_report(request):
    if not (request.user.is_staff or request.user.is_superuser):
        return HttpResponse("Доступ запрещен", status=403)

    incidents = Incident.objects.all()
    wb = Workbook()
    
    # ================== ЛИСТ 1: Общая сводка ==================
    ws_summary = wb.active
    ws_summary.title = "Общая сводка"
    
    # Подсчёт данных
    total_incidents = incidents.count()
    info_incidents_count = incidents.filter(incident_type='informational').count()
    edu_incidents_count = incidents.filter(incident_type='educational').count()
    
    # Всего назначений (assigned_to + violators)
    total_assignments = get_total_incidents_students(incidents)
    
    # Уникальные назначения (каждый пользователь считается 1 раз)
    unique_assigned_users = set()
    for incident in incidents:
        unique_assigned_users.update(incident.assigned_to.values_list('id', flat=True))
        unique_assigned_users.update(incident.violators.values_list('id', flat=True))
    total_unique_assignments = len(unique_assigned_users)
    
    # Завершённые обучения по курсам-инцидентам
    incident_courses = Course.objects.filter(is_incident=True)
    total_completed = UserCourse.objects.filter(
        course__in=incident_courses,
        status='completed'
    ).count()
    
    # Статусы инцидентов
    status_counts = {
        'new': incidents.filter(status='new').count(),
        'accepted': incidents.filter(status='accepted').count(),
        'assigned': incidents.filter(status='assigned').count(),
        'studies_completed': incidents.filter(status='studies_completed').count(),
        'resolved': incidents.filter(status='resolved').count(),
        'declined': incidents.filter(status='declined').count(),
    }
    
    # Заголовки и данные для общей сводки
    summary_headers = [
        "Всего инцидентов", "Информационных", "Обучающих",
        "Всего назначений", "Уникальных назначений", "Завершено обучений"
    ]
    ws_summary.append(summary_headers)
    _apply_header_style(ws_summary, 1, len(summary_headers))
    _set_column_widths(ws_summary, [50, 30, 30, 20, 22, 22])
    
    ws_summary.append([
        total_incidents, info_incidents_count, edu_incidents_count,
        total_assignments, total_unique_assignments, total_completed
    ])
    
    # Отступ и статусы инцидентов
    ws_summary.append([])
    ws_summary.append(["Статусы инцидентов"])
    ws_summary.cell(row=4, column=1).font = Font(bold=True)
    
    status_headers = ["Новый", "Принят", "Назначен", "Обучение завершено", "Завершён", "Отклонён"]
    ws_summary.append(status_headers)
    _apply_header_style(ws_summary, 5, len(status_headers))
    
    ws_summary.append([
        status_counts['new'], status_counts['accepted'], status_counts['assigned'],
        status_counts['studies_completed'], status_counts['resolved'], status_counts['declined']
    ])

    # Группы и инциденты для блоков «Просрочены дедлайны» и «По подразделениям»
    groups_involved = list(
        Group.objects.filter(user__id__in=unique_assigned_users)
        .values_list('name', flat=True)
        .distinct()
    )
    incidents_prefetched = incidents.prefetch_related('assigned_to', 'violators')

    # Просрочены дедлайны по подразделениям: считаем по UserCourse.deadline (срок курса у пользователя), не по Incident.deadline
    from django.utils import timezone
    now = timezone.now()
    incidents_with_course = [inc for inc in incidents_prefetched if inc.course_id is not None]
    # По группе: (group_name, set(user_ids) просрочивших, set(incident_ids) просроченных для группы)
    overdue_by_group = {}
    for group_name in groups_involved:
        group_user_ids = set(
            User.objects.filter(groups__name=group_name)
            .filter(id__in=unique_assigned_users)
            .values_list('id', flat=True)
        )
        overdue_user_ids = set()
        overdue_incident_ids = set()
        for inc in incidents_with_course:
            assigned_ids = set(inc.assigned_to.values_list('id', flat=True))
            violator_ids = set(inc.violators.values_list('id', flat=True))
            in_group = (assigned_ids | violator_ids) & group_user_ids
            if not in_group:
                continue
            # Просрочили: у пользователя есть UserCourse по курсу инцидента с дедлайном < now и статус не 'completed'
            overdue_user_ids_for_inc = set(
                UserCourse.objects.filter(
                    user_id__in=in_group,
                    course_id=inc.course_id,
                    deadline__isnull=False,
                    deadline__lt=now,
                ).exclude(status='completed').values_list('user_id', flat=True)
            )
            if overdue_user_ids_for_inc:
                overdue_incident_ids.add(inc.id)
                overdue_user_ids |= overdue_user_ids_for_inc
        overdue_by_group[group_name] = (len(overdue_user_ids), len(overdue_incident_ids))
    # Сортируем группы по количеству просроченных инцидентов (убывание)
    overdue_rows = [
        [group_name, num_employees, num_incidents]
        for group_name, (num_employees, num_incidents) in sorted(
            overdue_by_group.items(), key=lambda x: -x[1][1]
        )
    ]

    ws_summary.append([])
    ws_summary.append(['Просрочены дедлайны в подразделении', 'Количество сотрудников', 'Количество инцидентов'])
    _apply_header_style(ws_summary, ws_summary.max_row, 3)
    for row in overdue_rows:
        ws_summary.append(row)
    ws_summary.append([])
    ws_summary.append([])
    ws_summary.append(['По подразделениям'])
    _apply_header_style(ws_summary, ws_summary.max_row, 1)

    groups_headers = ["Подразделение", "Всего", "Обучающие", "Информационные", "Завершены", "Не завершены", "Повторяющиеся"]
    ws_summary.append(groups_headers)
    _apply_header_style(ws_summary, ws_summary.max_row, 8)

    start_row = ws_summary.max_row + 1
    for idx, group_name in enumerate(groups_involved):
        group_user_ids = set(
            User.objects.filter(groups__name=group_name)
            .filter(id__in=unique_assigned_users)
            .values_list('id', flat=True)
        )
        if not group_user_ids:
            ws_summary.append([group_name, 0, 0, 0, 0, 0, "Не выявлено"])
            row_num = start_row + idx
            for col in range(1,8):
                ws_summary.cell(row=row_num, column=col).alignment = Alignment(wrap_text=True)
            continue

        group_total = 0
        group_edu = 0
        group_info = 0
        titles_list = []

        for inc in incidents_prefetched:
            assigned_ids = set(inc.assigned_to.values_list('id', flat=True))
            violator_ids = set(inc.violators.values_list('id', flat=True))
            in_group = (assigned_ids | violator_ids) & group_user_ids
            n = len(in_group)
            if n == 0:
                continue
            group_total += n
            if inc.incident_type == 'educational':
                group_edu += n
            else:
                group_info += n
            titles_list.append(inc.title)

        completed = UserCourse.objects.filter(
            user_id__in=group_user_ids,
            course__in=incident_courses,
            status='completed'
        ).count()
        not_completed = max(0, group_total - completed)
        
        has_duplicate_titles = len(titles_list) != len(set(titles_list))
        repeat_value = "Выявлено" if has_duplicate_titles else "Не выявлено"

        ws_summary.append([
            group_name,
            group_total,
            group_edu,
            group_info,
            completed,
            not_completed,
            repeat_value,
        ])


    # ================== ЛИСТ 2: Диаграммы ==================
    ws_charts = wb.create_sheet("Диаграммы")
    
    # --- Данные для круговой диаграммы: Типы инцидентов ---
    ws_charts.append(["Тип инцидента", "Количество"])
    ws_charts.append(["Информационные", info_incidents_count])
    ws_charts.append(["Обучающие", edu_incidents_count])
    
    # Круговая диаграмма: Типы инцидентов
    pie_chart = PieChart()
    pie_chart.title = "Типы инцидентов"
    labels = Reference(ws_charts, min_col=1, min_row=2, max_row=3)
    data = Reference(ws_charts, min_col=2, min_row=1, max_row=3)
    pie_chart.add_data(data, titles_from_data=True)
    pie_chart.set_categories(labels)
    pie_chart.dataLabels = DataLabelList()
    pie_chart.dataLabels.showPercent = True
    pie_chart.dataLabels.showVal = True
    pie_chart.dataLabels.showCatName = False
    pie_chart.width = 12
    pie_chart.height = 8
    ws_charts.add_chart(pie_chart, "D2")
    
    # --- Данные для столбчатой диаграммы: Статусы инцидентов ---
    ws_charts.append([])  # Пустая строка
    ws_charts.append(["Статус", "Количество"])
    status_data_start_row = 6
    ws_charts.append(["Новый", status_counts['new']])
    ws_charts.append(["Принят", status_counts['accepted']])
    ws_charts.append(["Назначен", status_counts['assigned']])
    ws_charts.append(["Обучение завершено", status_counts['studies_completed']])
    ws_charts.append(["Завершён", status_counts['resolved']])
    ws_charts.append(["Отклонён", status_counts['declined']])
    
    # Столбчатая диаграмма: Статусы инцидентов
    bar_chart = BarChart()
    bar_chart.title = "Статусы инцидентов"
    bar_chart.type = "col"
    bar_chart.style = 10
    bar_chart.y_axis.title = "Количество"
    bar_chart.x_axis.title = "Статус"
    
    bar_labels = Reference(ws_charts, min_col=1, min_row=status_data_start_row, max_row=status_data_start_row + 5)
    bar_data = Reference(ws_charts, min_col=2, min_row=status_data_start_row - 1, max_row=status_data_start_row + 5)
    bar_chart.add_data(bar_data, titles_from_data=True)
    bar_chart.set_categories(bar_labels)
    bar_chart.shape = 4
    bar_chart.width = 16
    bar_chart.height = 10
    ws_charts.add_chart(bar_chart, "D14")
    
    # --- Данные для диаграммы: Назначения и завершения ---
    ws_charts.append([])
    ws_charts.append(["Метрика", "Значение"])
    metrics_start_row = 14
    ws_charts.append(["Всего назначений", total_assignments])
    ws_charts.append(["Уникальных назначений", total_unique_assignments])
    ws_charts.append(["Завершено обучений", total_completed])
    
    # Столбчатая диаграмма: Назначения
    bar_chart2 = BarChart()
    bar_chart2.title = "Назначения и завершения"
    bar_chart2.type = "col"
    bar_chart2.style = 12
    bar_chart2.y_axis.title = "Количество"
    
    bar2_labels = Reference(ws_charts, min_col=1, min_row=metrics_start_row, max_row=metrics_start_row + 2)
    bar2_data = Reference(ws_charts, min_col=2, min_row=metrics_start_row - 1, max_row=metrics_start_row + 2)
    bar_chart2.add_data(bar2_data, titles_from_data=True)
    bar_chart2.set_categories(bar2_labels)
    bar_chart2.width = 12
    bar_chart2.height = 8
    ws_charts.add_chart(bar_chart2, "D28")
    
    # Устанавливаем ширину колонок для данных
    _set_column_widths(ws_charts, [25, 15])
    
    # ================== ЛИСТ 3: Группировка по названию ==================
    ws_by_title = wb.create_sheet("По названиям")
    
    # Группируем инциденты по названию
    incidents_by_title = incidents.values('title').annotate(
        count=Count('id'),
        info_count=Count('id', filter=Q(incident_type='informational')),
        edu_count=Count('id', filter=Q(incident_type='educational'))
    ).order_by('-count')
    
    title_headers = ["Название инцидента", "Всего", "Информационных", "Обучающих"]
    ws_by_title.append(title_headers)
    _apply_header_style(ws_by_title, 1, len(title_headers))
    _set_column_widths(ws_by_title, [50, 12, 18, 15])
    
    for item in incidents_by_title:
        ws_by_title.append([
            item['title'], item['count'], item['info_count'], item['edu_count']
        ])
    
    # ================== ЛИСТ 4: Кто зафиксировал ==================
    ws_by_user = wb.create_sheet("Кто зафиксировал")
    
    # Группируем по пользователю, который создал инцидент
    incidents_by_user = incidents.values(
        'user__id', 'user__username', 'user__first_name', 'user__last_name'
    ).annotate(count=Count('id')).order_by('-count')
    
    user_headers = ["Пользователь", "Количество инцидентов"]
    ws_by_user.append(user_headers)
    _apply_header_style(ws_by_user, 1, len(user_headers))
    _set_column_widths(ws_by_user, [40, 25])
    
    for item in incidents_by_user:
        # Формируем имя пользователя
        full_name = f"{item['user__last_name'] or ''} {item['user__first_name'] or ''}".strip()
        display_name = full_name if full_name else item['user__username']
        ws_by_user.append([display_name, item['count']])
    
    # ================== ЛИСТ 5: Детализация по инцидентам ==================
    ws_details = wb.create_sheet("Детализация")
    
    details_headers = [
        "ID", "Название", "Тип", "Статус", "Зафиксировал",
        "Назначено (чел.)", "Нарушителей", "Курс-инцидент", "Дата создания"
    ]
    ws_details.append(details_headers)
    _apply_header_style(ws_details, 1, len(details_headers))
    _set_column_widths(ws_details, [8, 40, 18, 22, 30, 18, 15, 35, 20])
    
    for incident in incidents.select_related('user', 'course').prefetch_related('assigned_to', 'violators'):
        # Имя зафиксировавшего
        user = incident.user
        user_full_name = f"{user.last_name or ''} {user.first_name or ''}".strip()
        user_display = user_full_name if user_full_name else user.username
        
        # Тип и статус
        incident_type_display = "Информационный" if incident.incident_type == 'informational' else "Обучающий"
        status_display = dict(Incident.STATUS_CHOICES).get(incident.status, incident.status)
        
        ws_details.append([
            incident.id,
            incident.title,
            incident_type_display,
            status_display,
            user_display,
            incident.assigned_to.count(),
            incident.violators.count(),
            incident.course.title if incident.course else "—",
            incident.created_at.strftime('%Y-%m-%d %H:%M') if incident.created_at else "—"
        ])
    
    # Сохраняем файл
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    filename = f"incidents_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    response['Content-Disposition'] = f'attachment; filename={filename}'
    wb.save(response)
    
    audit_logger.info(
        f'Экспортировал отчет по инцидентам в Excel', 
        extra={
            'user': request.user.email if request.user.is_authenticated else 'Anonymous',
            'target_user': request.user.email
        }
    )
    return response



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
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser or request.user.profile.is_mentor_user):
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
        
        # Фильтр по статусу UserCourse
        status_choices = UserCourse.STATUS_CHOICES
        context['status_choices'] = status_choices
        
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
            # Статусы, выбранные в фильтре (чекбоксы)
            context['selected_statuses'] = self.request.GET.getlist('status', [])
            
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
        selected_statuses = context.get('selected_statuses', [])
        
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
                
                # Проверяем, назначен ли курс пользователю и подходит ли по статусу (если у инцидента есть курс)
                if incident.course:
                    user_course_qs = UserCourse.objects.filter(user=user, course=incident.course)
                    # Если выбраны статусы, ограничиваем ими
                    if selected_statuses:
                        user_course_qs = user_course_qs.filter(status__in=selected_statuses)
                    # Если подходящего UserCourse нет, пропускаем пользователя
                    if not user_course_qs.exists():
                        continue
                
                # Вычисляем прогресс курса, если он есть
                progress_percent = None
                course_deadline = None
                course_status = None
                user_course = None

                if incident.course:
                    course = incident.course
                    
                    # Получаем UserCourse для получения дедлайна (с учетом уже примененного фильтра по статусу выше)
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
                    
                    # Проверяем, назначен ли курс expert и подходит ли по статусу (если у инцидента есть курс)
                    if incident.course:
                        expert_course_qs = UserCourse.objects.filter(user=expert, course=incident.course)
                        if selected_statuses:
                            expert_course_qs = expert_course_qs.filter(status__in=selected_statuses)
                        # Если курс не назначен expert или статус не входит в выбранные, пропускаем его
                        if not expert_course_qs.exists():
                            should_add_expert = False
                    
                    if should_add_expert:
                        # Вычисляем прогресс курса, если он есть
                        progress_percent = None
                        course_deadline = None
                        course_status = None
                        user_course = None
                        if incident.course:
                            course = incident.course
                            
                            # Получаем UserCourse для получения дедлайна (с учетом уже примененного фильтра по статусу выше)
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


@method_decorator(login_required, name='dispatch')
class UnassignIncidentUserView(View, AuditLoggerMixin):
    """
    Отмена назначения пользователя на инцидент.
    Удаляет пользователя из поля assigned_to инцидента.
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser or request.user.profile.is_mentor_user):
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        from django.contrib.auth import get_user_model
        from django.contrib import messages
        
        User = get_user_model()
        incident_id = kwargs.get('incident_id')
        user_id = kwargs.get('user_id')
        
        incident = get_object_or_404(Incident, pk=incident_id)
        user = get_object_or_404(User, pk=user_id)
        
        # Проверяем, что пользователь действительно назначен на инцидент
        if user not in incident.assigned_to.all():
            messages.error(request, f'Пользователь {user.get_full_name() or user.username} не назначен на инцидент "{incident.title}"')
            return redirect('builder:incident_detail')
        
        # Сохраняем старые значения для аудита
        old_values = serialize_model_data(incident)
        
        # Удаляем пользователя из assigned_to
        # Сигнал автоматически удалит доступ к курсу, если он есть
        incident.assigned_to.remove(user)
        
        # Логируем действие
        comment = f"Отменено назначение пользователя {user.get_full_name() or user.username} на инцидент"
        self.log_update_action(incident, old_values, comment)
        
        messages.success(request, f'Назначение пользователя {user.get_full_name() or user.username} на инцидент "{incident.title}" отменено')
        
        # Перенаправляем обратно на страницу деталей с сохранением фильтров
        redirect_url = reverse('builder:incident_detail')
        # Получаем параметры фильтров из POST (они передаются как скрытые поля формы)
        # или из GET (если они есть)
        from urllib.parse import urlencode
        query_params = []
        for key in ['search', 'date_from', 'date_to', 'assigned_user', 'violator_filter']:
            value = request.POST.get(key) or request.GET.get(key)
            if value:
                query_params.append((key, value))
        
        if query_params:
            redirect_url += '?' + urlencode(query_params)
        
        return redirect(redirect_url)
