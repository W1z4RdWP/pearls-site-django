/**
 * API-клиент для взаимодействия с Django backend.
 * Использует fetch API, CSRF-токен из cookie.
 */

const API_BASE = '/api';

/**
 * Получает CSRF-токен из cookie.
 */
function getCSRFToken() {
  const cookies = document.cookie.split(';');
  for (const cookie of cookies) {
    const [name, value] = cookie.trim().split('=');
    if (name === 'csrftoken') {
      return value;
    }
  }
  return '';
}

/**
 * Универсальная обёртка для fetch-запросов.
 */
async function request(url, options = {}) {
  const defaultHeaders = {
    'Content-Type': 'application/json',
    'X-CSRFToken': getCSRFToken(),
  };

  const config = {
    credentials: 'include',
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  };

  const response = await fetch(`${API_BASE}${url}`, config);

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || `HTTP ${response.status}`);
  }

  return response.json();
}

/**
 * Получает данные для Layout (user, nav, version).
 */
export function fetchLayoutData() {
  return request('/frontend/layout/');
}

/**
 * Получает список курсов для главной страницы.
 */
export function fetchHomeCourses() {
  return request('/frontend/courses/');
}

/**
 * Авторизация пользователя.
 * @param {string} username — логин или email
 * @param {string} password — пароль
 * @returns {Promise<{success: boolean, user: object, is_external: boolean}>}
 */
export function loginUser(username, password) {
  return request('/frontend/login/', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  });
}

/**
 * Выход пользователя.
 * @returns {Promise<{success: boolean}>}
 */
export function logoutUser() {
  return request('/frontend/logout/', {
    method: 'POST',
    body: JSON.stringify({}),
  });
}
