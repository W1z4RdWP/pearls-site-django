from courses.models import Course, UserLessonTrajectory
from .models import CategoryName


def get_compact_fio(user):
    """
    Возвращает компактное ФИО: фамилия полностью, имя и отчество инициалами
    Например: "Кузнецов В.А." вместо "Владислав Александрович Кузнецов"
    """
    if not user:
        return None
    
    last_name = user.last_name or ''
    first_name = user.first_name or ''
    middle_name = getattr(user.profile, 'middle_name', '') if hasattr(user, 'profile') else ''
    
    # Формируем инициалы
    first_initial = first_name[0] + '.' if first_name else ''
    middle_initial = middle_name[0] + '.' if middle_name else ''
    
    # Собираем ФИО
    parts = [last_name]
    if first_initial:
        parts.append(first_initial)
    if middle_initial:
        parts.append(middle_initial)
    
    return ' '.join(parts) if parts else user.username




def user_has_category_access(user, category):
    """
    Проверяет, есть ли у пользователя доступ к категории через allowed_groups (учитывает родителей).
    Доступ наследуется вниз по дереву.
    """
    if not user.is_authenticated:
        return False
    user_groups = set(user.groups.values_list('id', flat=True))
    cat = category
    while cat:
        allowed = set(cat.allowed_groups.values_list('id', flat=True))
        if allowed and user_groups & allowed:
            return True
        cat = cat.parent
    return False




def filter_categories_and_lessons_for_user(user, categories, uncategorized_lessons):
    """
    Фильтрует дерево категорий и список уроков без категории для read-only пользователя,
    чтобы показывать только те уроки, которые входят в доступные для пользователя курсы
    ИЛИ доступны через группы в allowed_groups (категории и все вложенные).
    """
    # Получаем все курсы, доступные пользователю через менеджер
    available_courses = Course.objects.available_for_user(user)
    allowed_course_ids = set(c.id for c in available_courses)

    # Собираем все разрешённые уроки (с учётом траекторий)
    allowed_lesson_ids = set()
    for course in available_courses:
        trajectory = UserLessonTrajectory.objects.filter(user=user, course=course).first()
        if trajectory:
            allowed_lesson_ids.update(trajectory.lessons.values_list('id', flat=True))
        else:
            allowed_lesson_ids.update(course.lessons.values_list('id', flat=True))


    # --- ДОБАВЛЯЕМ доступ через группы (категории и все вложенные) ---
    def collect_group_accessible_lessons(cat_data, parent_access=False):
        # parent_access: был ли доступ у родителя
        cat_id = cat_data['id']
        cat_obj = CategoryName.objects.get(id=cat_id)
        has_access = parent_access or user_has_category_access(user, cat_obj)
        group_lesson_ids = set()
        if has_access:
            group_lesson_ids.update(lesson['id'] for lesson in cat_data['lessons'])
        for subcat in cat_data['subcategories']:
            group_lesson_ids.update(collect_group_accessible_lessons(subcat, has_access))
        return group_lesson_ids

    group_access_lesson_ids = set()
    for cat_data in categories:
        if cat_data:
            group_access_lesson_ids.update(collect_group_accessible_lessons(cat_data))
    allowed_lesson_ids.update(group_access_lesson_ids)

    # Фильтруем уроки без категории
    filtered_uncat = uncategorized_lessons.filter(id__in=allowed_lesson_ids)


    # Рекурсивно фильтруем дерево категорий (работаем со словарями из get_category_tree_data)
    def filter_category(cat_data, parent_access=False):
        cat_id = cat_data['id']
        cat_obj = CategoryName.objects.get(id=cat_id)
        has_access = parent_access or user_has_category_access(user, cat_obj)
        # Фильтруем уроки в категории
        filtered_lessons = [lesson for lesson in cat_data['lessons'] if lesson['id'] in allowed_lesson_ids]
        # Рекурсивно фильтруем подкатегории
        filtered_subcats = [filter_category(subcat, has_access) for subcat in cat_data['subcategories']]
        filtered_subcats = [sc for sc in filtered_subcats if sc is not None]
        if filtered_lessons or filtered_subcats:
            filtered_cat = cat_data.copy()
            filtered_cat['filtered_lessons'] = filtered_lessons
            filtered_cat['filtered_subcategories'] = filtered_subcats
            return filtered_cat
        return None

    filtered_categories = []
    for cat_data in categories:
        if cat_data:
            filtered = filter_category(cat_data)
            if filtered:
                filtered_categories.append(filtered)
    return filtered_categories, filtered_uncat