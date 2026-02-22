import { request } from './api';

/**
 * Список сертификатов текущего пользователя (по курсам и траекториям).
 * @returns {Promise<{ course_certificates: Array, trajectory_certificates: Array, total_count: number }>}
 */
export function fetchUserCertificates() {
  return request('/courses/user-certificates/');
}
