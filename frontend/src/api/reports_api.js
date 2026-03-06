import { request } from './api';

/**
 * Данные дашборда «Проверка заданий»: статистика и последние завершения (для наставников/staff).
 * @returns {Promise<{ total_materials: number, total_lessons: number, total_quizzes: number, total_homeworks: number, active_users: number, total_groups: number, is_admin: boolean, recent_completions: Array, pending_tests_count: number }>}
 */
export function fetchHomeworkCheckDashboard() {
  return request('/reports/homework-check-dashboard/');
}

/**
 * Пользователи с назначенным обучением: статистика, группы, фильтры, пагинация.
 * @param {Object} params - { page?: number, search?: string, group?: string }
 * @returns {Promise<{ is_admin: boolean, groups: Array<{id, name}>, search_query: string, selected_group: string, learning_percentage: number, completed_courses: number, in_progress_courses: number, available_courses: number, total_courses: number, learning_data: Array<{label, value, color}>, users: Array, pagination: Object }>}
 */
export function fetchUsersWithLearning(params = {}) {
  const searchParams = new URLSearchParams();
  if (params.page != null) searchParams.set('page', String(params.page));
  if (params.search != null && params.search !== '') searchParams.set('search', params.search);
  if (params.group != null && params.group !== '') searchParams.set('group', params.group);
  const qs = searchParams.toString();
  const path = qs ? `/reports/users-with-learning/?${qs}` : '/reports/users-with-learning/';
  return request(path);
}

/**
 * Отчёт по прогрессу курсов: список курсов с процентами завершения (пагинация, поиск).
 * @param {Object} params - { page?: number, search?: string }
 * @returns {Promise<{ total_courses: number, overall_learning_percentage: number, completed_assignments_total: number, in_progress_assignments_total: number, available_assignments_total: number, search_query: string, items: Array, pagination: Object }>}
 */
export function fetchCoursesProgress(params = {}) {
  const searchParams = new URLSearchParams();
  if (params.page != null) searchParams.set('page', String(params.page));
  if (params.search != null && params.search !== '') searchParams.set('search', params.search);
  const qs = searchParams.toString();
  const path = qs ? `/reports/courses-progress/?${qs}` : '/reports/courses-progress/';
  return request(path);
}

/**
 * Прогресс групп: список групп с обученностью, фильтр по группе, общая статистика.
 * @param {Object} params - { group?: string } — ID группы для фильтра
 * @returns {Promise<{ is_admin: boolean, all_available_groups: Array<{id: number, name: string}>, selected_group: string, groups: Array, total_courses: number, completed_courses: number, in_progress_courses: number, available_courses: number, overall_learning_percentage: number, learning_data: Array }>}
 */
export function fetchGroupsProgress(params = {}) {
  const searchParams = new URLSearchParams();
  if (params.group != null && params.group !== '') searchParams.set('group', String(params.group));
  const qs = searchParams.toString();
  const path = qs ? `/reports/groups-progress/?${qs}` : '/reports/groups-progress/';
  return request(path);
}

/**
 * Детальная страница назначений по курсу: пользователи и статусы (пагинация).
 * @param {number} courseId - ID курса
 * @param {Object} params - { page?: number }
 * @returns {Promise<{ course: { id, title }, total_assignments, completed_assignments, in_progress_assignments, available_assignments, blocked_assignments, learning_percentage, items: Array, pagination: Object }>}
 */
export function fetchCourseAssignmentsDetail(courseId, params = {}) {
  const searchParams = new URLSearchParams();
  if (params.page != null) searchParams.set('page', String(params.page));
  const qs = searchParams.toString();
  const path = qs ? `/reports/courses-progress/${courseId}/?${qs}` : `/reports/courses-progress/${courseId}/`;
  return request(path);
}

/**
 * Прогресс студентов группы: список студентов с курсами и процентами (пагинация).
 * @param {number} groupId - ID группы
 * @param {Object} params - { page?: number }
 * @returns {Promise<{ group: { id, name }, items: Array, pagination: Object }>}
 */
export function fetchGroupStudentsProgress(groupId, params = {}) {
  const searchParams = new URLSearchParams();
  if (params.page != null) searchParams.set('page', String(params.page));
  const qs = searchParams.toString();
  const path = qs ? `/reports/groups/${groupId}/students-progress/?${qs}` : `/reports/groups/${groupId}/students-progress/`;
  return request(path);
}
