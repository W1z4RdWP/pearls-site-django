import json

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.db import transaction
from django.db.models import Q, Max
from django.http import Http404, JsonResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView, TemplateView, UpdateView

from courses.models import Course, Lesson, Trajectory, TrajectoryCourse, UserCourseTrajectory
from quizzes.models import Quiz


class TrajectoryManagementView(TemplateView):
    """
    Централизованная панель управления траекториями для администраторов.
    Позволяет создавать и управлять уроками, курсами, траекториями и тестами.
    """
    template_name = 'builder/trajectory_management.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Статистика для дашборда (исключаем курсы-инциденты)
        context['total_courses'] = Course.objects.filter(is_incident=False).count()
        context['total_incident_courses'] = Course.objects.filter(is_incident=True).count()
        context['total_lessons'] = Lesson.objects.count()
        context['total_trajectories'] = Trajectory.objects.count()
        context['total_quizzes'] = Quiz.objects.count()
        context['total_users'] = User.objects.count()
        
        # Последние созданные элементы (исключаем курсы-инциденты из общего списка)
        context['recent_courses'] = Course.objects.filter(is_incident=False).order_by('-created_at')[:5]
        context['recent_lessons'] = Lesson.objects.order_by('-id')[:5]
        context['recent_trajectories'] = Trajectory.objects.order_by('-id')[:5]
        context['recent_quizzes'] = Quiz.objects.order_by('-id')[:5]
        
        # Все группы Django для выбора в модальных окнах
        context['all_groups'] = Group.objects.all()
        
        return context




class TrajectoryListView(ListView):
    """
    Список всех траекторий с возможностью управления.
    """
    model = Trajectory
    template_name = 'builder/trajectory_list.html'
    context_object_name = 'trajectories'
    ordering = ['name']
    paginate_by = 20

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Добавляем статистику
        context['total_trajectories'] = Trajectory.objects.count()
        context['total_courses'] = Course.objects.count()
        context['total_groups'] = Group.objects.count()
        
        # Добавляем все группы для модального окна создания траектории
        context['all_groups'] = Group.objects.all().order_by('name')
        
        # Добавляем поиск
        search_query = self.request.GET.get('search', '')
        if search_query:
            context['trajectories'] = Trajectory.objects.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query)
            ).order_by('name')
        
        context['search_query'] = search_query
        
        return context




@csrf_exempt
@login_required
def trajectory_detail_ajax(request, trajectory_id):
    """
    AJAX представление для получения детальной информации о траектории
    """
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'forbidden'}, status=403)
    
    try:
        trajectory = Trajectory.objects.get(pk=trajectory_id)
    except Trajectory.DoesNotExist:
        return JsonResponse({'error': 'Траектория не найдена'}, status=404)
    
    # Получаем курсы в правильном порядке
    trajectory_courses = TrajectoryCourse.objects.filter(trajectory=trajectory).select_related('course').order_by('order')
    
    # Получаем статистику пользователей
    user_trajectories = UserCourseTrajectory.objects.filter(trajectory=trajectory)
    total_users = user_trajectories.count()
    active_users = user_trajectories.filter(completed=False).count()
    completed_users = user_trajectories.filter(completed=True).count()
    
    # Формируем данные для ответа
    data = {
        'id': trajectory.id,
        'name': trajectory.name,
        'description': trajectory.description or 'Описание отсутствует',
        'groups': [
            {
                'id': group.id,
                'name': group.name,
                'user_count': group.user_set.count()
            } for group in trajectory.groups.all()
        ],
        'courses': [
            {
                'id': tc.course.id,
                'title': tc.course.title,
                'order': tc.order,
                'lesson_count': tc.course.lessons.count(),
                'author': tc.course.author.get_full_name() or tc.course.author.username
            } for tc in trajectory_courses
        ],
        'statistics': {
            'total_users': total_users,
            'active_users': active_users,
            'completed_users': completed_users,
            'completion_rate': round((completed_users / total_users * 100) if total_users > 0 else 0, 1)
        },
        'created_at': trajectory.id,  # Используем ID как приблизительную дату создания
        'total_courses': trajectory.courses.count(),
        'total_groups': trajectory.groups.count()
    }
    
    return JsonResponse(data)




class TrajectoryEditView(UpdateView):
    """
    Представление для редактирования траектории
    """
    model = Trajectory
    template_name = 'builder/trajectory_edit.html'
    fields = ['name', 'description', 'groups']
    success_url = reverse_lazy('builder:trajectory_list')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['trajectory'] = self.object
        context['all_groups'] = Group.objects.all()
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Траектория успешно обновлена',
                'redirect_url': self.success_url
            })
        return response

    def form_invalid(self, form):
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'errors': form.errors
            }, status=400)
        return super().form_invalid(form)




class TrajectoryCoursesView(TemplateView):
    """
    Представление для управления курсами в траектории
    """
    template_name = 'builder/trajectory_courses.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        trajectory_id = self.kwargs.get('trajectory_id')
        
        try:
            trajectory = Trajectory.objects.get(pk=trajectory_id)
        except Trajectory.DoesNotExist:
            raise Http404("Траектория не найдена")
        
        # Получаем курсы в траектории с их порядком
        trajectory_courses = TrajectoryCourse.objects.filter(trajectory=trajectory).select_related('course').order_by('order')
        
        # Получаем все доступные курсы для добавления
        available_courses = Course.objects.exclude(
            id__in=trajectory_courses.values_list('course_id', flat=True)
        ).order_by('title')
        
        context['trajectory'] = trajectory
        context['trajectory_courses'] = trajectory_courses
        context['available_courses'] = available_courses
        context['total_courses'] = trajectory_courses.count()
        
        return context




@csrf_exempt
@login_required
def trajectory_course_reorder(request, trajectory_id):
    """
    AJAX представление для изменения порядка курсов в траектории
    """
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'forbidden'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        course_orders = data.get('course_orders', [])  # [{course_id: 1, order: 1}, ...]
        
        with transaction.atomic():
            for item in course_orders:
                course_id = item.get('course_id')
                new_order = item.get('order')
                
                if course_id and new_order is not None:
                    TrajectoryCourse.objects.filter(
                        trajectory_id=trajectory_id,
                        course_id=course_id
                    ).update(order=new_order)
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)




@csrf_exempt
@login_required
def trajectory_course_add(request, trajectory_id):
    """
    AJAX представление для добавления курса в траекторию
    """
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'forbidden'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        course_id = data.get('course_id')
        
        if not course_id:
            return JsonResponse({'error': 'course_id required'}, status=400)
        
        # Получаем максимальный порядок в траектории
        max_order = TrajectoryCourse.objects.filter(trajectory_id=trajectory_id).aggregate(
            Max('order')
        )['order__max'] or 0
        
        # Создаем новую связь
        TrajectoryCourse.objects.create(
            trajectory_id=trajectory_id,
            course_id=course_id,
            order=max_order + 1
        )
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)




@csrf_exempt
@login_required
def trajectory_course_add_multiple(request, trajectory_id):
    """
    AJAX представление для добавления нескольких курсов в траекторию
    """
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'success': False, 'error': 'Недостаточно прав'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Метод не поддерживается'}, status=405)
    
    try:
        data = json.loads(request.body)
        course_ids = data.get('course_ids', [])
        
        if not course_ids or not isinstance(course_ids, list):
            return JsonResponse({'success': False, 'error': 'Список ID курсов обязателен'}, status=400)
        
        # Проверяем существование траектории
        try:
            trajectory = Trajectory.objects.get(id=trajectory_id)
        except Trajectory.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Траектория не найдена'}, status=404)
        
        # Проверяем существование курсов
        from courses.models import Course
        existing_courses = Course.objects.filter(id__in=course_ids)
        if len(existing_courses) != len(course_ids):
            return JsonResponse({'success': False, 'error': 'Некоторые курсы не найдены'}, status=400)
        
        # Получаем максимальный порядок в траектории
        max_order = TrajectoryCourse.objects.filter(trajectory_id=trajectory_id).aggregate(
            Max('order')
        )['order__max'] or 0
        
        # Создаем связи для всех курсов
        trajectory_courses = []
        for i, course_id in enumerate(course_ids):
            # Проверяем, не добавлен ли уже курс
            if not TrajectoryCourse.objects.filter(trajectory_id=trajectory_id, course_id=course_id).exists():
                trajectory_courses.append(
                    TrajectoryCourse(
                        trajectory_id=trajectory_id,
                        course_id=course_id,
                        order=max_order + i + 1
                    )
                )
        
        # Массово создаем записи
        if trajectory_courses:
            TrajectoryCourse.objects.bulk_create(trajectory_courses)
        
        added_count = len(trajectory_courses)
        skipped_count = len(course_ids) - added_count
        
        message = f'Добавлено курсов: {added_count}'
        if skipped_count > 0:
            message += f', пропущено (уже добавлены): {skipped_count}'
        
        return JsonResponse({
            'success': True,
            'message': message,
            'added_count': added_count,
            'skipped_count': skipped_count
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Неверный формат JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)




@csrf_exempt
@login_required
def trajectory_course_remove(request, trajectory_id):
    """
    AJAX представление для удаления курса из траектории
    """
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'forbidden'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        course_id = data.get('course_id')
        
        if not course_id:
            return JsonResponse({'error': 'course_id required'}, status=400)
        
        # Удаляем связь
        TrajectoryCourse.objects.filter(
            trajectory_id=trajectory_id,
            course_id=course_id
        ).delete()
        
        # Пересчитываем порядок оставшихся курсов
        remaining_courses = TrajectoryCourse.objects.filter(
            trajectory_id=trajectory_id
        ).order_by('order')
        
        for index, tc in enumerate(remaining_courses, 1):
            tc.order = index
            tc.save()
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)




@csrf_exempt
@login_required
def trajectory_delete(request, trajectory_id):
    """
    AJAX представление для удаления траектории и всех связанных с ней данных
    """
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'success': False, 'error': 'Недостаточно прав'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Метод не поддерживается'}, status=405)
    
    try:
        trajectory = Trajectory.objects.get(id=trajectory_id)
    except Trajectory.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Траектория не найдена'}, status=404)
    
    try:
        with transaction.atomic():
            # Удаляем все связи с курсами
            TrajectoryCourse.objects.filter(trajectory=trajectory).delete()
            
            # Удаляем все записи о прогрессе пользователей по этой траектории
            UserCourseTrajectory.objects.filter(trajectory=trajectory).delete()
            
            # Удаляем саму траекторию
            trajectory.delete()
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)




class CourseListView(ListView):
    """
    Представление для просмотра всех курсов на платформе сотрудниками УЦ.
    """
    template_name = 'builder/course_list.html'
    context_object_name = 'courses'
    paginate_by = 15
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        from courses.models import Course
        from django.db.models import Q
        
        queryset = Course.objects.exclude(is_incident=True)
        
        # Поиск по названию
        search_query = self.request.GET.get('search', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) | 
                Q(description__icontains=search_query) |
                Q(slug__icontains=search_query)
            )
        
        # Фильтр по автору
        author_id = self.request.GET.get('author', '').strip()
        if author_id:
            try:
                queryset = queryset.filter(author_id=int(author_id))
            except (ValueError, TypeError):
                pass
        
        # Фильтр по группам
        group_id = self.request.GET.get('group', '').strip()
        if group_id:
            try:
                from django.contrib.auth.models import Group
                group = Group.objects.get(id=int(group_id))
                # Фильтруем курсы, которые принадлежат этой группе через траектории
                queryset = queryset.filter(trajectory__groups=group).distinct()
            except (ValueError, TypeError, Group.DoesNotExist):
                pass
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from courses.models import Course
        from django.contrib.auth.models import User
        
        # Получаем параметры фильтрации для сохранения в форме
        context['search_query'] = self.request.GET.get('search', '')
        context['selected_author'] = self.request.GET.get('author', '')
        context['selected_group'] = self.request.GET.get('group', '')
        
        # Статистика (всегда показываем общую статистику)
        context['total_courses'] = Course.objects.exclude(is_incident=True).count()
        context['active_courses'] = Course.objects.exclude(is_incident=True).count()  # Все курсы считаются активными
        context['total_lessons'] = sum(course.lessons.count() for course in Course.objects.exclude(is_incident=True))
        context['total_authors'] = User.objects.filter(authored_courses__isnull=False).distinct().count()
        
        # Список авторов для фильтра
        context['authors'] = User.objects.filter(authored_courses__isnull=False).distinct().order_by('first_name', 'last_name', 'username')
        
        # Список групп для фильтра
        from django.contrib.auth.models import Group
        context['groups'] = Group.objects.all().order_by('name')
        
        return context




class IncidentCourseListView(ListView):
    """
    Представление для просмотра всех курсов-инцидентов на платформе сотрудниками УЦ.
    """
    template_name = 'builder/incident_course_list.html'
    context_object_name = 'courses'
    paginate_by = 15

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_staff or request.user.is_superuser):
            return render(request, '403.html', status=403)
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        queryset = Course.objects.filter(is_incident=True)

                # Поиск по названию
        search_query = self.request.GET.get('search', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) | 
                Q(description__icontains=search_query) |
                Q(slug__icontains=search_query)
            )
        
        # Фильтр по автору
        author_id = self.request.GET.get('author', '').strip()
        if author_id:
            try:
                queryset = queryset.filter(author_id=int(author_id))
            except (ValueError, TypeError):
                pass
        
        # Фильтр по группам
        group_id = self.request.GET.get('group', '').strip()
        if group_id:
            try:
                from django.contrib.auth.models import Group
                group = Group.objects.get(id=int(group_id))
                # Фильтруем курсы, которые принадлежат этой группе через траектории
                queryset = queryset.filter(trajectory__groups=group).distinct()
            except (ValueError, TypeError, Group.DoesNotExist):
                pass
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from courses.models import Course
        from django.contrib.auth.models import User
        
        # Получаем параметры фильтрации для сохранения в форме
        context['search_query'] = self.request.GET.get('search', '')
        context['selected_author'] = self.request.GET.get('author', '')
        context['selected_group'] = self.request.GET.get('group', '')
        
        # Статистика (всегда показываем общую статистику)
        context['total_courses'] = Course.objects.filter(is_incident=True).count()
        context['active_courses'] = Course.objects.filter(is_incident=True).count()  # Все курсы считаются активными
        context['total_lessons'] = sum(course.lessons.count() for course in Course.objects.filter(is_incident=True))
        context['total_authors'] = User.objects.filter(authored_courses__isnull=False).distinct().count()
        
        # Список авторов для фильтра
        context['authors'] = User.objects.filter(authored_courses__isnull=False).distinct().order_by('first_name', 'last_name', 'username')
        
        # Список групп для фильтра
        from django.contrib.auth.models import Group
        context['groups'] = Group.objects.all().order_by('name')
        
        return context