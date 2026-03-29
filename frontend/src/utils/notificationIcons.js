/** Иконки типов уведомлений (Font Awesome классы). */

export const NOTIFICATION_TYPE_ICONS = {
  course_assigned: 'fas fa-graduation-cap',
  trajectory_assigned: 'fas fa-route',
  dascoin: 'fas fa-coins',
  platform_update: 'fas fa-sync-alt',
  lesson_actualization: 'fas fa-book',
  ticket_status: 'fas fa-ticket-alt',
  ticket_comment: 'fas fa-comment',
  chat_message: 'fas fa-comment',
  quiz_reviewed: 'fas fa-check-circle',
  homework_reviewed: 'fas fa-tasks',
  order_status: 'fas fa-shopping-cart',
  course_materials_updated: 'fas fa-book',
  incident_course_overdue: 'fas fa-exclamation-circle',
  course_reminder: 'fas fa-bell',
};

export function getNotificationIconClass(type) {
  return NOTIFICATION_TYPE_ICONS[type] || 'fas fa-bell';
}
