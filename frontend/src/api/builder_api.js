import { request } from './api';

// ---------------------------------------------------------------------------
// База знаний (содержание, мастер-деталь)
// ---------------------------------------------------------------------------

/**
 * Данные страницы «Содержание базы знаний»: дерево категорий, уроки без категории, словарь, флаги доступа.
 * При передаче lessonId в ответ добавляются данные выбранного урока (деталь, версии, актуализация, черновик).
 * @param {number|null} [lessonId] — опциональный ID урока для блока детали
 * @returns {Promise<{
 *   categories: Array<{ id, name, order, subcategories, lessons }>,
 *   uncategorized_lessons: Array<{ id, title, has_mirrors }>,
 *   dictionary_sections: Array<{ id, name }>,
 *   is_readonly: boolean,
 *   roles: Array<{ id, name }>,
 *   urls: { update_control, lesson_draft_create, lesson_draft_edit, lesson_draft_review },
 *   selected_lesson?: { id, title, content, video_id }|null,
 *   lesson_versions?: Array<{ version, title, content, video_id }>,
 *   actualization_history?: Array,
 *   actualization_info?: { next_update, responsible_role }|null,
 *   today?: string|null,
 *   user_is_responsible_for_lesson?: boolean,
 *   responsible_id_default?: number|null,
 *   previous_role_id?: number|null,
 *   previous_role_name?: string|null,
 *   pending_draft?: { id, lesson_id, edit_url, review_url }|null,
 *   is_mentor_only?: boolean
 * }>}
 */
export function fetchMasterDetailContent(lessonId = null) {
  const url = lessonId != null ? `/builder/content/?lesson_id=${lessonId}` : '/builder/content/';
  return request(url);
}

/**
 * Данные страницы «Содержание базы знаний» с выбранным уроком по ID из URL (аналог /builder/lesson/<pk>/).
 * Возвращает те же поля, что и fetchMasterDetailContent(lessonId), с заполненным блоком детали урока.
 * @param {number} pk — ID урока
 * @returns {Promise<object>} — тот же формат, что и fetchMasterDetailContent с lesson_id
 */
export function fetchLessonDetail(pk) {
  return request(`/builder/lesson/${pk}/`);
}

/**
 * Данные урока для диалога удаления (название).
 * @param {number} id — ID урока
 * @returns {Promise<{ title: string }>}
 */
export function fetchLessonDeleteInfo(id) {
  return request('/builder/lesson/delete/info/', {
    method: 'POST',
    body: JSON.stringify({ id: Number(id) }),
  });
}

/**
 * Удаление урока (как в Django LessonDeleteView: аудит и delete).
 * @param {number} id — ID урока
 * @returns {Promise<{ success: boolean }>}
 */
export function deleteLesson(id) {
  return request('/builder/lesson/delete/', {
    method: 'POST',
    body: JSON.stringify({ id: Number(id) }),
  });
}

/**
 * Создание корневой категории (inline в сайдбаре базы знаний).
 * @param {string} name — название категории
 * @returns {Promise<{ id: number, name: string, order: number }>}
 */
export function createRootCategory(name) {
  return request('/builder/categories/root/', {
    method: 'POST',
    body: JSON.stringify({ name: (name || '').trim() }),
  });
}

/**
 * Создание подкатегории (inline в сайдбаре базы знаний).
 * @param {number} parentId — ID родительской категории
 * @param {string} name — название подкатегории
 * @returns {Promise<{ id: number, name: string, order: number, parent: number }>}
 */
export function createSubcategory(parentId, name) {
  return request('/builder/categories/sub/', {
    method: 'POST',
    body: JSON.stringify({ parent_id: parentId, name: (name || '').trim() }),
  });
}

/**
 * Переименование категории (инлайн в сайдбаре базы знаний).
 * @param {number} id — ID категории
 * @param {string} name — новое название
 * @returns {Promise<{ id: number, name: string }>}
 */
export function renameCategory(id, name) {
  return request('/builder/categories/rename/', {
    method: 'POST',
    body: JSON.stringify({ id: Number(id), name: (name || '').trim() }),
  });
}

/**
 * Статистика категории для диалога удаления.
 * @param {number} id — ID категории
 * @returns {Promise<{ name: string, subcategories_count: number, lessons_count: number, mirrors_count: number, total_items: number }>}
 */
export function fetchCategoryDeleteStats(id) {
  return request('/builder/categories/delete/stats/', {
    method: 'POST',
    body: JSON.stringify({ id: Number(id) }),
  });
}

/**
 * Удаление категории.
 * @param {number} id — ID категории
 * @param {'move_to_none'|'delete_all'} [action] — move_to_none: перенести в «Без категории»; delete_all: удалить безвозвратно
 * @returns {Promise<{ success: boolean }>}
 */
export function deleteCategory(id, action = 'move_to_none') {
  return request('/builder/categories/delete/', {
    method: 'POST',
    body: JSON.stringify({ id: Number(id), action }),
  });
}

// ---------------------------------------------------------------------------
// Контекстное меню: буфер обмена (copy/cut/paste), зеркала, назначение
// ---------------------------------------------------------------------------

/**
 * Получить содержимое серверного буфера обмена.
 * @returns {Promise<{ empty?: true, id?, type?, action? }>}
 */
export function fetchClipboard() {
  return request('/builder/clipboard/');
}

/**
 * Скопировать урок или категорию в буфер обмена.
 * @param {string|number} id
 * @param {'lesson'|'category'} type
 */
export function clipboardCopy(id, type) {
  return request('/builder/copy/', {
    method: 'POST',
    body: JSON.stringify({ id, type }),
  });
}

/**
 * Вырезать урок или категорию в буфер обмена.
 * @param {string|number} id
 * @param {'lesson'|'category'} type
 */
export function clipboardCut(id, type) {
  return request('/builder/cut/', {
    method: 'POST',
    body: JSON.stringify({ id, type }),
  });
}

/**
 * Вставить элемент из буфера обмена в указанную категорию.
 * @param {string|number|null} targetCategory — ID категории-назначения (null/'' = корень / без категории)
 * @returns {Promise<{ ok: true, result: { id, title|name } }>}
 */
export function clipboardPaste(targetCategory) {
  return request('/builder/paste/', {
    method: 'POST',
    body: JSON.stringify({ target_category: targetCategory ?? '' }),
  });
}

/**
 * Создать зеркало урока в указанной категории.
 * @param {string|number} lessonId
 * @param {string|number} categoryId
 */
export function createMirror(lessonId, categoryId) {
  return request('/builder/mirror/', {
    method: 'POST',
    body: JSON.stringify({ lesson_id: lessonId, category_id: categoryId }),
  });
}

/**
 * Получить все ID уроков категории (включая подкатегории) — для назначения.
 * @param {number} categoryId
 * @returns {Promise<{ lesson_ids: number[], category_name: string, count: number }>}
 */
export function fetchCategoryLessons(categoryId) {
  return request(`/builder/categories/${categoryId}/lessons/`);
}

// ---------------------------------------------------------------------------
// Управление траекториями, курсы, формы уроков
// ---------------------------------------------------------------------------

/**
 * Данные страницы «Управление траекториями»: статистика, последние уроки/курсы/траектории/тесты, группы, URL.
 * Только для staff/superuser.
 * @returns {Promise<{ total_lessons, total_courses, total_incident_courses, total_trajectories, total_quizzes, recent_lessons, recent_courses, recent_trajectories, recent_quizzes, all_groups, urls }>}
 */
export function fetchTrajectoryManagementData() {
  return request('/builder/trajectory-management/');
}

/**
 * Список курсов (не инциденты) с пагинацией и фильтрами.
 * @param {Object} params - search, author, group, page
 * @returns {Promise<{ items, pagination, total_courses, total_lessons, total_authors, authors, groups, urls }>}
 */
export function fetchCourseList(params = {}) {
  const searchParams = new URLSearchParams();
  if (params.search != null && params.search !== '') searchParams.set('search', params.search);
  if (params.author != null && params.author !== '') searchParams.set('author', params.author);
  if (params.group != null && params.group !== '') searchParams.set('group', params.group);
  if (params.page != null && params.page > 1) searchParams.set('page', params.page);
  const qs = searchParams.toString();
  return request(`/builder/courses/${qs ? `?${qs}` : ''}`);
}

/**
 * Удаление курса по slug.
 * @param {string} slug
 * @returns {Promise<{ success: boolean }>}
 */
export function deleteCourse(slug) {
  return request(`/builder/course/${encodeURIComponent(slug)}/delete/`, {
    method: 'POST',
  });
}

/**
 * Список курсов-инцидентов с пагинацией и фильтрами.
 * @param {Object} params - search, author, group, page
 * @returns {Promise<{ items, pagination, total_courses, total_lessons, total_authors, authors, groups, urls }>}
 */
export function fetchIncidentCourseList(params = {}) {
  const searchParams = new URLSearchParams();
  if (params.search != null && params.search !== '') searchParams.set('search', params.search);
  if (params.author != null && params.author !== '') searchParams.set('author', params.author);
  if (params.group != null && params.group !== '') searchParams.set('group', params.group);
  if (params.page != null && params.page > 1) searchParams.set('page', params.page);
  const qs = searchParams.toString();
  return request(`/builder/incident-courses/${qs ? `?${qs}` : ''}`);
}

/**
 * Удаление курса-инцидента по slug.
 * @param {string} slug
 * @returns {Promise<{ success: boolean }>}
 */
export function deleteIncidentCourse(slug) {
  return request(`/builder/incident-courses/course/${encodeURIComponent(slug)}/delete/`, {
    method: 'POST',
  });
}

/**
 * Данные формы добавления урока (категории, курсы, тесты, preselected_category).
 * @param {number|null} [categoryId] — опциональный ID категории для предзаполнения
 * @returns {Promise<{ categories, courses, quizzes, preselected_category, cancel_url }>}
 */
export function fetchLessonFormCreateData(categoryId = null) {
  const url = categoryId != null ? `/builder/add/${categoryId}/` : '/builder/add/';
  return request(url);
}

/**
 * Создание урока (форма базы знаний builder).
 * @param {Object} data — title, content, category_id?, course_ids[], required_time?, final_quiz_id?, return_url?
 * @param {number|null} [categoryId] — опциональный ID категории из URL
 * @returns {Promise<{ success: boolean, lesson_id: number, redirect_url: string }>}
 */
export function createLesson(data, categoryId = null) {
  const url = categoryId != null ? `/builder/add/${categoryId}/` : '/builder/add/';
  return request(url, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/**
 * Данные формы редактирования урока (builder).
 * @param {number} pk — ID урока
 * @returns {Promise<{ lesson, categories, courses_choices, quizzes, cancel_url }>}
 */
export function fetchLessonFormEditData(pk) {
  return request(`/builder/lesson/${pk}/edit/`);
}

/**
 * Сохранение изменений урока (builder).
 * @param {number} pk — ID урока
 * @param {Object} data — title, content, order, category_id?, course_ids[], required_time?, final_quiz_id?, return_url?
 * @returns {Promise<{ success: boolean, redirect_url: string }>}
 */
export function updateLesson(pk, data) {
  return request(`/builder/lesson/${pk}/edit/`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

// ---------------------------------------------------------------------------
// Инциденты
// ---------------------------------------------------------------------------

/**
 * Список инцидентов с фильтрами (даты, статусы, тип).
 * @param {Object} params — date_from, date_to, status[] (массив), incident_type
 * @returns {Promise<{ incidents, status_choices, incident_type_choices, date_from, date_to, selected_statuses, selected_incident_type, readonly }>}
 */
export function fetchIncidents(params = {}) {
  const searchParams = new URLSearchParams();
  if (params.date_from != null && params.date_from !== '') searchParams.set('date_from', params.date_from);
  if (params.date_to != null && params.date_to !== '') searchParams.set('date_to', params.date_to);
  if (params.incident_type != null && params.incident_type !== '') searchParams.set('incident_type', params.incident_type);
  if (params.status != null && Array.isArray(params.status)) {
    params.status.forEach((s) => searchParams.append('status', s));
  }
  const qs = searchParams.toString();
  return request(`/builder/incidents/${qs ? `?${qs}` : ''}`);
}

/**
 * Отклонить или возобновить инцидент (toggle). POST.
 * @param {number} pk — ID инцидента
 * @returns {Promise<{ success: boolean, status: string, status_display: string }>}
 */
export function declineIncident(pk) {
  return request(`/builder/incidents/${pk}/decline/`, {
    method: 'POST',
    body: JSON.stringify({}),
  });
}

/**
 * Данные страницы «Детали инцидентов»: пользователи для фильтра, список назначений, фильтры.
 * @param {Object} params — search, date_from, date_to, assigned_user, violator_filter
 * @returns {Promise<{ users, incident_user_list, date_from, date_to, search, selected_user_id, violator_filter, violator_filter_locked }>}
 */
export function fetchIncidentDetail(params = {}) {
  const searchParams = new URLSearchParams();
  if (params.search != null && params.search !== '') searchParams.set('search', params.search);
  if (params.date_from != null && params.date_from !== '') searchParams.set('date_from', params.date_from);
  if (params.date_to != null && params.date_to !== '') searchParams.set('date_to', params.date_to);
  if (params.assigned_user != null && params.assigned_user !== '') searchParams.set('assigned_user', params.assigned_user);
  if (params.violator_filter != null && params.violator_filter !== '') searchParams.set('violator_filter', params.violator_filter);
  if (params.status != null && Array.isArray(params.status)) {
    params.status.forEach((s) => searchParams.append('status', s));
  }
  if (params.department_filter != null && Array.isArray(params.department_filter)) {
    params.department_filter.forEach((d) => searchParams.append('department_filter', d));
  }
  if (params.only_overdue === true) searchParams.set('only_overdue', 'on');
  const qs = searchParams.toString();
  return request(`/builder/incidents/detail/${qs ? `?${qs}` : ''}`);
}

/**
 * Отменить назначение пользователя на инцидент. POST.
 * @param {number} incidentId — ID инцидента
 * @param {number} userId — ID пользователя
 * @returns {Promise<{ success: boolean }>}
 */
export function unassignIncidentUser(incidentId, userId) {
  return request(`/builder/incidents/${incidentId}/unassign-user/${userId}/`, {
    method: 'POST',
    body: JSON.stringify({}),
  });
}

/**
 * Отчёт по инцидентам: статистика по пользователям (назначено, просрочено, завершено, обучение завершено).
 * @param {Object} params — date_from, date_to, department_filter
 * @returns {Promise<{ date_from: string, date_to: string, department_filter: string, departments: Array<{ name: string }>, report_data: Array<{ full_name, department, assigned_count, overdue_count, resolved_count, studies_completed_count }> }>}
 */
export function fetchIncidentStatusesReport(params = {}) {
  const searchParams = new URLSearchParams();
  if (params.date_from != null && params.date_from !== '') searchParams.set('date_from', params.date_from);
  if (params.date_to != null && params.date_to !== '') searchParams.set('date_to', params.date_to);
  if (params.department_filter != null && params.department_filter !== '') searchParams.set('department_filter', params.department_filter);
  const qs = searchParams.toString();
  return request(`/builder/incidents/statuses-report/${qs ? `?${qs}` : ''}`);
}

// ---------------------------------------------------------------------------
// Форма создания/редактирования инцидента
// ---------------------------------------------------------------------------

/**
 * Данные для формы инцидента: choices и при pk — данные инцидента для редактирования.
 * @param {number|null} [pk] — ID инцидента для режима редактирования
 * @returns {Promise<{ incident_type_choices, status_choices, defaults, incident?: object }>}
 */
export function fetchIncidentFormData(pk = null) {
  const url = pk != null ? `/builder/incidents/form/data/?pk=${pk}` : '/builder/incidents/form/data/';
  return request(url);
}

/**
 * Создание инцидента. POST.
 * @param {Object} data — title, incident_type, user_id, responsible_mentor_id, mentors_time_to_check, assigned_to_ids[], violators_ids[], expert_id, assigned_to_time_to_complete, expert_time_to_complete, description
 * @returns {Promise<{ id: number, redirect_url: string }>}
 */
export function createIncident(data) {
  return request('/builder/incidents/create/', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/**
 * Обновление инцидента. PUT.
 * @param {number} pk — ID инцидента
 * @param {Object} data — те же поля, что и для создания
 * @returns {Promise<{ id: number, success: boolean }>}
 */
export function updateIncident(pk, data) {
  return request(`/builder/incidents/${pk}/edit/`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

/**
 * Создание курса-инцидента из инцидента. POST.
 * @param {number} pk — ID инцидента
 * @returns {Promise<{ redirect_url: string }>}
 */
export function createIncidentCourse(pk) {
  return request(`/builder/incidents/${pk}/create-course/`, {
    method: 'POST',
    body: JSON.stringify({}),
  });
}

/**
 * Поиск пользователей (для полей user, mentor, expert, assigned).
 * @param {string} q — поисковый запрос
 * @param {Object} [opts] — mentor_only: только наставники; exclude_staff: исключить staff
 * @returns {Promise<{ users: Array<{ id, full_name, username, role? }> }>}
 */
export function searchUsers(q, opts = {}) {
  const params = new URLSearchParams();
  if (q != null && q !== '') params.set('q', q);
  if (opts.mentor_only === true) params.set('mentor_only', 'true');
  if (opts.exclude_staff === true) params.set('exclude_staff', 'true');
  const qs = params.toString();
  return request(`/builder/users/search/${qs ? `?${qs}` : ''}`);
}

/**
 * Получение пользователей по списку ID.
 * @param {number[]|string} ids — массив ID или строка через запятую
 * @returns {Promise<{ users: Array<{ id, full_name, username }> }>}
 */
export function getUsersByIds(ids) {
  const idList = Array.isArray(ids) ? ids : String(ids).split(',').map((s) => s.trim()).filter(Boolean);
  if (idList.length === 0) return Promise.resolve({ users: [] });
  const params = new URLSearchParams({ ids: idList.join(',') });
  return request(`/builder/users/by-ids/?${params.toString()}`);
}

/**
 * Список групп.
 * @param {Object} [opts] — exclude_staff: исключить staff из подсчёта
 * @returns {Promise<{ groups: Array<{ id, name, user_count }> }>}
 */
export function getGroups(opts = {}) {
  const params = new URLSearchParams();
  if (opts.exclude_staff !== false) params.set('exclude_staff', 'true');
  const qs = params.toString();
  return request(`/builder/groups/${qs ? `?${qs}` : ''}`);
}

/**
 * Пользователи группы.
 * @param {number} groupId
 * @param {Object} [opts] — exclude_staff
 * @returns {Promise<{ users: Array<{ id, full_name, username }> }>}
 */
export function getGroupUsers(groupId, opts = {}) {
  const params = new URLSearchParams();
  if (opts.exclude_staff === true) params.set('exclude_staff', 'true');
  const qs = params.toString();
  return request(`/builder/groups/${groupId}/users/${qs ? `?${qs}` : ''}`);
}
