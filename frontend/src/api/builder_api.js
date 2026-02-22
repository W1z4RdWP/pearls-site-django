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
