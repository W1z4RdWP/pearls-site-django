import { request } from './api'

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