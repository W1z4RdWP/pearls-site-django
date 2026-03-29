import { request } from './api';

/**
 * Число непрочитанных уведомлений.
 */
export function fetchNotificationCount() {
  return request('/notifications/count/');
}

/**
 * Последние уведомления для выпадающего списка.
 */
export function fetchNotificationsDropdown() {
  return request('/notifications/dropdown/');
}

/**
 * Отметить все уведомления прочитанными (как при открытии dropdown в layout.html).
 */
export function markAllNotificationsRead() {
  return request('/notifications/mark-all-read/', {
    method: 'POST',
    body: JSON.stringify({}),
  });
}
