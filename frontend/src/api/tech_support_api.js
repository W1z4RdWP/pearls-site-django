import { request, API_BASE, getCSRFToken } from './api';

/**
 * Создаёт тикет обращения в поддержку.
 * @param {object} payload — { ticket_type, title, description, attachments?: File[] }
 * @returns {Promise<{ ticket_id: number, ticket_number: string, ticket_detail_url: string }>}
 */
export function createTicket(payload) {
  const files = payload.attachments || [];
  if (files.length === 0) {
    return request('/tech_support/chat/', {
      method: 'POST',
      body: JSON.stringify({
        ticket_type: payload.ticket_type,
        title: payload.title,
        description: payload.description,
      }),
    });
  }

  const formData = new FormData();
  formData.append('ticket_type', payload.ticket_type);
  formData.append('title', payload.title);
  formData.append('description', payload.description);
  files.forEach((file) => formData.append('attachments', file));

  return fetch(`${API_BASE}/tech_support/chat/`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'X-CSRFToken': getCSRFToken() },
    body: formData,
  }).then(async (response) => {
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      const err = new Error(data.error || `HTTP ${response.status}`);
      if (data.errors) err.errors = data.errors;
      throw err;
    }
    return data;
  });
}

/**
 * Список тикетов текущего пользователя (мои тикеты).
 * @returns {Promise<{ tickets: Array }>}
 */
export function fetchMyTicketList() {
  return request('/tech_support/my/tickets/');
}

/**
 * Список тикетов для staff (с фильтрами по GET).
 * @param {object} params — { status?, priority?, ticket_type?, search?, date_from?, date_to? }
 * @returns {Promise<{ tickets: Array }>}
 */
export function fetchTicketListStaff(params = {}) {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value != null && value !== '') searchParams.set(key, value);
  });
  const query = searchParams.toString();
  return request(`/tech_support/tickets/${query ? `?${query}` : ''}`.trim());
}

/**
 * Проверка наличия новых тикетов (только staff/superuser).
 * @returns {Promise<{ count: number, has_new: boolean }>}
 */
export function fetchNewTicketsCount() {
  return request('/tech_support/new-tickets-count/');
}

/**
 * Данные дашборда поддержки для staff.
 * @returns {Promise<{ total_tickets, active_tickets, resolved_tickets, overdue_tickets, priority_stats, type_stats, avg_rating, recent_tickets, overdue_tickets_list, status_in_progress_id }>}
 */
export function fetchStaffDashboard() {
  return request('/tech_support/dashboard/');
}

/**
 * Отчёты по тикетам за период.
 * @param {string} period — 'week' | 'month' | 'year'
 * @returns {Promise<{ period, tickets_by_period, performer_stats, avg_resolution_time, avg_rating, total_resolved }>}
 */
export function fetchTicketReports(period = 'month') {
  return request(`/tech_support/reports/?period=${encodeURIComponent(period)}`);
}

/**
 * Детальная информация о тикете.
 * @param {number} ticketId
 * @returns {Promise<{ ticket, comments, attachments, is_staff_view, is_closed, can_comment, can_rate, update_options? }>}
 */
export function fetchTicketDetail(ticketId) {
  return request(`/tech_support/ticket/${ticketId}/`);
}

/**
 * Взять тикет в работу (staff).
 * @param {number} ticketId
 * @returns {Promise<{ success: boolean, message: string }>}
 */
export function takeTicket(ticketId) {
  return request(`/tech_support/ticket/${ticketId}/take/`, { method: 'POST' });
}

/**
 * Закрыть тикет (staff).
 * @param {number} ticketId
 * @returns {Promise<{ success: boolean, message: string }>}
 */
export function closeTicket(ticketId) {
  return request(`/tech_support/ticket/${ticketId}/close/`, { method: 'POST' });
}

/**
 * Добавить комментарий к тикету.
 * @param {number} ticketId
 * @param {string} content
 * @returns {Promise<{ success: boolean, comment: object }>}
 */
export function addTicketComment(ticketId, content) {
  return request(`/tech_support/ticket/${ticketId}/comment/`, {
    method: 'POST',
    body: JSON.stringify({ content }),
  });
}

/**
 * Обновить параметры тикета (staff).
 * @param {number} ticketId
 * @param {object} payload — { title?, status_id?, priority_id?, category_id?, deadline?, assigned_to_id? }
 * @returns {Promise<{ success: boolean, message: string }>}
 */
export function updateTicket(ticketId, payload) {
  return request(`/tech_support/ticket/${ticketId}/update/`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

/**
 * Оценить решение тикета (только автор закрытого тикета).
 * @param {number} ticketId
 * @param {number} rating — от 1 до 5
 * @param {string} studentFeedback — отзыв
 * @returns {Promise<{ success: boolean, message: string }>}
 */
export function rateTicket(ticketId, rating, studentFeedback = '') {
  return request(`/tech_support/ticket/${ticketId}/rate/`, {
    method: 'POST',
    body: JSON.stringify({ rating, student_feedback: studentFeedback }),
  });
}
