import { request, getCSRFToken, API_BASE } from './api'


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

/**
 * Создание пользователя (шаг 1) - email и пароль.
 * @param {string} email — email пользователя
 * @param {string} password1 — пароль
 * @param {string} password2 — подтверждение пароля
 * @returns {Promise<{success: boolean, user_id: number, message: string, errors?: object}>}
 */
export function createUserStep1(email, password1, password2) {
  return request('/user_management/users/add/step1/', {
    method: 'POST',
    body: JSON.stringify({ email, password1, password2 }),
  });
}

/**
 * Получение данных для шага 2 (роли, группы, текущие данные пользователя).
 * @returns {Promise<{roles: Array, groups: Array, user: object, profile: object}>}
 */
export function fetchUserCreateStep2Data() {
  return request('/user_management/users/add/step2/data/');
}

/**
 * Создание профиля пользователя (шаг 2).
 * @param {object} profileData — данные профиля
 * @param {File} [imageFile] — файл изображения (опционально)
 * @returns {Promise<{success: boolean, user_id: number, email_sent: boolean, message: string, errors?: object}>}
 */
export function createUserStep2(profileData, imageFile = null) {
  const formData = new FormData();
  
  // Добавляем все поля профиля
  Object.keys(profileData).forEach(key => {
    const value = profileData[key];
    if (value !== null && value !== undefined) {
      if (key === 'groups' && Array.isArray(value)) {
        // Группы передаём как JSON строку
        formData.append(key, JSON.stringify(value));
      } else {
        formData.append(key, value);
      }
    }
  });
  
  // Добавляем файл изображения, если есть
  if (imageFile) {
    formData.append('image', imageFile);
  }
  
  // Используем fetch напрямую для FormData
  return fetch(`${API_BASE}/user_management/users/add/step2/`, {
    method: 'POST',
    credentials: 'include',
    headers: {
      'X-CSRFToken': getCSRFToken(),
    },
    body: formData,
  })
    .then(response => {
      if (!response.ok) {
        return response.json().then(errorData => {
          throw new Error(errorData.error || `HTTP ${response.status}`);
        });
      }
      return response.json();
    });
}

/**
 * Получение данных пользователя для редактирования.
 * @param {number} userId — ID пользователя
 * @returns {Promise<{user: object, profile: object, roles: Array, groups: Array}>}
 */
export function fetchUserEditData(userId) {
  return request(`/user_management/users/${userId}/edit/data/`);
}

/**
 * Обновление пользователя.
 * @param {number} userId — ID пользователя
 * @param {object} userData — данные пользователя
 * @param {File} [imageFile] — файл изображения (опционально)
 * @returns {Promise<{success: boolean, user_id: number, message: string, errors?: object}>}
 */
export function updateUser(userId, userData, imageFile = null) {
  const formData = new FormData();
  
  // Добавляем все поля
  Object.keys(userData).forEach(key => {
    const value = userData[key];
    if (value !== null && value !== undefined) {
      if (key === 'groups' && Array.isArray(value)) {
        formData.append(key, JSON.stringify(value));
      } else {
        formData.append(key, value);
      }
    }
  });
  
  // Добавляем файл изображения, если есть
  if (imageFile) {
    formData.append('image', imageFile);
  }
  
  return fetch(`${API_BASE}/user_management/users/${userId}/edit/`, {
    method: 'POST',
    credentials: 'include',
    headers: {
      'X-CSRFToken': getCSRFToken(),
    },
    body: formData,
  })
    .then(response => {
      if (!response.ok) {
        return response.json().then(errorData => {
          throw new Error(errorData.error || `HTTP ${response.status}`);
        });
      }
      return response.json();
    });
}

/**
 * Создание новой должности.
 * @param {string} name — название должности
 * @returns {Promise<{success: boolean, role: object, message: string}>}
 */
export function createRole(name) {
  return request('/user_management/roles/create/', {
    method: 'POST',
    body: JSON.stringify({ name }),
  });
}

/**
 * Обновление должности.
 * @param {number} roleId — ID должности
 * @param {string} name — новое название
 * @returns {Promise<{success: boolean, role: object, message: string}>}
 */
export function updateRole(roleId, name) {
  return request(`/user_management/roles/${roleId}/update/`, {
    method: 'POST',
    body: JSON.stringify({ name }),
  });
}

/**
 * Удаление должности.
 * @param {number} roleId — ID должности
 * @returns {Promise<{success: boolean, message: string}>}
 */
export function deleteRole(roleId) {
  return request(`/user_management/roles/${roleId}/delete/`, {
    method: 'POST',
    body: JSON.stringify({}),
  });
}

/**
 * Назначение ответственного за должность.
 * @param {number} roleId — ID должности
 * @param {number|null} responsibleId — ID пользователя (null для снятия ответственности)
 * @returns {Promise<{success: boolean, message: string}>}
 */
export function setRoleResponsible(roleId, responsibleId) {
  return request(`/user_management/roles/${roleId}/set-responsible/`, {
    method: 'POST',
    body: JSON.stringify({ responsible_id: responsibleId }),
  });
}

/**
 * Получение списка пользователей с данной ролью.
 * @param {number} roleId — ID должности
 * @returns {Promise<{users: Array}>}
 */
export function fetchRoleUsers(roleId) {
  return request(`/user_management/roles/${roleId}/users/`);
}

/**
 * Смена пароля пользователя (только для staff/superuser).
 * @param {number} userId — ID пользователя
 * @param {string} newPassword1 — новый пароль
 * @param {string} newPassword2 — подтверждение нового пароля
 * @returns {Promise<{success: boolean, message: string, errors?: object}>}
 */
export function changeUserPassword(userId, newPassword1, newPassword2) {
  return request(`/user_management/users/${userId}/password/`, {
    method: 'POST',
    body: JSON.stringify({ new_password1: newPassword1, new_password2: newPassword2 }),
  });
}

/**
 * Административная панель статистики пользователей по баллам DASCOIN (staff/superuser/mentor).
 * @param {number} [page=1] — номер страницы
 * @param {string} [group=''] — ID группы для фильтрации
 * @param {string} [role=''] — ID должности для фильтрации
 * @param {string} [points_min=''] — минимальное количество баллов
 * @param {string} [points_max=''] — максимальное количество баллов
 * @param {boolean} [zero_points=false] — фильтр по нулевым баллам
 * @param {boolean} [approved_only=true] — фильтр по подтвержденным пользователям
 * @param {boolean} [show_all=false] — показать всех пользователей
 * @param {number} [top=null] — показать топ-N пользователей
 * @returns {Promise<{users: Array, total_spent_points: number, total_dascoin_points: number, last_award_date: string, groups: Array, roles: Array, pagination: object}>}
 */
export function fetchAdminDascoinDashboard(page = 1, filters = {}) {
  const params = new URLSearchParams({ page: String(page) });
  if (filters.group) params.set('group', filters.group);
  if (filters.role) params.set('role', filters.role);
  if (filters.points_min) params.set('points_min', filters.points_min);
  if (filters.points_max) params.set('points_max', filters.points_max);
  if (filters.zero_points) params.set('zero_points', '1');
  if (filters.approved_only) params.set('approved', '1');
  if (filters.show_all) params.set('show_all', '1');
  if (filters.top) params.set('top', String(filters.top));
  return request(`/user_management/admin/dascoin_dashboard/?${params.toString()}`);
}

/**
 * История транзакций DASCOIN конкретного пользователя (staff/superuser).
 * @param {number} userId — ID пользователя
 * @param {number} [page=1] — номер страницы
 * @param {string} [type=''] — фильтр по типу транзакции (award, deduct, set, correction)
 * @returns {Promise<{user: object, transactions: Array, total_transactions: number, current_filter: string, stats: object, pagination: object}>}
 */
export function fetchAdminUserTransactions(userId, page = 1, type = '') {
  const params = new URLSearchParams({ page: String(page) });
  if (type && type.trim()) params.set('type', type.trim());
  return request(`/user_management/admin/user/${userId}/transactions/?${params.toString()}`);
}