import { useState, useEffect, useCallback } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { fetchTicketListStaff } from '../../../api/tech_support_api';
import './TicketListPage.css';

const TicketListPage = () => {
  const [searchParams] = useSearchParams();
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const queryString = searchParams.toString();

  const loadTickets = useCallback(async () => {
    setLoading(true);
    setError(null);
    const params = {};
    searchParams.forEach((value, key) => {
      params[key] = value;
    });
    try {
      const data = await fetchTicketListStaff(params);
      setTickets(data.tickets || []);
    } catch (err) {
      setError(err.message || 'Ошибка загрузки списка тикетов');
      setTickets([]);
    } finally {
      setLoading(false);
    }
  }, [queryString]);

  useEffect(() => {
    loadTickets();
  }, [loadTickets]);

  useEffect(() => {
    document.title = 'Тикеты поддержки';
    return () => { document.title = 'Главная'; };
  }, []);

  const hasTickets = tickets.length > 0;

  return (
    <main className="ticket-list-page" aria-label="Тикеты поддержки">
      <div className="ticket-list-page__container">
        <div className="ticket-list-page__header">
          <h1 className="ticket-list-page__title">Тикеты</h1>
          <Link to="/tech_support/chat/" className="ticket-list-page__btn-create btn btn-primary btn-sm">
            Новый тикет
          </Link>
        </div>

        {loading && (
          <p className="ticket-list-page__loading" aria-live="polite">
            Загрузка…
          </p>
        )}

        {error && (
          <p className="ticket-list-page__error" role="alert">
            {error}
          </p>
        )}

        {!loading && !error && (
          <div className="ticket-list-page__card card">
            <div className="ticket-list-page__table-wrap table-responsive">
              <table className="ticket-list-page__table table align-middle mb-0">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Заголовок</th>
                    <th>Статус</th>
                    <th>Приоритет</th>
                    <th>Категория</th>
                    <th>Автор</th>
                    <th>Ответственный</th>
                    <th>Создан</th>
                    <th aria-label="Действия" />
                  </tr>
                </thead>
                <tbody>
                  {hasTickets ? (
                    tickets.map((t) => (
                      <tr key={t.id}>
                        <td>{t.ticket_number}</td>
                        <td>
                          <Link to={`/tech_support/ticket/${t.id}/`} className="ticket-list-page__link">
                            {t.title}
                          </Link>
                        </td>
                        <td>{t.status?.name ?? ''}</td>
                        <td>
                          <span
                            className="ticket-list-page__badge badge"
                            style={{ background: t.priority?.color ?? '#6c757d' }}
                          >
                            {t.priority?.name ?? ''}
                          </span>
                        </td>
                        <td>{t.category?.name ?? ''}</td>
                        <td>{t.created_by_display ?? ''}</td>
                        <td>{t.assigned_to_display ?? '—'}</td>
                        <td>{t.created_at}</td>
                        <td className="text-end">
                          <Link
                            to={`/tech_support/ticket/${t.id}/`}
                            className="btn btn-sm btn-outline-secondary"
                          >
                            Открыть
                          </Link>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={9} className="text-center text-muted py-4">
                        Нет тикетов
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </main>
  );
};

export default TicketListPage;
