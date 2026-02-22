import { request } from './api';

/**
 * Данные страницы «Управление траекториями»: статистика, последние уроки/курсы/траектории/тесты, группы, URL.
 * Только для staff/superuser.
 * @returns {Promise<{ total_lessons, total_courses, total_incident_courses, total_trajectories, total_quizzes, recent_lessons, recent_courses, recent_trajectories, recent_quizzes, all_groups, urls }>}
 */
export function fetchTrajectoryManagementData() {
  return request('/builder/trajectory-management/');
}
