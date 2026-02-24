import { request } from './api';

/**
 * Создаёт тикет обращения в поддержку.
 * @param {object} payload — { ticket_type: string, title: string, description: string }
 * @returns {Promise<{ ticket_id: number, ticket_number: string, ticket_detail_url: string }>}
 */
export function createTicket(payload) {
  return request('/tech_support/chat/', {
    method: 'POST',
    body: JSON.stringify({
      ticket_type: payload.ticket_type,
      title: payload.title,
      description: payload.description,
    }),
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
