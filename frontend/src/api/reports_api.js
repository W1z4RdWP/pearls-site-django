import { request } from './api';

/**
 * Данные дашборда «Проверка заданий»: статистика и последние завершения (для наставников/staff).
 * @returns {Promise<{ total_materials: number, total_lessons: number, total_quizzes: number, total_homeworks: number, active_users: number, total_groups: number, is_admin: boolean, recent_completions: Array, pending_tests_count: number }>}
 */
export function fetchHomeworkCheckDashboard() {
  return request('/reports/homework-check-dashboard/');
}
