import { request } from './api';

/**
 * Список траекторий пользователя и прогресс по курсам (все курсы без серверной фильтрации).
 * @returns {Promise<{ user_trajectories: Array, courses_data: Array, ...stats }>}
 */
export function fetchTrajectoryList() {
  return request('/courses/trajectories/');
}

/**
 * Список сертификатов текущего пользователя (по курсам и траекториям).
 * @returns {Promise<{ course_certificates: Array, trajectory_certificates: Array, total_count: number }>}
 */
export function fetchUserCertificates() {
  return request('/courses/user-certificates/');
}
