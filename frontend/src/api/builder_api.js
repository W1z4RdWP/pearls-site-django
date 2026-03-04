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
