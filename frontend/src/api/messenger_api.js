import { request, getCSRFToken } from './api'

/**
 * Получает список комнат чата для текущего пользователя.
 * @returns {Promise<{chat_rooms: Array}>}
 */
export function fetchChatRooms() {
  return request('/messenger/chat_rooms/');
}

/**
 * Создает новую комнату чата.
 * @param {string} name - Название комнаты (необязательно)
 * @returns {Promise<{success: boolean, chat_room: object}>}
 */
export function createChatRoom(name = '') {
  return request('/messenger/chat_room/create/', {
    method: 'POST',
    body: JSON.stringify({ name }),
  });
}

/**
 * Получает данные комнаты чата (информация о комнате, сообщения, участники, статус уведомлений).
 * @param {string} roomId - ID комнаты
 * @returns {Promise<{room: object, messages: Array, messages_by_date: object, notifications_enabled: boolean, is_creator: boolean, current_user_id: number, current_user_name: string, current_user_avatar: string, current_user_initials: string}>}
 */
export function fetchChatRoomData(roomId) {
  return request(`/messenger/chat_room/${roomId}/`);
}

/**
 * Загружает файлы и отправляет сообщение с вложениями.
 * @param {string} roomId - ID комнаты
 * @param {string} message - Текст сообщения
 * @param {File[]} files - Массив файлов для загрузки
 * @param {Function} onProgress - Callback для отслеживания прогресса загрузки
 * @returns {Promise<{success: boolean, message_id: number, message: string, attachments: Array}>}
 */
export function uploadChatAttachment(roomId, message, files, onProgress) {
  const formData = new FormData();
  formData.append('message', message);
  files.forEach(file => {
    formData.append('files', file);
  });

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();

    if (onProgress) {
      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
          onProgress(Math.round((e.loaded / e.total) * 100));
        }
      });
    }

    xhr.onload = function() {
      if (xhr.status === 200) {
        try {
          const response = JSON.parse(xhr.responseText);
          resolve(response);
        } catch (e) {
          reject(new Error('Ошибка парсинга ответа'));
        }
      } else {
        try {
          const error = JSON.parse(xhr.responseText);
          reject(new Error(error.error || 'Ошибка загрузки'));
        } catch (e) {
          reject(new Error(`HTTP ${xhr.status}`));
        }
      }
    };

    xhr.onerror = function() {
      reject(new Error('Ошибка сети при загрузке файлов'));
    };

    // Используем прямой путь к Django endpoint
    xhr.open('POST', `/messenger/chat/room/${roomId}/upload/`);
    xhr.setRequestHeader('X-CSRFToken', getCSRFToken());
    xhr.send(formData);
  });
}

/**
 * Получает список участников комнаты.
 * @param {string} roomId - ID комнаты
 * @returns {Promise<{participants: Array, is_creator: boolean}>}
 */
export function fetchRoomParticipants(roomId) {
  return fetch(`/messenger/chat/room/${roomId}/participants/`, {
    credentials: 'include',
  }).then(async (response) => {
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(data.error || `HTTP ${response.status}`);
    }
    return data;
  });
}

/**
 * Добавляет участника в комнату (только для создателя).
 * @param {string} roomId - ID комнаты
 * @param {number} userId - ID пользователя для добавления
 * @returns {Promise<{success: boolean, user: object}>}
 */
export function addRoomParticipant(roomId, userId) {
  const formData = new FormData();
  formData.append('user_id', userId);

  return fetch(`/messenger/chat/room/${roomId}/participants/add/`, {
    method: 'POST',
    credentials: 'include',
    headers: {
      'X-CSRFToken': getCSRFToken(),
    },
    body: formData,
  }).then(async (response) => {
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(data.error || `HTTP ${response.status}`);
    }
    return data;
  });
}

/**
 * Ищет пользователей для добавления в комнату (только для создателя).
 * @param {string} roomId - ID комнаты
 * @param {string} query - Поисковый запрос
 * @returns {Promise<{users: Array}>}
 */
export function searchUsersForRoom(roomId, query) {
  return fetch(`/messenger/chat/room/${roomId}/search-users/?q=${encodeURIComponent(query)}`, {
    credentials: 'include',
  }).then(async (response) => {
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(data.error || `HTTP ${response.status}`);
    }
    return data;
  });
}

/**
 * Переключает уведомления для комнаты.
 * @param {string} roomId - ID комнаты
 * @returns {Promise<{success: boolean, notifications_enabled: boolean}>}
 */
export function toggleRoomNotifications(roomId) {
  return request(`/messenger/chat/room/${roomId}/notifications/toggle/`, {
    method: 'POST',
  });
}

/**
 * Получает статус уведомлений для комнаты.
 * @param {string} roomId - ID комнаты
 * @returns {Promise<{notifications_enabled: boolean}>}
 */
export function getRoomNotificationStatus(roomId) {
  return fetch(`/messenger/chat/room/${roomId}/notifications/status/`, {
    credentials: 'include',
  }).then(async (response) => {
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(data.error || `HTTP ${response.status}`);
    }
    return data;
  });
}

/**
 * Отправляет текстовое сообщение в комнату чата.
 * @param {string} roomId - ID комнаты
 * @param {string} message - Текст сообщения
 * @returns {Promise<{success: boolean, message_id: number, message: string, timestamp: string}>}
 */
export function sendChatMessage(roomId, message) {
  return request(`/messenger/chat_room/${roomId}/send/`, {
    method: 'POST',
    body: JSON.stringify({ message }),
  });
}