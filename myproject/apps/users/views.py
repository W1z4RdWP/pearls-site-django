from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from weasyprint import HTML
from django.template.loader import render_to_string
from datetime import datetime

from collections import defaultdict
import logging


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.contrib.auth import login as auth_login
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.views.generic import FormView, ListView
from django.views.decorators.cache import cache_page
from django.urls import reverse, reverse_lazy
from django.utils.encoding import smart_str
from django.contrib.auth.models import Group
from django.db.models import Q, Avg, Count, Sum
from django.utils.http import urlencode


from myapp.models import UserCourse, UserProgress, QuizResult, UserAnswer
from quizzes.models import Answer
from courses.models import UserLessonTrajectory, Course
from gamification.models import Badge, Achievement, DascoinTransaction
from .forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm
from .models import Profile, Role
 
# Получаем логгер для записи в журнал аудита
audit_logger = logging.getLogger('audit')


class RegisterView(LoginRequiredMixin, FormView):
    form_class = UserRegisterForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        user = form.save()
        # Логирование действия
        audit_logger.info(
            'Зарегистрировался на платформе', 
            extra={
                'user': user.email if user.is_authenticated else 'Anonymous'
            }
        )
                
        form.save()
        return super().form_valid(form)



@login_required
def profile(request: HttpRequest) -> HttpResponse:
    """
    Отображает страницу профиля пользователя, а также его прогресс
    по начатым курсам.

    Args:
        request (HttpRequest): Объект запроса.

    Returns:
        HttpResponse: Ответ с отрендеренным шаблоном профиля.
        Шаблон включает формы для редактирования профиля и список курсов с прогрессом.
    """
    user = request.user
    try:
        profile = user.profile
    except Profile.DoesNotExist:
        return render(request, 'users/profile_error.html', {
            'error_message': 'Профиль пользователя не найден. Пожалуйста, обратитесь к администратору.'
        })
    # Получаем все доступные курсы через менеджер
    available_courses = Course.objects.available_for_user(user)
    # Получаем UserCourse для каждого доступного курса
    started_courses = []
    for course in available_courses:
        user_course = UserCourse.objects.filter(user=user, course=course).first()
        if user_course:
            started_courses.append(user_course)
        else:
            # Создаем UserCourse если его нет (для курсов из траекторий)
            user_course = UserCourse.objects.create(user=user, course=course, status='available')
            started_courses.append(user_course)
    unfinished_courses = []
    finished_courses = []
    quiz_results = QuizResult.objects.filter(user=request.user).order_by('-completed_at')
    # Пагинация для истории тестов
    paginator = Paginator(quiz_results, 4)  # 4 элементов на странице
    page_number = request.GET.get('page', 1)

    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

        # Проверка на AJAX-запрос
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # Логирование действия
        audit_logger.info(
                    'Смотрит истории своих тестов в профиле', 
        extra={
            'user': request.user.email if request.user.is_authenticated else 'Anonymous'
        }
        )
        return render(request, 'users/includes/_quiz_history.html', {'page_obj': page_obj})

    all_lessons_completed = False
    percent = 0 

    for user_course in started_courses:
        course = user_course.course
        completed = UserProgress.objects.filter(
            user=user,
            course=course,
            completed=True
        ).count()

        trajectory = UserLessonTrajectory.objects.filter(user=request.user, course=course).first()
        total = trajectory.lessons.count() if trajectory else course.lessons.count()
        percent = int((completed / total) * 100) if total > 0 else 0

        course_data = {
            'course': course,
            'completed': completed,
            'total': total,
            'percent': percent,
            'status': user_course.status
        }

        if course.final_quiz:
            quiz_passed = QuizResult.objects.filter(
                user=request.user,
                quiz_title=course.final_quiz,
                passed=True
            ).exists()
            course_data['quiz_passed'] = quiz_passed

        if percent == 100:
            finished_courses.append(course_data)
        else:
            unfinished_courses.append(course_data)

        # Обновляем флаг завершения всех уроков
        all_lessons_completed = (percent == 100) or all_lessons_completed

    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect('users:profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=profile)


    # Логирование действия
    audit_logger.info(
        'Перешёл в свой профиль', 
        extra={
            'user': request.user.email if request.user.is_authenticated else 'Anonymous'
        }
    )

    return render(request, 'users/profile.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'unfinished_courses': unfinished_courses,
        'finished_courses': finished_courses,
        'quiz_results': quiz_results,
        'page_obj': page_obj,
        'all_lessons_completed': all_lessons_completed,
        'dascoin_points': profile.dascoin_points,
        'recent_badges': profile.get_recent_badges(),
        'recent_achievements': profile.get_recent_achievements(),
        'total_badges': profile.get_badges().count(),
        'total_achievements': profile.get_achievements().count(),
    })


@login_required
def all_badges(request: HttpRequest) -> HttpResponse:
    """Отображает все бейджи пользователя"""
    user = request.user
    profile = user.profile
    
    user_badges = profile.get_badges()
    total_badges = user_badges.count()
    all_badges_count = Badge.objects.filter(is_active=True).count()
    progress_percent = int((total_badges / all_badges_count * 100)) if all_badges_count > 0 else 0
    
    context = {
        'user_badges': user_badges,
        'total_badges': all_badges_count,
        'progress_percent': progress_percent,
    }
    
    return render(request, 'users/includes/_all_badges.html', context)


@login_required
def all_achievements(request: HttpRequest) -> HttpResponse:
    """Отображает все достижения пользователя"""
    user = request.user
    profile = user.profile
    
    user_achievements = profile.get_achievements()
    
    context = {
        'user_achievements': user_achievements,
    }
    
    return render(request, 'users/includes/_all_achievements.html', context)


@login_required
def quiz_report(request, quiz_id):
    quiz_result = get_object_or_404(QuizResult, id=quiz_id, user=request.user)
    answers = quiz_result.answers.select_related('question', 'selected_answer').order_by('question__id').all()

    # Создаем словарь, где ключ - вопрос, значение - список выбранных ответов
    multiple_choice_answers = {}

    for answer in answers:
        if answer.question.question_type == 'multiple':
            # Если вопрос еще не в словаре, добавляем с пустым списком
            if answer.question not in multiple_choice_answers:
                multiple_choice_answers[answer.question] = []
            # Добавляем выбранный ответ (если он есть)
            if answer.selected_answer:
                multiple_choice_answers[answer.question].append(answer.selected_answer)

    context = {
        'quiz_result': quiz_result,
        'answers': answers,
        'multiple_choice_answers': multiple_choice_answers,
    }
    return render(request, 'users/includes/_quiz_report.html', context)


class CustomLoginView(LoginView):
    """
    Кастомный класс расширяющий функционал встроенной в Django функции авторизации.
    Если пользователь зарегистрирован, но администратор сайта не поставил ему в админ панеле галочку - подтверждение,
    то пользователю, при попытке входа, будет выводится сообщение "Ваш аккаунт ожидает подтверждения администратором."
    """
    template_name = "users/login.html"
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Заменяем label для поля username на email
        form.fields['username'].label = 'Email'
        form.fields['username'].help_text = 'Введите ваш email'
        return form

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('users:profile')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.get_user()
        try:
            profile = user.profile
        except Profile.DoesNotExist:
            return render(self.request, 'users/profile_error.html', {
                'error_message': 'Профиль пользователя не найден. Пожалуйста, обратитесь к администратору.'
            })
        if not profile.is_approved:
            # Логирование действия
            audit_logger.info(
                'Хочет авторизоваться, но профиль не подтверждён', 
                extra={
                    'user': user.email if user.is_authenticated else 'Anonymous'
                }
            )
            messages.error(self.request, "Ваш аккаунт ожидает подтверждения администратором.")
            return redirect('users:login')
        audit_logger.info(
            'Вошёл в систему', 
            extra={
                'user': user.email if user.is_authenticated else 'Anonymous'
            }
        )
        auth_login(self.request, user)
        return redirect(self.get_success_url())


class TransactionsListView(LoginRequiredMixin, ListView):
    """CBV для отображения истории транзакций DASCOIN пользователя"""
    model = DascoinTransaction
    template_name = 'users/transactions.html'
    context_object_name = 'transactions'
    paginate_by = 20
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Возвращает транзакции только для текущего пользователя с возможностью фильтрации"""
        queryset = DascoinTransaction.objects.filter(user=self.request.user).order_by('-created_at')
        
        # Фильтрация по типу транзакции
        transaction_type = self.request.GET.get('type')
        if transaction_type and transaction_type in ['award', 'deduct', 'set', 'correction']:
            queryset = queryset.filter(transaction_type=transaction_type)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        """Добавляет дополнительный контекст"""
        context = super().get_context_data(**kwargs)
        
        context['total_transactions'] = self.get_queryset().count()
        context['current_filter'] = self.request.GET.get('type', '')
        
        # Статистика по типам транзакций
        all_transactions = DascoinTransaction.objects.filter(user=self.request.user)
        context['stats'] = {
            'award': all_transactions.filter(transaction_type='award').count(),
            'deduct': all_transactions.filter(transaction_type='deduct').count(),
            'set': all_transactions.filter(transaction_type='set').count(),
            'correction': all_transactions.filter(transaction_type='correction').count(),
        }
        
        # Безопасный back_url
        referer = self.request.META.get('HTTP_REFERER', '')
        current_host = self.request.get_host()
        if referer and current_host in referer:
            context['back_url'] = referer
        else:
            context['back_url'] = reverse('users:profile')
        # Логирование действия
        audit_logger.info(
            'Смотрит историю транзакций DASCOIN', 
            extra={
                'user': self.request.user.email if self.request.user.is_authenticated else 'Anonymous'
            }
        )
        
        return context


@login_required
def export_transactions_excel(request):
    transactions = DascoinTransaction.objects.filter(user=request.user).order_by('-created_at')
    wb = Workbook()
    ws = wb.active
    ws.title = "Транзакции DASCOIN"
    headers = ['Дата', 'Тип', 'Изменение', 'До', 'После', 'Причина', 'Администратор']
    ws.append(headers)
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    for tx in transactions:
        ws.append([
            tx.created_at.strftime("%d.%m.%Y %H:%M"),
            tx.get_transaction_type_display(),
            tx.points_change,
            tx.points_before,
            tx.points_after,
            tx.reason or "Не указана",
            tx.admin_user.get_full_name() if tx.admin_user else "Система"
        ])
    for column in ws.columns:
        max_length = max(len(str(cell.value)) for cell in column)
        ws.column_dimensions[column[0].column_letter].width = min(max_length + 2, 50)
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    filename = f"transactions_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    response['Content-Disposition'] = f'attachment; filename={filename}'
    wb.save(response)
    return response


@login_required
def export_transactions_pdf(request):
    """Экспорт транзакций в PDF с помощью WeasyPrint"""
    transactions = DascoinTransaction.objects.filter(user=request.user).order_by('-created_at')
    html_string = render_to_string('users/transactions_pdf.html', {
        'transactions': transactions,
        'user': request.user,
        'generated_at': datetime.now(),
        'total_transactions': transactions.count(),
    })
    html = HTML(string=html_string)
    pdf = html.write_pdf()
    response = HttpResponse(pdf, content_type='application/pdf')
    filename = f"transactions_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    response['Content-Disposition'] = f'attachment; filename={filename}'
    audit_logger.info(
        'Экспортировал транзакции в PDF', 
        extra={
            'user': request.user.email if request.user.is_authenticated else 'Anonymous'
        }
    )
    return response


class AdminDashboardView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """CBV для отображения административной панели статистики пользователей по баллам DASCOIN"""
    model = User
    template_name = 'users/admin_dascoin_dashboard.html'
    context_object_name = 'users'
    paginate_by = 25
    ordering = ['-profile__dascoin_points', 'email']
    
    def test_func(self):
        """Проверяет, что пользователь является staff или superuser"""
        return self.request.user.is_staff or self.request.user.is_superuser
    
    def get_queryset(self):
        """Возвращает пользователей с фильтрацией"""
        queryset = User.objects.select_related('profile', 'profile__role').prefetch_related('groups').order_by('-profile__dascoin_points', 'email')
        
        # Фильтрация по группе
        group_id = self.request.GET.get('group')
        if group_id:
            queryset = queryset.filter(groups__id=group_id)
        
        # Фильтрация по должности
        role_id = self.request.GET.get('role')
        if role_id:
            queryset = queryset.filter(profile__role__id=role_id)
        
        # Фильтрация по минимальному количеству баллов
        points_min = self.request.GET.get('points_min')
        if points_min and points_min.isdigit():
            queryset = queryset.filter(profile__dascoin_points__gte=int(points_min))
        
        # Фильтрация по максимальному количеству баллов
        points_max = self.request.GET.get('points_max')
        if points_max and points_max.isdigit():
            queryset = queryset.filter(profile__dascoin_points__lte=int(points_max))
        
        # Быстрые фильтры
        zero_points = self.request.GET.get('zero_points')
        if zero_points:
            queryset = queryset.filter(profile__dascoin_points=0)
        
        approved_only = self.request.GET.get('approved')
        if approved_only:
            queryset = queryset.filter(profile__is_approved=True)
        
        # Применяем distinct() до среза
        queryset = queryset.distinct()
        
        # Быстрый фильтр топ-N применяется после distinct()
        top_users = self.request.GET.get('top')
        if top_users and top_users.isdigit():
            queryset = queryset.order_by('-profile__dascoin_points')[:int(top_users)]
        
        return queryset
    
    def get_context_data(self, **kwargs):
        """Добавляет дополнительный контекст"""
        context = super().get_context_data(**kwargs)
        
        # Общая статистика
        all_users = User.objects.select_related('profile')
        context['total_users'] = all_users.count()
        context['total_dascoin_points'] = all_users.aggregate(total=Sum('profile__dascoin_points'))['total'] or 0
        context['active_users'] = all_users.filter(is_active=True).count()
        
        # Группы и должности для фильтров
        context['groups'] = Group.objects.all().order_by('name')
        context['roles'] = Role.objects.all().order_by('name')
        
        # Параметры фильтрации
        context['selected_group'] = self.request.GET.get('group')
        context['selected_role'] = self.request.GET.get('role')
        context['points_min'] = self.request.GET.get('points_min')
        context['points_max'] = self.request.GET.get('points_max')
        
        # Флаги быстрых фильтров
        context['any_filter'] = any([
            self.request.GET.get('group'),
            self.request.GET.get('role'),
            self.request.GET.get('points_min'),
            self.request.GET.get('points_max'),
            self.request.GET.get('top'),
            self.request.GET.get('zero_points'),
            self.request.GET.get('approved')
        ])
        context['top_users'] = bool(self.request.GET.get('top'))
        context['zero_points'] = bool(self.request.GET.get('zero_points'))
        context['approved_only'] = bool(self.request.GET.get('approved'))
        
        # Параметры для пагинации
        query_params = self.request.GET.copy()
        if 'page' in query_params:
            del query_params['page']
        context['query_params'] = '&' + urlencode(query_params) if query_params else ''
        
        # Логирование действия
        audit_logger.info(
            'Просматривает административную панель статистики DASCOIN', 
            extra={
                'user': self.request.user.email if self.request.user.is_authenticated else 'Anonymous'
            }
        )
        
        return context


@login_required
def export_admin_stats_excel(request):
    """Экспорт статистики администратора в Excel"""
    if not (request.user.is_staff or request.user.is_superuser):
        return HttpResponse("Доступ запрещен", status=403)
    
    # Получаем данные с теми же фильтрами, что и в dashboard
    queryset = User.objects.select_related('profile', 'profile__role').prefetch_related('groups')
    
    # Применяем фильтры
    group_id = request.GET.get('group')
    if group_id:
        queryset = queryset.filter(groups__id=group_id)
    
    role_id = request.GET.get('role')
    if role_id:
        queryset = queryset.filter(profile__role__id=role_id)
    
    points_min = request.GET.get('points_min')
    if points_min and points_min.isdigit():
        queryset = queryset.filter(profile__dascoin_points__gte=int(points_min))
    
    points_max = request.GET.get('points_max')
    if points_max and points_max.isdigit():
        queryset = queryset.filter(profile__dascoin_points__lte=int(points_max))
    
    # Быстрые фильтры
    zero_points = request.GET.get('zero_points')
    if zero_points:
        queryset = queryset.filter(profile__dascoin_points=0)
    
    approved_only = request.GET.get('approved')
    if approved_only:
        queryset = queryset.filter(profile__is_approved=True)
    
    # Применяем distinct() до среза
    queryset = queryset.distinct()
    
    # Быстрый фильтр топ-N применяется после distinct()
    top_users = request.GET.get('top')
    if top_users and top_users.isdigit():
        queryset = queryset.order_by('-profile__dascoin_points')[:int(top_users)]
    else:
        queryset = queryset.order_by('-profile__dascoin_points', 'email')
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Статистика DASCOIN"
    
    headers = ['Пользователь', 'Email', 'Группы', 'Должность', 'DASCOIN', 'Статус', 'Дата регистрации']
    ws.append(headers)
    
    # Стили для заголовков
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    
    for user in queryset:
        groups = ', '.join([group.name for group in user.groups.all()])
        role = user.profile.role.name if user.profile.role else ''
        
        if user.is_active:
            if user.profile.is_approved:
                status = 'Активен'
            else:
                status = 'Ожидает подтверждения'
        else:
            status = 'Неактивен'
        
        ws.append([
            user.get_full_name() or user.email,
            user.email,
            groups,
            role,
            user.profile.dascoin_points,
            status,
            user.date_joined.strftime("%d.%m.%Y %H:%M")
        ])
    
    # Автоматическая ширина колонок
    for column in ws.columns:
        max_length = max(len(str(cell.value)) for cell in column)
        ws.column_dimensions[column[0].column_letter].width = min(max_length + 2, 50)
    
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    filename = f"admin_stats_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    response['Content-Disposition'] = f'attachment; filename={filename}'
    wb.save(response)
    
    audit_logger.info(
        'Экспортировал статистику администратора в Excel', 
        extra={
            'user': request.user.email if request.user.is_authenticated else 'Anonymous'
        }
    )
    return response


@login_required
def export_admin_stats_pdf(request):
    """Экспорт статистики администратора в PDF"""
    if not (request.user.is_staff or request.user.is_superuser):
        return HttpResponse("Доступ запрещен", status=403)
    
    # Получаем данные с теми же фильтрами
    queryset = User.objects.select_related('profile', 'profile__role').prefetch_related('groups')
    
    # Применяем фильтры
    group_id = request.GET.get('group')
    if group_id:
        queryset = queryset.filter(groups__id=group_id)
    
    role_id = request.GET.get('role')
    if role_id:
        queryset = queryset.filter(profile__role__id=role_id)
    
    points_min = request.GET.get('points_min')
    if points_min and points_min.isdigit():
        queryset = queryset.filter(profile__dascoin_points__gte=int(points_min))
    
    points_max = request.GET.get('points_max')
    if points_max and points_max.isdigit():
        queryset = queryset.filter(profile__dascoin_points__lte=int(points_max))
    
    # Быстрые фильтры
    zero_points = request.GET.get('zero_points')
    if zero_points:
        queryset = queryset.filter(profile__dascoin_points=0)
    
    approved_only = request.GET.get('approved')
    if approved_only:
        queryset = queryset.filter(profile__is_approved=True)
    
    # Применяем distinct() до среза
    queryset = queryset.distinct()
    
    # Быстрый фильтр топ-N применяется после distinct()
    top_users = request.GET.get('top')
    if top_users and top_users.isdigit():
        queryset = queryset.order_by('-profile__dascoin_points')[:int(top_users)]
    else:
        queryset = queryset.order_by('-profile__dascoin_points', 'email')
    
    # Общая статистика
    all_users = User.objects.select_related('profile')
    total_users = all_users.count()
    total_dascoin_points = all_users.aggregate(total=Sum('profile__dascoin_points'))['total'] or 0
    active_users = all_users.filter(is_active=True).count()
    
    html_string = render_to_string('users/admin_stats_pdf.html', {
        'users': queryset,
        'total_users': total_users,
        'total_dascoin_points': total_dascoin_points,
        'active_users': active_users,
        'generated_at': datetime.now(),
        'generated_by': request.user.get_full_name() or request.user.email,
    })
    
    html = HTML(string=html_string)
    pdf = html.write_pdf()
    response = HttpResponse(pdf, content_type='application/pdf')
    filename = f"admin_stats_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    response['Content-Disposition'] = f'attachment; filename={filename}'
    
    audit_logger.info(
        'Экспортировал статистику администратора в PDF', 
        extra={
            'user': request.user.email if request.user.is_authenticated else 'Anonymous'
        }
    )
    return response


class AdminUserTransactionsView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """CBV для отображения истории транзакций DASCOIN конкретного пользователя администратором"""
    model = DascoinTransaction
    template_name = 'users/admin_user_transactions.html'
    context_object_name = 'transactions'
    paginate_by = 20
    ordering = ['-created_at']
    
    def test_func(self):
        """Проверяет, что пользователь является staff или superuser"""
        return self.request.user.is_staff or self.request.user.is_superuser
    
    def get_queryset(self):
        """Возвращает транзакции конкретного пользователя с возможностью фильтрации"""
        user_id = self.kwargs.get('user_id')
        self.user = get_object_or_404(User, id=user_id)
        
        queryset = DascoinTransaction.objects.filter(user=self.user).order_by('-created_at')
        
        # Фильтрация по типу транзакции
        transaction_type = self.request.GET.get('type')
        if transaction_type and transaction_type in ['award', 'deduct', 'set', 'correction']:
            queryset = queryset.filter(transaction_type=transaction_type)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        """Добавляет дополнительный контекст"""
        context = super().get_context_data(**kwargs)
        
        context['user'] = self.user
        context['total_transactions'] = self.get_queryset().count()
        context['current_filter'] = self.request.GET.get('type', '')
        
        # Статистика по типам транзакций
        all_transactions = DascoinTransaction.objects.filter(user=self.user)
        context['stats'] = {
            'award': all_transactions.filter(transaction_type='award').count(),
            'deduct': all_transactions.filter(transaction_type='deduct').count(),
            'set': all_transactions.filter(transaction_type='set').count(),
            'correction': all_transactions.filter(transaction_type='correction').count(),
        }
        
        # Логирование действия
        audit_logger.info(
            f'Просматривает историю транзакций пользователя {self.user.email}', 
            extra={
                'user': self.request.user.email if self.request.user.is_authenticated else 'Anonymous',
                'target_user': self.user.email
            }
        )
        
        return context


@login_required
def export_admin_user_transactions_excel(request, user_id):
    """Экспорт транзакций конкретного пользователя в Excel"""
    if not (request.user.is_staff or request.user.is_superuser):
        return HttpResponse("Доступ запрещен", status=403)
    
    user = get_object_or_404(User, id=user_id)
    transactions = DascoinTransaction.objects.filter(user=user).order_by('-created_at')
    
    # Применяем фильтры
    transaction_type = request.GET.get('type')
    if transaction_type and transaction_type in ['award', 'deduct', 'set', 'correction']:
        transactions = transactions.filter(transaction_type=transaction_type)
    
    wb = Workbook()
    ws = wb.active
    ws.title = f"Транзакции {user.email}"
    
    headers = ['Дата', 'Тип', 'Изменение', 'До', 'После', 'Причина', 'Администратор']
    ws.append(headers)
    
    # Стили для заголовков
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    
    for tx in transactions:
        ws.append([
            tx.created_at.strftime("%d.%m.%Y %H:%M"),
            tx.get_transaction_type_display(),
            tx.points_change,
            tx.points_before,
            tx.points_after,
            tx.reason or "Не указана",
            tx.admin_user.get_full_name() if tx.admin_user else "Система"
        ])
    
    # Автоматическая ширина колонок
    for column in ws.columns:
        max_length = max(len(str(cell.value)) for cell in column)
        ws.column_dimensions[column[0].column_letter].width = min(max_length + 2, 50)
    
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    filename = f"transactions_{user.email}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    response['Content-Disposition'] = f'attachment; filename={filename}'
    wb.save(response)
    
    audit_logger.info(
        f'Экспортировал транзакции пользователя {user.email} в Excel', 
        extra={
            'user': request.user.email if request.user.is_authenticated else 'Anonymous',
            'target_user': user.email
        }
    )
    return response


@login_required
def export_admin_user_transactions_pdf(request, user_id):
    """Экспорт транзакций конкретного пользователя в PDF"""
    if not (request.user.is_staff or request.user.is_superuser):
        return HttpResponse("Доступ запрещен", status=403)
    
    user = get_object_or_404(User, id=user_id)
    transactions = DascoinTransaction.objects.filter(user=user).order_by('-created_at')
    
    # Применяем фильтры
    transaction_type = request.GET.get('type')
    if transaction_type and transaction_type in ['award', 'deduct', 'set', 'correction']:
        transactions = transactions.filter(transaction_type=transaction_type)
    
    html_string = render_to_string('users/transactions_pdf.html', {
        'transactions': transactions,
        'user': user,
        'generated_at': datetime.now(),
        'total_transactions': transactions.count(),
        'is_admin_view': True,
        'generated_by': request.user.get_full_name() or request.user.email,
    })
    
    html = HTML(string=html_string)
    pdf = html.write_pdf()
    response = HttpResponse(pdf, content_type='application/pdf')
    filename = f"transactions_{user.email}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    response['Content-Disposition'] = f'attachment; filename={filename}'
    
    audit_logger.info(
        f'Экспортировал транзакции пользователя {user.email} в PDF', 
        extra={
            'user': request.user.email if request.user.is_authenticated else 'Anonymous',
            'target_user': user.email
        }
    )
    return response