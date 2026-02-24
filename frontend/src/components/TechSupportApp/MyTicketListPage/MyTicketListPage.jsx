import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { fetchMyTicketList } from '../../../api/tech_support_api';
import './MyTicketListPage.css';

const MyTicketListPage = () => {
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadTickets = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchMyTicketList();
      setTickets(data.tickets || []);
    } catch (err) {
      setError(err.message || 'Ошибка загрузки списка тикетов');
      setTickets([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadTickets();
  }, [loadTickets]);

  useEffect(() => {
    document.title = 'Мои тикеты';
    return () => { document.title = 'Главная'; };
  }, []);

  const hasTickets = tickets.length > 0;

  return (
    <main className="my-ticket-list-page" aria-label="Мои тикеты">
      <div className="my-ticket-list-page__container">
        <div className="my-ticket-list-page__header">
          <h1 className="my-ticket-list-page__title">Мои тикеты</h1>
          <Link to="/tech_support/chat/" className="my-ticket-list-page__btn-create btn btn-primary btn-sm">
            Создать тикет
          </Link>
        </div>

        {loading && (
          <p className="my-ticket-list-page__loading" aria-live="polite">
            Загрузка…
          </p>
        )}

        {error && (
          <p className="my-ticket-list-page__error" role="alert">
            {error}
          </p>
        )}

        {!loading && !error && (
          <div className="my-ticket-list-page__card card">
            <div className="my-ticket-list-page__table-wrap table-responsive">
              <table className="my-ticket-list-page__table table align-middle mb-0">
                <colgroup>
                  <col className="my-ticket-list-page__col-num" />
                  <col className="my-ticket-list-page__col-title" />
                  <col className="my-ticket-list-page__col-status" />
                  <col className="my-ticket-list-page__col-priority" />
                  <col className="my-ticket-list-page__col-category" />
                  <col className="my-ticket-list-page__col-created" />
                  <col className="my-ticket-list-page__col-actions" />
                </colgroup>
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Заголовок</th>
                    <th>Статус</th>
                    <th>Приоритет</th>
                    <th>Категория</th>
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
                          <Link to={`/tech_support/ticket/${t.id}/`} className="my-ticket-list-page__link">
                            {t.title}
                          </Link>
                        </td>
                        <td>{t.status?.name ?? ''}</td>
                        <td>
                          <span
                            className="my-ticket-list-page__badge badge"
                            style={{ background: t.priority?.color ?? '#6c757d' }}
                          >
                            {t.priority?.name ?? ''}
                          </span>
                        </td>
                        <td>{t.category?.name ?? ''}</td>
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
                      <td colSpan={7} className="text-center text-muted py-4">
                        У вас пока нет тикетов
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

export default MyTicketListPage;
