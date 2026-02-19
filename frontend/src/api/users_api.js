import { request, getCSRFToken } from "./api";

/**
 * Данные текущего пользователя (краткие, для navbar и т.п.).
 */
export function fetchUserData() {
    return request('/users/user_info/');
  }
  
  /**
   * Полные данные для страницы профиля (профиль, бейджи, достижения, группы).
   * @returns {Promise<object>}
   */
  export function fetchProfilePageData() {
    return request('/users/profile/');
  }
  
  /**
   * Обновление профиля пользователя.
   * @param {FormData|object} data - Данные для обновления (first_name, last_name, middle_name, date_of_birth, image, bio)
   * @returns {Promise<object>} - Обновленные данные профиля
   */
  export function updateProfile(data) {
    // Если data - это FormData (с файлом), используем multipart/form-data
    if (data instanceof FormData) {
      const config = {
        method: 'POST',
        credentials: 'include',
        headers: {
          'X-CSRFToken': getCSRFToken(),
          // Не устанавливаем Content-Type для FormData - браузер сам установит с boundary
        },
        body: data,
      };
      
      return fetch(`${API_BASE}/users/profile/update/`, config)
        .then(async (response) => {
          if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || `HTTP ${response.status}`);
          }
          return response.json();
        });
    }
    
    // Иначе отправляем как JSON
    return request('/users/profile/update/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }
  
  // ——— Users API: транзакции DASCOIN ———
  
  /**
   * История транзакций DASCOIN текущего пользователя (фильтрация, пагинация, статистика).
   * @param {number} [page=1] — номер страницы
   * @param {string} [type=''] — фильтр по типу транзакции (award, deduct, set, correction)
   * @returns {Promise<{transactions: Array, total_transactions: number, current_filter: string, stats: object, pagination: object}>}
   */
  export function fetchTransactions(page = 1, type = '') {
    const params = new URLSearchParams({ page: String(page) });
    if (type && type.trim()) params.set('type', type.trim());
    return request(`/users/transactions/?${params.toString()}`);
  }
  
  /**
   * Все бейджи пользователя.
   * @returns {Promise<{badges: Array, stats: {total_received: number, total_available: number, progress_percent: number}}>}
   */
  export function fetchAllBadges() {
    return request('/users/profile/all-badges/');
  }
  
  /**
   * Все достижения пользователя.
   * @returns {Promise<{achievements: Array, stats: {total_received: number}}>}
   */
  export function fetchAllAchievements() {
    return request('/users/profile/all-achievements/');
  }
  
  /**
   * Смена пароля текущего пользователя (требует старый пароль).
   * @param {string} oldPassword — текущий пароль
   * @param {string} newPassword1 — новый пароль
   * @param {string} newPassword2 — подтверждение нового пароля
   * @returns {Promise<{success: boolean, message: string, errors?: object}>}
   */
  export function changePassword(oldPassword, newPassword1, newPassword2) {
    return request('/users/password_change/', {
      method: 'POST',
      body: JSON.stringify({ 
        old_password: oldPassword, 
        new_password1: newPassword1, 
        new_password2: newPassword2 
      }),
    });
  }