import {
  useState, useEffect, useCallback, useRef,
} from 'react';
import {
  useSearchParams, Link, useOutletContext,
} from 'react-router-dom';
import {
  fetchNotificationsList,
  markAllNotificationsRead,
  markNotificationRead,
  deleteNotification,
  clearOldNotifications,
} from '../../../api/notifications_api';
import { getNotificationIconClass } from '../../../utils/notificationIcons';
import './NotificationsListPage.css';

function buildListSearchParams(page, type, search) {
  const q = new URLSearchParams();
  if (page > 1) {
    q.set('page', String(page));
  }
  if (type) {
    q.set('type', type);
  }
  if (search) {
    q.set('search', search);
  }
  return q;
}

const NotificationsListPage = () => {
  const { isAuthenticated, refreshLayout } = useOutletContext();
  const [searchParams, setSearchParams] = useSearchParams();
  const pageParam = searchParams.get('page');
  const typeParam = searchParams.get('type') || '';
  const searchFromUrl = searchParams.get('search') || '';
  const page = Math.max(1, parseInt(pageParam || '1', 10) || 1);

  const [searchInput, setSearchInput] = useState(searchFromUrl);
  const searchDebounceRef = useRef(null);

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [actionBusyId, setActionBusyId] = useState(null);

  useEffect(() => {
    setSearchInput(searchFromUrl);
  }, [searchFromUrl]);

  const loadData = useCallback(async () => {
    if (!isAuthenticated) {
      setData(null);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const result = await fetchNotificationsList({
        page,
        type: typeParam,
        search: searchFromUrl,
      });
      setData(result);
    } catch (err) {
      setError(err.message || 'Ошибка загрузки уведомлений');
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated, page, typeParam, searchFromUrl]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  useEffect(() => {
    document.title = 'Уведомления';
    return () => {
      document.title = 'Главная';
    };
  }, []);

  const updateUrlFilters = useCallback((next) => {
    const q = buildListSearchParams(
      next.page ?? page,
      next.type !== undefined ? next.type : typeParam,
      next.search !== undefined ? next.search : searchFromUrl,
    );
    setSearchParams(q);
  }, [page, typeParam, searchFromUrl, setSearchParams]);

  const handleTypeChange = (e) => {
    updateUrlFilters({ type: e.target.value, page: 1 });
  };

  const handleSearchInput = (e) => {
    const value = e.target.value;
    setSearchInput(value);
    if (searchDebounceRef.current) {
      window.clearTimeout(searchDebounceRef.current);
    }
    searchDebounceRef.current = window.setTimeout(() => {
      const q = buildListSearchParams(1, typeParam, value);
      setSearchParams(q);
    }, 500);
  };

  const handleFilterSubmit = (e) => {
    e.preventDefault();
    const q = buildListSearchParams(1, typeParam, searchInput);
    setSearchParams(q);
  };

  const handleMarkAllRead = async () => {
    try {
      await markAllNotificationsRead();
      await refreshLayout?.();
      await loadData();
    } catch (err) {
      console.error(err);
    }
  };

  const handleClearOld = async () => {
    if (!window.confirm('Удалить уведомления старше 30 дней?')) {
      return;
    }
    try {
      await clearOldNotifications();
      await refreshLayout?.();
      await loadData();
    } catch (err) {
      console.error(err);
    }
  };

  const handleMarkRead = async (notificationId) => {
    setActionBusyId(notificationId);
    try {
      await markNotificationRead(notificationId);
      await refreshLayout?.();
      await loadData();
    } catch (err) {
      console.error(err);
    } finally {
      setActionBusyId(null);
    }
  };

  const handleDelete = async (notificationId) => {
    if (!window.confirm('Удалить уведомление?')) {
      return;
    }
    setActionBusyId(notificationId);
    try {
      await deleteNotification(notificationId);
      await refreshLayout?.();
      await loadData();
    } catch (err) {
      console.error(err);
    } finally {
      setActionBusyId(null);
    }
  };

  const handleItemActivate = (n) => {
    if (n.url && n.url !== '#') {
      window.location.href = n.url;
    }
  };

  if (!isAuthenticated) {
    return (
      <main className="notifications-list-page" aria-label="Уведомления">
        <div className="notifications-list-page__container">
          <p className="notifications-list-page__guest">
            Чтобы просматривать уведомления, войдите в аккаунт.
          </p>
          <Link to="/users/login" className="notifications-list-page__login-link">
            Войти
          </Link>
        </div>
      </main>
    );
  }

  const { pagination, items, unread_count: unreadCount } = data || {};
  const hasItems = items && items.length > 0;

  const pageNumbers = [];
  if (pagination && pagination.num_pages > 0) {
    const { num_pages: total, page: current } = pagination;
    const from = Math.max(1, current - 2);
    const to = Math.min(total, current + 2);
    for (let n = from; n <= to; n += 1) {
      pageNumbers.push(n);
    }
  }

  const pageLink = (num) => {
    const q = buildListSearchParams(num, typeParam, searchFromUrl);
    const qs = q.toString();
    return qs ? `/notifications/?${qs}` : '/notifications/';
  };

  return (
    <main className="notifications-list-page" aria-label="Уведомления">
      <header className="notifications-list-page__hero">
        <div className="notifications-list-page__hero-inner">
          <h1 className="notifications-list-page__title">
            <i className="fas fa-bell notifications-list-page__title-icon" aria-hidden />
            Уведомления
          </h1>
          <p className="notifications-list-page__subtitle">
            Управление всеми вашими уведомлениями
          </p>
        </div>
      </header>

      <div className="notifications-list-page__container">
        {loading && (
          <p className="notifications-list-page__loading" aria-live="polite">
            Загрузка…
          </p>
        )}

        {error && (
          <p className="notifications-list-page__error" role="alert">
            {error}
          </p>
        )}

        {!loading && !error && data && (
          <>
            <section className="notifications-list-page__stats" aria-label="Статистика">
              <div className="notifications-list-page__stat">
                <div className="notifications-list-page__stat-number">{data.total_count}</div>
                <div className="notifications-list-page__stat-label">Всего уведомлений</div>
              </div>
              <div className="notifications-list-page__stat">
                <div className="notifications-list-page__stat-number notifications-list-page__stat-number--warning">
                  {data.unread_count}
                </div>
                <div className="notifications-list-page__stat-label">Непрочитанных</div>
              </div>
              <div className="notifications-list-page__stat">
                <div className="notifications-list-page__stat-number notifications-list-page__stat-number--success">
                  {data.read_count}
                </div>
                <div className="notifications-list-page__stat-label">Прочитанных</div>
              </div>
            </section>

            <button
              type="button"
              className="notifications-list-page__clear-old"
              onClick={() => { void handleClearOld(); }}
            >
              <i className="fas fa-trash" aria-hidden />
              Очистить старые уведомления (старше 30 дней)
            </button>

            <section className="notifications-list-page__filters" aria-label="Фильтры">
              <form className="notifications-list-page__filter-form" onSubmit={handleFilterSubmit}>
                <div className="notifications-list-page__filter-field">
                  <label htmlFor="notifications-type" className="notifications-list-page__label">
                    Тип уведомления
                  </label>
                  <select
                    id="notifications-type"
                    className="notifications-list-page__select"
                    value={typeParam}
                    onChange={handleTypeChange}
                  >
                    <option value="">Все типы</option>
                    {(data.notification_types || []).map((t) => (
                      <option key={t.code} value={t.code}>{t.label}</option>
                    ))}
                  </select>
                </div>
                <div className="notifications-list-page__filter-field notifications-list-page__filter-field--grow">
                  <label htmlFor="notifications-search" className="notifications-list-page__label">
                    Поиск
                  </label>
                  <input
                    id="notifications-search"
                    type="search"
                    className="notifications-list-page__input"
                    value={searchInput}
                    onChange={handleSearchInput}
                    placeholder="Поиск по заголовку или сообщению"
                    autoComplete="off"
                  />
                </div>
                <div className="notifications-list-page__filter-field notifications-list-page__filter-field--submit">
                  <span className="notifications-list-page__label notifications-list-page__label--phantom">
                    &nbsp;
                  </span>
                  <button type="submit" className="notifications-list-page__btn-search">
                    <i className="fas fa-search" aria-hidden />
                    Найти
                  </button>
                </div>
              </form>
            </section>

            {unreadCount > 0 && (
              <div className="notifications-list-page__mark-all-wrap">
                <button
                  type="button"
                  className="notifications-list-page__mark-all"
                  onClick={() => { void handleMarkAllRead(); }}
                >
                  <i className="fas fa-check-double" aria-hidden />
                  Отметить все как прочитанные
                </button>
              </div>
            )}

            {hasItems ? (
              <>
                <ul className="notifications-list-page__list">
                  {items.map((n) => {
                    const hasLink = n.url && n.url !== '#';
                    return (
                      <li key={n.id}>
                        <article
                          className={
                            `notifications-list-page__item${!n.is_read ? ' notifications-list-page__item--unread' : ''}${hasLink ? ' notifications-list-page__item--clickable' : ''}`
                          }
                          onClick={() => handleItemActivate(n)}
                          onKeyDown={(e) => {
                            if (hasLink && (e.key === 'Enter' || e.key === ' ')) {
                              e.preventDefault();
                              handleItemActivate(n);
                            }
                          }}
                          role={hasLink ? 'button' : undefined}
                          tabIndex={hasLink ? 0 : undefined}
                          title={hasLink ? 'Нажмите для перехода к связанному объекту' : undefined}
                        >
                          <div className="notifications-list-page__item-row">
                            <div className="notifications-list-page__icon-wrap">
                              {n.avatar_url ? (
                                <img
                                  src={n.avatar_url}
                                  alt=""
                                  className="notifications-list-page__avatar"
                                />
                              ) : (
                                <span className="notifications-list-page__icon-ring">
                                  <i className={getNotificationIconClass(n.notification_type)} aria-hidden />
                                </span>
                              )}
                            </div>
                            <div className="notifications-list-page__content">
                              <div className="notifications-list-page__item-title">
                                {n.title}
                                {!n.is_read ? (
                                  <span className="notifications-list-page__unread-dot" aria-hidden />
                                ) : null}
                              </div>
                              <div className="notifications-list-page__item-message">{n.message}</div>
                              <div className="notifications-list-page__meta">
                                <span className="notifications-list-page__type-badge">
                                  <i className="fas fa-tag" aria-hidden />
                                  {n.notification_type_display}
                                </span>
                                <span className="notifications-list-page__time">
                                  <i className="fas fa-clock" aria-hidden />
                                  {n.created_at_display}
                                </span>
                              </div>
                            </div>
                            <div
                              className="notifications-list-page__actions"
                              role="group"
                              aria-label="Действия"
                              onClick={(e) => e.stopPropagation()}
                              onKeyDown={(e) => e.stopPropagation()}
                            >
                              {!n.is_read ? (
                                <button
                                  type="button"
                                  className="notifications-list-page__action notifications-list-page__action--read"
                                  disabled={actionBusyId === n.id}
                                  onClick={() => { void handleMarkRead(n.id); }}
                                >
                                  {actionBusyId === n.id ? (
                                    <i className="fas fa-spinner fa-spin" aria-hidden />
                                  ) : (
                                    <i className="fas fa-check" aria-hidden />
                                  )}
                                  Прочитано
                                </button>
                              ) : null}
                              <button
                                type="button"
                                className="notifications-list-page__action notifications-list-page__action--delete"
                                disabled={actionBusyId === n.id}
                                onClick={() => { void handleDelete(n.id); }}
                              >
                                <i className="fas fa-trash" aria-hidden />
                              </button>
                            </div>
                          </div>
                        </article>
                      </li>
                    );
                  })}
                </ul>

                {pagination && pagination.num_pages > 1 && (
                  <nav className="notifications-list-page__pagination" aria-label="Навигация по страницам">
                    <ul className="notifications-list-page__pagination-list">
                      {pagination.has_previous ? (
                        <li>
                          <Link
                            className="notifications-list-page__page-link"
                            to={pageLink(pagination.previous_page_number)}
                          >
                            Предыдущая
                          </Link>
                        </li>
                      ) : null}
                      {pageNumbers.map((num) => (
                        <li key={num}>
                          {num === pagination.page ? (
                            <span className="notifications-list-page__page-current">{num}</span>
                          ) : (
                            <Link className="notifications-list-page__page-link" to={pageLink(num)}>
                              {num}
                            </Link>
                          )}
                        </li>
                      ))}
                      {pagination.has_next ? (
                        <li>
                          <Link
                            className="notifications-list-page__page-link"
                            to={pageLink(pagination.next_page_number)}
                          >
                            Следующая
                          </Link>
                        </li>
                      ) : null}
                    </ul>
                  </nav>
                )}
              </>
            ) : (
              <div className="notifications-list-page__empty">
                <i className="fas fa-bell-slash notifications-list-page__empty-icon" aria-hidden />
                <h2 className="notifications-list-page__empty-title">Уведомлений не найдено</h2>
                <p className="notifications-list-page__empty-text">
                  Попробуйте изменить параметры поиска или фильтры
                </p>
              </div>
            )}
          </>
        )}
      </div>
    </main>
  );
};

export default NotificationsListPage;
