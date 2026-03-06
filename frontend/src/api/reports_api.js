import { request } from './api';

/**
 * Данные дашборда «Проверка заданий»: статистика и последние завершения (для наставников/staff).
 * @returns {Promise<{ total_materials: number, total_lessons: number, total_quizzes: number, total_homeworks: number, active_users: number, total_groups: number, is_admin: boolean, recent_completions: Array, pending_tests_count: number }>}
 */
export function fetchHomeworkCheckDashboard() {
  return request('/reports/homework-check-dashboard/');
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
