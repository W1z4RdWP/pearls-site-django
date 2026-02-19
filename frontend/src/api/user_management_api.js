import { request, getCSRFToken } from './api'


// ——— User Management API ———

/**
 * Список пользователей с фильтрацией и пагинацией (staff/superuser/mentor).
 * @param {number} [page=1] — номер страницы
 * @param {string} [q=''] — поисковый запрос (имя, email)
 * @param {string} [filter='approved'] — фильтр по статусу (approved, not_approved, responsible, not_responsible)
 * @param {string} [group=''] — ID группы для фильтрации
 * @param {boolean} [exclude_external=true] — исключить внешних пользователей
 * @returns {Promise<{users: Array, groups: Array, is_mentor_only: boolean, exclude_external_checked: boolean, pagination: object, filters: object}>}
 */
export function fetchUserList(page = 1, q = '', filter = 'approved', group = '', exclude_external = true) {
    const params = new URLSearchParams({ page: String(page) });
    if (q && q.trim()) params.set('q', q.trim());
    if (filter) params.set('filter', filter);
    if (group) params.set('group', group);
    if (exclude_external) {
      params.append('exclude_external', '1');
    } else {
      params.append('exclude_external', '0');
    }
    return request(`/user_management/users/?${params.toString()}`);
  }