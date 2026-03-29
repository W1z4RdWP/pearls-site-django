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

/**
 * Список уведомлений (фильтры, поиск, пагинация).
 * @param {{ page?: number, type?: string, search?: string }} params
 */
export function fetchNotificationsList({ page = 1, type = '', search = '' } = {}) {
  const q = new URLSearchParams();
  if (page > 1) {
    q.set('page', String(page));
  }
  if (type) {
    q.set('type', type);
  }
  if (search) {
    q.set('search', search);
  }
  const qs = q.toString();
  return request(qs ? `/notifications/?${qs}` : '/notifications/');
}

export function markNotificationRead(notificationId) {
  return request(`/notifications/${notificationId}/mark-read/`, {
    method: 'POST',
    body: JSON.stringify({}),
  });
}

export function deleteNotification(notificationId) {
  return request(`/notifications/${notificationId}/delete/`, {
    method: 'POST',
    body: JSON.stringify({}),
  });
}

export function clearOldNotifications() {
  return request('/notifications/clear-old/', {
    method: 'POST',
    body: JSON.stringify({}),
  });
}
