import { useState, useEffect, useCallback } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { fetchTicketReports } from '../../../api/tech_support_api';
import './TicketReportsPage.css';

const PERIODS = [
  { value: 'week', label: 'Неделя', icon: 'fa-calendar-week' },
  { value: 'month', label: 'Месяц', icon: 'fa-calendar-alt' },
  { value: 'year', label: 'Год', icon: 'fa-calendar' },
];

function formatDay(isoDay) {
  if (!isoDay) return '';
  const d = new Date(isoDay + 'T12:00:00');
  const day = String(d.getDate()).padStart(2, '0');
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const year = d.getFullYear();
  return `${day}.${month}.${year}`;
}

const TicketReportsPage = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const periodFromUrl = searchParams.get('period') || 'month';
  const [period, setPeriod] = useState(
    PERIODS.some((p) => p.value === periodFromUrl) ? periodFromUrl : 'month'
  );
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadReports = useCallback(async (p) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchTicketReports(p);
      setData(res);
    } catch (err) {
      setError(err.message || 'Ошибка загрузки отчётов');
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const p = PERIODS.some((x) => x.value === periodFromUrl) ? periodFromUrl : 'month';
    setPeriod(p);
    loadReports(p);
  }, [periodFromUrl, loadReports]);

  useEffect(() => {
    document.title = 'Отчеты по тикетам - УЦ «Территория Улыбки»';
    return () => {
      document.title = 'Главная';
    };
  }, []);

  const handlePeriodChange = (newPeriod) => {
    setSearchParams({ period: newPeriod });
    setPeriod(newPeriod);
    loadReports(newPeriod);
  };

  if (loading && !data) {
    return (
      <main className="ticket-reports-page" aria-label="Отчеты по тикетам">
        <div className="ticket-reports-page__container">
          <p className="ticket-reports-page__loading" aria-live="polite">
            Загрузка…
          </p>
        </div>
      </main>
    );
  }

  if (error && !data) {
    return (
      <main className="ticket-reports-page" aria-label="Отчеты по тикетам">
        <div className="ticket-reports-page__container">
          <p className="ticket-reports-page__error" role="alert">
            {error}
          </p>
        </div>
      </main>
    );
  }

  const total_resolved = data?.total_resolved ?? 0;
  const avg_resolution_time = data?.avg_resolution_time ?? 0;
  const performer_stats = data?.performer_stats ?? [];
  const avg_rating = data?.avg_rating ?? 0;
  const tickets_by_period = data?.tickets_by_period ?? [];

  return (
    <main className="ticket-reports-page" aria-label="Отчеты по тикетам">
      <div className="ticket-reports-page__container">
        <header className="ticket-reports-page__header">
          <h1 className="ticket-reports-page__title">
            <i className="fas fa-chart-bar ticket-reports-page__title-icon" aria-hidden />
            Отчеты по тикетам
          </h1>
          <div className="ticket-reports-page__actions">
            <Link to="/tech_support/dashboard" className="btn btn-outline-primary me-2">
              <i className="fas fa-tachometer-alt me-2" aria-hidden />
              Дашборд
            </Link>
            <Link to="/tech_support/tickets" className="btn btn-outline-secondary">
              <i className="fas fa-list me-2" aria-hidden />
              Тикеты
            </Link>
          </div>
        </header>

        <section className="ticket-reports-page__period" aria-label="Выбор периода">
          <h2 className="ticket-reports-page__period-title">
            <i className="fas fa-calendar me-2" aria-hidden />
            Выберите период для отчета
          </h2>
          <div className="ticket-reports-page__period-buttons" role="group" aria-label="Период">
            {PERIODS.map((p) => (
              <button
                key={p.value}
                type="button"
                className={`ticket-reports-page__period-btn ${period === p.value ? 'ticket-reports-page__period-btn--active' : ''}`}
                onClick={() => handlePeriodChange(p.value)}
                aria-pressed={period === p.value}
              >
                <i className={`fas ${p.icon} me-1`} aria-hidden />
                {p.label}
              </button>
            ))}
          </div>
        </section>

        <section className="ticket-reports-page__stats" aria-label="Общая статистика">
          <div className="ticket-reports-page__stats-grid">
            <div className="ticket-reports-page__report-card ticket-reports-page__report-card--center">
              <i className="fas fa-ticket-alt ticket-reports-page__card-icon ticket-reports-page__card-icon--primary" aria-hidden />
              <div className="ticket-reports-page__stats-number">{total_resolved}</div>
              <div className="ticket-reports-page__stats-label">Решенных тикетов</div>
            </div>
            <div className="ticket-reports-page__report-card ticket-reports-page__report-card--center">
              <i className="fas fa-clock ticket-reports-page__card-icon ticket-reports-page__card-icon--warning" aria-hidden />
              <div className="ticket-reports-page__stats-number">{avg_resolution_time}</div>
              <div className="ticket-reports-page__stats-label">Среднее время решения (часы)</div>
            </div>
            <div className="ticket-reports-page__report-card ticket-reports-page__report-card--center">
              <i className="fas fa-users ticket-reports-page__card-icon ticket-reports-page__card-icon--success" aria-hidden />
              <div className="ticket-reports-page__stats-number">{performer_stats.length}</div>
              <div className="ticket-reports-page__stats-label">Активных исполнителей</div>
            </div>
            <div className="ticket-reports-page__report-card ticket-reports-page__report-card--center">
              <i className="fas fa-star ticket-reports-page__card-icon ticket-reports-page__card-icon--warning" aria-hidden />
              <div className="ticket-reports-page__stats-number">{avg_rating}</div>
              <div className="ticket-reports-page__stats-label">Средняя оценка</div>
            </div>
          </div>
        </section>

        <section className="ticket-reports-page__section" aria-label="Статистика по исполнителям">
          <div className="ticket-reports-page__report-card">
            <h2 className="ticket-reports-page__section-title">
              <i className="fas fa-users me-2" aria-hidden />
              Статистика по исполнителям
            </h2>
            {performer_stats.length > 0 ? (
              <div className="ticket-reports-page__performers-grid">
                {performer_stats.map((performer) => {
                  const successPercent =
                    performer.total > 0
                      ? Math.round((performer.resolved / performer.total) * 100)
                      : 0;
                  const ratingInt = performer.avg_rating != null ? Math.round(performer.avg_rating) : 0;
                  return (
                    <div key={performer.assigned_to__username} className="ticket-reports-page__performer-card">
                      <div className="ticket-reports-page__performer-header">
                        <h3 className="ticket-reports-page__performer-name">
                          {performer.assigned_to__username}
                        </h3>
                        <span className="ticket-reports-page__performer-badge">
                          {performer.total} тикетов
                        </span>
                      </div>
                      <div className="ticket-reports-page__performer-row">
                        <div className="ticket-reports-page__performer-cell">
                          <div className="ticket-reports-page__performer-value ticket-reports-page__performer-value--success">
                            {performer.resolved}
                          </div>
                          <small className="ticket-reports-page__performer-label">Решено</small>
                        </div>
                        <div className="ticket-reports-page__performer-cell">
                          <div className="ticket-reports-page__performer-value ticket-reports-page__performer-value--warning">
                            {performer.avg_rating != null ? performer.avg_rating.toFixed(1) : '—'}
                          </div>
                          <small className="ticket-reports-page__performer-label">Оценка</small>
                        </div>
                        <div className="ticket-reports-page__performer-cell">
                          <div className="ticket-reports-page__performer-value ticket-reports-page__performer-value--info">
                            {successPercent}%
                          </div>
                          <small className="ticket-reports-page__performer-label">Успешность</small>
                        </div>
                      </div>
                      {performer.avg_rating != null && (
                        <div className="ticket-reports-page__rating-stars" aria-label={`Оценка ${performer.avg_rating.toFixed(1)} из 5`}>
                          {[1, 2, 3, 4, 5].map((i) => (
                            <i
                              key={i}
                              className={i <= ratingInt ? 'fas fa-star' : 'far fa-star'}
                              aria-hidden
                            />
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="ticket-reports-page__empty">Нет данных для отображения</p>
            )}
          </div>
        </section>

        <section className="ticket-reports-page__section" aria-label="Динамика тикетов по дням">
          <div className="ticket-reports-page__report-card">
            <h2 className="ticket-reports-page__section-title">
              <i className="fas fa-chart-line me-2" aria-hidden />
              Динамика тикетов по дням
            </h2>
            {tickets_by_period.length > 0 ? (
              <div className="ticket-reports-page__table-wrap">
                <table className="ticket-reports-page__table">
                  <thead>
                    <tr>
                      <th>Дата</th>
                      <th>Количество тикетов</th>
                      <th>Процент от общего</th>
                    </tr>
                  </thead>
                  <tbody>
                    {tickets_by_period.map((day) => {
                      const percent = total_resolved > 0 ? Math.round((day.count / total_resolved) * 100) : 0;
                      return (
                        <tr key={day.day}>
                          <td>{formatDay(day.day)}</td>
                          <td>
                            <div className="ticket-reports-page__progress-cell">
                              <div
                                className="ticket-reports-page__progress-bar"
                                role="progressbar"
                                aria-valuenow={day.count}
                                aria-valuemin={0}
                                aria-valuemax={total_resolved}
                                style={{ width: `${percent}%` }}
                              />
                              <span className="ticket-reports-page__progress-badge">{day.count}</span>
                            </div>
                          </td>
                          <td>{percent}%</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="ticket-reports-page__empty">Нет данных для отображения</p>
            )}
          </div>
        </section>
      </div>
    </main>
  );
};

export default TicketReportsPage;
