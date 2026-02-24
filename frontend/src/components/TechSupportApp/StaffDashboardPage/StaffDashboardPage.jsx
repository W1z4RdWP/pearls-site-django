import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { fetchStaffDashboard } from '../../../api/tech_support_api';
import './StaffDashboardPage.css';

const PRIORITY_LEVEL_HIGH = 3;
const PRIORITY_LEVEL_MEDIUM = 2;

const StaffDashboardPage = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadDashboard = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchStaffDashboard();
      setData(res);
    } catch (err) {
      setError(err.message || 'Ошибка загрузки дашборда');
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  useEffect(() => {
    document.title = 'Дашборд поддержки - УЦ «Территория Улыбки»';
    return () => { document.title = 'Главная'; };
  }, []);

  const getTicketPriorityClass = (level) => {
    if (level === PRIORITY_LEVEL_HIGH) return 'staff-dashboard-page__ticket-item--high';
    if (level === PRIORITY_LEVEL_MEDIUM) return 'staff-dashboard-page__ticket-item--medium';
    return 'staff-dashboard-page__ticket-item--low';
  };

  const ticketsLink = '/tech_support/tickets';
  const ticketsWithPriority = `${ticketsLink}?priority=3`;
  const ticketsOverdue = `${ticketsLink}?search=просрочен`;
  const ticketsActiveChats = data?.status_in_progress_id
    ? `${ticketsLink}?status=${data.status_in_progress_id}`
    : ticketsLink;
  const ticketsFilterActive = `${ticketsLink}?active=1`;
  const ticketsFilterResolved = `${ticketsLink}?resolved=1`;
  const ticketsFilterOverdue = `${ticketsLink}?search=просрочен`;

  if (loading) {
    return (
      <main className="staff-dashboard-page" aria-label="Дашборд поддержки">
        <div className="staff-dashboard-page__container">
          <p className="staff-dashboard-page__loading" aria-live="polite">
            Загрузка…
          </p>
        </div>
      </main>
    );
  }

  if (error) {
    return (
      <main className="staff-dashboard-page" aria-label="Дашборд поддержки">
        <div className="staff-dashboard-page__container">
          <p className="staff-dashboard-page__error" role="alert">
            {error}
          </p>
        </div>
      </main>
    );
  }

  const {
    total_tickets = 0,
    active_tickets = 0,
    resolved_tickets = 0,
    overdue_tickets = 0,
    priority_stats = [],
    type_stats = [],
    avg_rating = 0,
    recent_tickets = [],
    overdue_tickets_list = [],
  } = data || {};

  const avgRatingInt = Math.round(avg_rating);
  const ratingPercent = (avg_rating / 5) * 100;

  return (
    <main className="staff-dashboard-page" aria-label="Дашборд поддержки">
      <div className="staff-dashboard-page__container">
        <header className="staff-dashboard-page__header">
          <h1 className="staff-dashboard-page__title">
            <i className="fas fa-tachometer-alt staff-dashboard-page__title-icon" aria-hidden />
            Дашборд поддержки
          </h1>
          <div className="staff-dashboard-page__actions">
            <Link to={ticketsLink} className="btn btn-primary me-2">
              <i className="fas fa-list me-2" aria-hidden />Все тикеты
            </Link>
            <a href="/tech_support/reports/" className="btn btn-outline-primary">
              <i className="fas fa-chart-bar me-2" aria-hidden />Отчеты
            </a>
          </div>
        </header>

        <section className="staff-dashboard-page__stats" aria-label="Статистика">
          <div className="staff-dashboard-page__stats-grid">
            <Link to={ticketsLink} className="staff-dashboard-page__stats-card staff-dashboard-page__stats-card--link">
              <div className="staff-dashboard-page__stats-inner">
                <div>
                  <div className="staff-dashboard-page__stats-number">{total_tickets}</div>
                  <div className="staff-dashboard-page__stats-label">Всего тикетов</div>
                </div>
                <i className="fas fa-ticket-alt staff-dashboard-page__stats-icon" aria-hidden />
              </div>
            </Link>
            <Link to={ticketsFilterActive} className="staff-dashboard-page__stats-card staff-dashboard-page__stats-card--warning staff-dashboard-page__stats-card--link">
              <div className="staff-dashboard-page__stats-inner">
                <div>
                  <div className="staff-dashboard-page__stats-number">{active_tickets}</div>
                  <div className="staff-dashboard-page__stats-label">Активных</div>
                </div>
                <i className="fas fa-clock staff-dashboard-page__stats-icon" aria-hidden />
              </div>
            </Link>
            <Link to={ticketsFilterResolved} className="staff-dashboard-page__stats-card staff-dashboard-page__stats-card--success staff-dashboard-page__stats-card--link">
              <div className="staff-dashboard-page__stats-inner">
                <div>
                  <div className="staff-dashboard-page__stats-number">{resolved_tickets}</div>
                  <div className="staff-dashboard-page__stats-label">Решенных</div>
                </div>
                <i className="fas fa-check-circle staff-dashboard-page__stats-icon" aria-hidden />
              </div>
            </Link>
            <Link to={ticketsFilterOverdue} className="staff-dashboard-page__stats-card staff-dashboard-page__stats-card--info staff-dashboard-page__stats-card--link">
              <div className="staff-dashboard-page__stats-inner">
                <div>
                  <div className="staff-dashboard-page__stats-number">{overdue_tickets}</div>
                  <div className="staff-dashboard-page__stats-label">Просроченных</div>
                </div>
                <i className="fas fa-exclamation-triangle staff-dashboard-page__stats-icon" aria-hidden />
              </div>
            </Link>
          </div>
        </section>

        <div className="staff-dashboard-page__row">
          <section className="staff-dashboard-page__quick-actions">
            <h2 className="staff-dashboard-page__section-title">
              <i className="fas fa-bolt me-2" aria-hidden />Быстрые действия
            </h2>
            <Link to={ticketsLink} className="staff-dashboard-page__action-btn staff-dashboard-page__action-btn--primary">
              <i className="fas fa-list me-2" aria-hidden />Просмотр всех тикетов
            </Link>
            <Link to={ticketsWithPriority} className="staff-dashboard-page__action-btn staff-dashboard-page__action-btn--warning">
              <i className="fas fa-exclamation-triangle me-2" aria-hidden />Высокий приоритет
            </Link>
            <Link to={ticketsOverdue} className="staff-dashboard-page__action-btn staff-dashboard-page__action-btn--success">
              <i className="fas fa-clock me-2" aria-hidden />Просроченные тикеты
            </Link>
            <Link to={ticketsActiveChats} className="staff-dashboard-page__action-btn staff-dashboard-page__action-btn--info">
              <i className="fas fa-comments me-2" aria-hidden />Активные чаты
            </Link>
          </section>

          <section className="staff-dashboard-page__chart staff-dashboard-page__chart--priorities">
            <h2 className="staff-dashboard-page__section-title">
              <i className="fas fa-chart-pie me-2" aria-hidden />Распределение по приоритетам
            </h2>
            {priority_stats.length > 0 ? (
              <div className="staff-dashboard-page__priority-grid">
                {priority_stats.map((stat, idx) => (
                  <div key={idx} className="staff-dashboard-page__priority-card card text-center">
                    <div className="card-body">
                      <h3 className="card-title">{stat.priority__name}</h3>
                      <div className="h3 text-primary">{stat.count}</div>
                      <small className="text-muted">тикетов</small>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-muted">Нет данных для отображения</p>
            )}
          </section>
        </div>

        <div className="staff-dashboard-page__row">
          <section className="staff-dashboard-page__ticket-list">
            <h2 className="staff-dashboard-page__section-title">
              <i className="fas fa-history me-2" aria-hidden />Последние тикеты
            </h2>
            {recent_tickets.length > 0 ? (
              <ul className="staff-dashboard-page__ticket-list-inner" aria-label="Список последних тикетов">
                {recent_tickets.map((ticket) => (
                  <li
                    key={ticket.id}
                    className={`staff-dashboard-page__ticket-item ${ticket.is_overdue ? 'staff-dashboard-page__ticket-item--overdue' : ''} ${getTicketPriorityClass(ticket.priority?.level)}`}
                  >
                    <div className="staff-dashboard-page__ticket-item-inner">
                      <div className="staff-dashboard-page__ticket-item-body">
                        <h3 className="staff-dashboard-page__ticket-title">
                          <a href={`/tech_support/ticket/${ticket.id}/`} className="staff-dashboard-page__ticket-link">
                            {ticket.ticket_number} - {ticket.title}
                          </a>
                        </h3>
                        <p className="staff-dashboard-page__ticket-desc text-muted small">{ticket.description}</p>
                        <div className="staff-dashboard-page__ticket-meta">
                          <span
                            className="staff-dashboard-page__priority-badge me-2"
                            style={{ backgroundColor: ticket.priority?.color || '#6c757d', color: 'white' }}
                          >
                            {ticket.priority?.name}
                          </span>
                          <span
                            className="staff-dashboard-page__status-badge me-2"
                            style={{ backgroundColor: ticket.status?.color || '#6c757d', color: 'white' }}
                          >
                            {ticket.status?.name}
                          </span>
                          <small className="text-muted">{ticket.created_at}</small>
                        </div>
                      </div>
                      {ticket.is_overdue && (
                        <span className="badge bg-danger">
                          <i className="fas fa-exclamation-triangle me-1" aria-hidden />ПРОСРОЧЕН
                        </span>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-muted">Нет тикетов для отображения</p>
            )}
          </section>

          <section className="staff-dashboard-page__ticket-list">
            <h2 className="staff-dashboard-page__section-title">
              <i className="fas fa-exclamation-triangle me-2 text-danger" aria-hidden />
              Просроченные тикеты (последние 5 активных)
            </h2>
            {overdue_tickets_list.length > 0 ? (
              <ul className="staff-dashboard-page__ticket-list-inner" aria-label="Просроченные тикеты">
                {overdue_tickets_list.map((ticket) => (
                  <li key={ticket.id} className="staff-dashboard-page__ticket-item staff-dashboard-page__ticket-item--overdue">
                    <div className="staff-dashboard-page__ticket-item-inner">
                      <div className="staff-dashboard-page__ticket-item-body">
                        <h3 className="staff-dashboard-page__ticket-title">
                          <a href={`/tech_support/ticket/${ticket.id}/`} className="staff-dashboard-page__ticket-link">
                            {ticket.ticket_number} - {ticket.title}
                          </a>
                        </h3>
                        <p className="staff-dashboard-page__ticket-desc text-muted small">{ticket.description}</p>
                        <div className="staff-dashboard-page__ticket-meta">
                          <span
                            className="staff-dashboard-page__priority-badge me-2"
                            style={{ backgroundColor: ticket.priority?.color || '#6c757d', color: 'white' }}
                          >
                            {ticket.priority?.name}
                          </span>
                          {ticket.hours_overdue != null && (
                            <small className="text-danger">
                              <i className="fas fa-clock me-1" aria-hidden />
                              Просрочен на {ticket.hours_overdue}ч
                            </small>
                          )}
                        </div>
                      </div>
                      <span className="badge bg-danger">
                        <i className="fas fa-exclamation-triangle me-1" aria-hidden />ПРОСРОЧЕН
                      </span>
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-success">
                <i className="fas fa-check-circle me-2" aria-hidden />Нет просроченных тикетов!
              </p>
            )}
          </section>
        </div>

        <section className="staff-dashboard-page__chart">
          <h2 className="staff-dashboard-page__section-title">
            <i className="fas fa-chart-bar me-2" aria-hidden />Статистика по типам тикетов
          </h2>
          {type_stats.length > 0 ? (
            <div className="staff-dashboard-page__type-grid">
              {type_stats.map((stat, idx) => (
                <div key={idx} className="staff-dashboard-page__type-card card text-center">
                  <div className="card-body">
                    <h3 className="card-title">{stat.ticket_type_display}</h3>
                    <small className="text-muted">кол-во тикетов: </small>
                    <div className="h3 text-primary">{stat.count}</div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-muted">Нет данных для отображения</p>
          )}
        </section>

        <section className="staff-dashboard-page__chart staff-dashboard-page__rating">
          <h2 className="staff-dashboard-page__section-title">
            <i className="fas fa-star me-2" aria-hidden />Качество обслуживания
          </h2>
          <div className="staff-dashboard-page__rating-inner">
            <div className="staff-dashboard-page__rating-score">
              <div className="h1 text-warning mb-2">{avg_rating}/5</div>
              <div className="staff-dashboard-page__rating-stars mb-3">
                {[1, 2, 3, 4, 5].map((i) => (
                  <i
                    key={i}
                    className={i <= avgRatingInt ? 'fas fa-star text-warning' : 'far fa-star text-warning'}
                    aria-hidden
                  />
                ))}
              </div>
              <p className="text-muted">Средняя оценка пользователей</p>
            </div>
            <div className="staff-dashboard-page__rating-bar-wrap">
              <div className="progress mb-2" style={{ height: '25px' }}>
                <div
                  className="progress-bar bg-warning"
                  role="progressbar"
                  style={{ width: `${ratingPercent}%` }}
                  aria-valuenow={avg_rating}
                  aria-valuemin={0}
                  aria-valuemax={5}
                >
                  {Math.round(ratingPercent)}%
                </div>
              </div>
              <small className="text-muted">Уровень удовлетворенности</small>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
};

export default StaffDashboardPage;
