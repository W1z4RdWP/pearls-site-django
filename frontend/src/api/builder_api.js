import { request } from './api';

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
