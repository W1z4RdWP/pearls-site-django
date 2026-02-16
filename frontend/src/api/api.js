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

// ——— Shop API (бэкенд отдаёт данные по /api/shop/...) ———

/**
 * Список товаров магазина.
 * @returns {Promise<{products: Array}>}
 */
export function fetchShopProducts() {
  return request('/shop/products/');
}

/**
 * Детали товара по ID.
 * @param {number} productId
 * @returns {Promise<{product: object}>}
 */
export function fetchProductDetails(productId) {
  return request(`/shop/product/details/?product_id=${productId}`);
}

/**
 * Оформить заказ товара.
 * @param {number} productId
 * @returns {Promise<{success: boolean, order_id: number, points_spent: number}>}
 */
export function orderProduct(productId) {
  return request('/shop/order/', {
    method: 'POST',
    body: JSON.stringify({ product_id: productId }),
  });
}

/**
 * Количество заказов пользователя (для бейджа корзины).
 * @returns {Promise<{count: number}>}
 */
export function fetchOrdersCount() {
  return request('/shop/orders/count/');
}

/**
 * История заказов пользователя (с пагинацией и статистикой).
 * @param {number} [page=1] — номер страницы
 * @returns {Promise<{orders: Array, stats: {total: number, pending: number}, total_points_spent: number, total_points_refunded: number, pagination: object}>}
 */
export function fetchOrderHistory(page = 1) {
  return request(`/shop/orders/history/?page=${page}`);
}

/**
 * Пользователи с покупками (только staff/superuser). Поиск и пагинация.
 * @param {number} [page=1] — номер страницы
 * @param {string} [q=''] — поисковый запрос (имя, email, username)
 * @returns {Promise<{users: Array, total_users: number, total_orders: number, total_points_spent: number, search_query: string, pagination: object}>}
 */
export function fetchUsersWithOrders(page = 1, q = '') {
  const params = new URLSearchParams({ page: String(page) });
  if (q && q.trim()) params.set('q', q.trim());
  return request(`/shop/admin/users/?${params.toString()}`);
}

/**
 * История заказов пользователя (админ, staff/superuser). Пагинация.
 * @param {number} userId — ID пользователя
 * @param {number} [page=1] — номер страницы
 * @returns {Promise<{target_user: object, orders: Array, stats: object, total_points_spent: number, total_points_refunded: number, pagination: object}>}
 */
export function fetchUserOrdersAdmin(userId, page = 1) {
  return request(`/shop/admin/user/${userId}/orders/?page=${page}`);
}

/**
 * Создание товара (staff/superuser). FormData: name, description, points_price, constraints, restrictions_text, image, is_active.
 * @param {FormData} formData
 * @returns {Promise<{success: boolean, product: object}>}
 */
export function createProduct(formData) {
  const config = {
    method: 'POST',
    credentials: 'include',
    headers: {
      'X-CSRFToken': getCSRFToken(),
    },
    body: formData,
  };
  return fetch(`${API_BASE}/shop/product/create/`, config).then(async (response) => {
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      const err = new Error(data.error || `HTTP ${response.status}`);
      err.errors = data.errors;
      throw err;
    }
    return data;
  });
}

/**
 * Данные дашборда (панель управления): топ пользователей по DASCOIN (для наставников)
 * или неоценённые открытые ответы (для админов/staff).
 * @returns {Promise<{top_users_dascoin: Array, total_unrated_count: number, unrated_text_answers: Array}>}
 */
export function fetchDashboardData() {
  return request('/builder/dashboard/');
}

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