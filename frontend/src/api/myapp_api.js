import { request } from './api'

/**
 * Получает список записей истории изменений с пагинацией.
 * @param {number} page - Номер страницы (по умолчанию 1)
 * @returns {Promise<{items: Array, pagination: object}>}
 */
export function fetchChangelogList(page = 1) {
  const params = new URLSearchParams({ page: page.toString() });
  return request(`/myapp/changelog/?${params.toString()}`);
}
