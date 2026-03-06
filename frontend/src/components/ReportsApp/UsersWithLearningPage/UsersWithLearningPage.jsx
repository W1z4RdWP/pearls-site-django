import { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { fetchUsersWithLearning } from '../../../api/reports_api';
import './UsersWithLearningPage.css';

const CHART_SIZE = 250;
const CHART_R = 70;
const CHART_STROKE = 28;

function DoughnutChart({ data }) {
  if (!data || data.length === 0) {
    return (
      <div className="users-with-learning-page__chart-empty" aria-hidden>
        Нет данных
      </div>
    );
  }
  const total = data.reduce((acc, d) => acc + d.value, 0);
  if (total === 0) {
    return (
      <div className="users-with-learning-page__chart-empty" aria-hidden>
        Нет данных
      </div>
    );
  }
  const circumference = 2 * Math.PI * CHART_R;
  let offset = 0;
  const segments = data.map((d) => {
    const length = (d.value / total) * circumference;
    const seg = { ...d, dashArray: `${length} ${circumference}`, dashOffset: -offset };
    offset += length;
    return seg;
  });

  return (
    <svg
      className="users-with-learning-page__chart-svg"
      width={CHART_SIZE}
      height={CHART_SIZE}
      viewBox={`0 0 ${CHART_SIZE} ${CHART_SIZE}`}
      aria-hidden
    >
      <g transform={`translate(${CHART_SIZE / 2}, ${CHART_SIZE / 2})`}>
        {segments.map((seg, i) => (
          <circle
            key={seg.label}
            r={CHART_R}
            fill="none"
            stroke={seg.color}
            strokeWidth={CHART_STROKE}
            strokeDasharray={seg.dashArray}
            strokeDashoffset={seg.dashOffset}
            transform="rotate(-90)"
          />
        ))}
      </g>
    </svg>
  );
}

const UsersWithLearningPage = () => {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchInput, setSearchInput] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedGroup, setSelectedGroup] = useState('');
  const [page, setPage] = useState(1);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchUsersWithLearning({
        page,
        search: searchQuery,
        group: selectedGroup || undefined,
      });
      setData(result);
    } catch (err) {
      setError(err.message || 'Ошибка загрузки данных');
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [page, searchQuery, selectedGroup]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  useEffect(() => {
    setSearchInput(searchQuery);
  }, [searchQuery]);

  const handleSubmit = (e) => {
    e.preventDefault();
    setSearchQuery(searchInput.trim());
    setPage(1);
  };

  const handleClearFilters = () => {
    setSearchInput('');
    setSearchQuery('');
    setSelectedGroup('');
    setPage(1);
  };

  const handleRowClick = (userId) => {
    navigate(`/user_management/users/${userId}/progress`);
  };

  const getExportExcelUrl = () => {
    const params = new URLSearchParams();
    if (searchQuery) params.set('search', searchQuery);
    if (selectedGroup) params.set('group', selectedGroup);
    const qs = params.toString();
    return `/reports/users-with-learning/export-excel/${qs ? `?${qs}` : ''}`;
  };

  if (loading && !data) {
    return (
      <main className="users-with-learning-page" aria-label="Пользователи с обучением">
        <div className="users-with-learning-page__loading">Загрузка...</div>
      </main>
    );
  }

  if (error && !data) {
    return (
      <main className="users-with-learning-page" aria-label="Пользователи с обучением">
        <div className="users-with-learning-page__error" role="alert">
          <p>{error}</p>
        </div>
      </main>
    );
  }

  const isAdmin = data?.is_admin ?? false;
  const subtitle = isAdmin
    ? 'Все пользователи с назначенными курсами'
    : 'Пользователи из ваших групп с назначенными курсами';
  const users = data?.users ?? [];
  const pagination = data?.pagination ?? {};
  const groups = data?.groups ?? [];
  const learningData = data?.learning_data ?? [];

  return (
    <main className="users-with-learning-page" aria-label="Пользователи с обучением">
      <div className="users-with-learning-page__container">
        <header className="users-with-learning-page__header">
          <div className="users-with-learning-page__title-wrap">
            <h1 className="users-with-learning-page__title">
              <i className="fas fa-users" aria-hidden />
              Пользователи с обучением
            </h1>
            <p className="users-with-learning-page__subtitle">{subtitle}</p>
          </div>
          <div className="users-with-learning-page__actions">
            <a
              href={getExportExcelUrl()}
              className="users-with-learning-page__btn users-with-learning-page__btn--success"
            >
              <i className="fas fa-file-excel" aria-hidden />
              Экспорт в Excel
            </a>
            <Link
              to="/reports/homework-check-dashboard"
              className="users-with-learning-page__btn users-with-learning-page__btn--secondary"
            >
              <i className="fas fa-arrow-left" aria-hidden />
              Назад к панели
            </Link>
          </div>
        </header>

        <section className="users-with-learning-page__stats-card" aria-label="Статистика обученности">
          <div className="users-with-learning-page__stats-body">
            <div className="users-with-learning-page__chart-wrap">
              <DoughnutChart data={learningData} />
              <div className="users-with-learning-page__chart-center">
                <span className="users-with-learning-page__chart-value">
                  {data?.learning_percentage ?? 0}%
                </span>
                <span className="users-with-learning-page__chart-label">Обученность</span>
              </div>
            </div>
            <div className="users-with-learning-page__stats-grid">
              <div className="users-with-learning-page__stat-item">
                <span className="users-with-learning-page__stat-num users-with-learning-page__stat-num--success">
                  {data?.completed_courses ?? 0}
                </span>
                <span className="users-with-learning-page__stat-label">Завершено</span>
              </div>
              <div className="users-with-learning-page__stat-item">
                <span className="users-with-learning-page__stat-num users-with-learning-page__stat-num--warning">
                  {data?.in_progress_courses ?? 0}
                </span>
                <span className="users-with-learning-page__stat-label">В процессе</span>
              </div>
              <div className="users-with-learning-page__stat-item">
                <span className="users-with-learning-page__stat-num users-with-learning-page__stat-num--secondary">
                  {data?.available_courses ?? 0}
                </span>
                <span className="users-with-learning-page__stat-label">Не начато</span>
              </div>
              <div className="users-with-learning-page__stat-item">
                <span className="users-with-learning-page__stat-num users-with-learning-page__stat-num--info">
                  {data?.total_courses ?? 0}
                </span>
                <span className="users-with-learning-page__stat-label">Всего</span>
              </div>
            </div>
          </div>
        </section>

        <section className="users-with-learning-page__card">
          <form
            onSubmit={handleSubmit}
            className="users-with-learning-page__filters"
            aria-label="Фильтры и поиск"
          >
            <div className="users-with-learning-page__filter-group">
              <label htmlFor="users-search" className="users-with-learning-page__label">
                Поиск по ФИО
              </label>
              <input
                id="users-search"
                type="text"
                className="users-with-learning-page__input"
                placeholder="Введите ФИО..."
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                autoComplete="off"
              />
            </div>
            <div className="users-with-learning-page__filter-group">
              <label htmlFor="users-group" className="users-with-learning-page__label">
                Группа
              </label>
              <select
                id="users-group"
                className="users-with-learning-page__select"
                value={selectedGroup}
                onChange={(e) => {
                  setSelectedGroup(e.target.value);
                  setPage(1);
                }}
              >
                <option value="">Все группы</option>
                {groups.map((g) => (
                  <option key={g.id} value={String(g.id)}>
                    {g.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="users-with-learning-page__filter-actions">
              <button type="submit" className="users-with-learning-page__btn users-with-learning-page__btn--primary">
                <i className="fas fa-search" aria-hidden />
                Поиск
              </button>
              <button
                type="button"
                className="users-with-learning-page__btn users-with-learning-page__btn--secondary"
                onClick={handleClearFilters}
              >
                <i className="fas fa-times" aria-hidden />
                Сбросить
              </button>
            </div>
          </form>
        </section>

        <section className="users-with-learning-page__card">
          <div className="users-with-learning-page__card-header">
            <div>
              <h2 className="users-with-learning-page__card-title">Список пользователей</h2>
              <p className="users-with-learning-page__card-desc">Пользователи с назначенным обучением</p>
            </div>
            <span className="users-with-learning-page__badge" aria-label="Количество пользователей">
              {users.length} пользователей
            </span>
          </div>
          <div className="users-with-learning-page__card-body">
            {users.length > 0 ? (
              <>
                <div className="users-with-learning-page__table-wrap">
                  <table className="users-with-learning-page__table">
                    <thead>
                      <tr>
                        <th className="users-with-learning-page__th users-with-learning-page__th--n">#</th>
                        <th className="users-with-learning-page__th users-with-learning-page__th--name">ФИО</th>
                        <th className="users-with-learning-page__th users-with-learning-page__th--email">Email</th>
                        <th className="users-with-learning-page__th users-with-learning-page__th--groups">Группы</th>
                        <th className="users-with-learning-page__th users-with-learning-page__th--status">Статус</th>
                      </tr>
                    </thead>
                    <tbody>
                      {users.map((user, index) => (
                        <tr
                          key={user.id}
                          className="users-with-learning-page__row users-with-learning-page__row--clickable"
                          onClick={() => handleRowClick(user.id)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter' || e.key === ' ') {
                              e.preventDefault();
                              handleRowClick(user.id);
                            }
                          }}
                          role="button"
                          tabIndex={0}
                          aria-label={`Перейти к прогрессу: ${user.full_name}`}
                        >
                          <td className="users-with-learning-page__td users-with-learning-page__td--muted">
                            {(pagination.page - 1) * 20 + index + 1}
                          </td>
                          <td className="users-with-learning-page__td">
                            <strong>{user.full_name}</strong>
                          </td>
                          <td className="users-with-learning-page__td">
                            <small>{user.email}</small>
                          </td>
                          <td className="users-with-learning-page__td">
                            {user.groups?.length > 0 ? (
                              user.groups.map((name) => (
                                <span key={name} className="users-with-learning-page__group-badge">
                                  {name}
                                </span>
                              ))
                            ) : (
                              <span className="users-with-learning-page__td--empty">—</span>
                            )}
                          </td>
                          <td className="users-with-learning-page__td">
                            {user.total_courses > 0 ? (
                              <div className="users-with-learning-page__status">
                                {user.is_fully_completed ? (
                                  <span className="users-with-learning-page__status-badge users-with-learning-page__status-badge--success">
                                    <i className="fas fa-check" aria-hidden />
                                    Завершено
                                  </span>
                                ) : user.completed_courses > 0 ? (
                                  <span className="users-with-learning-page__status-badge users-with-learning-page__status-badge--warning">
                                    <i className="fas fa-clock" aria-hidden />
                                    В процессе
                                  </span>
                                ) : (
                                  <span className="users-with-learning-page__status-badge users-with-learning-page__status-badge--info">
                                    <i className="fas fa-play" aria-hidden />
                                    Не начато
                                  </span>
                                )}
                                <small className="users-with-learning-page__status-detail">
                                  {user.completed_courses}/{user.total_courses}
                                </small>
                              </div>
                            ) : (
                              <span className="users-with-learning-page__td--empty">—</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {pagination.num_pages > 1 && (
                  <nav className="users-with-learning-page__pagination" aria-label="Пагинация пользователей">
                    <ul className="users-with-learning-page__pagination-list">
                      {pagination.has_previous && (
                        <>
                          <li className="users-with-learning-page__pagination-item">
                            <button
                              type="button"
                              className="users-with-learning-page__pagination-link"
                              onClick={() => setPage(1)}
                            >
                              Первая
                            </button>
                          </li>
                          <li className="users-with-learning-page__pagination-item">
                            <button
                              type="button"
                              className="users-with-learning-page__pagination-link"
                              onClick={() => setPage(pagination.previous_page_number)}
                            >
                              Предыдущая
                            </button>
                          </li>
                        </>
                      )}
                      <li className="users-with-learning-page__pagination-item users-with-learning-page__pagination-item--current">
                        <span className="users-with-learning-page__pagination-current">
                          Страница {pagination.page} из {pagination.num_pages}
                        </span>
                      </li>
                      {pagination.has_next && (
                        <>
                          <li className="users-with-learning-page__pagination-item">
                            <button
                              type="button"
                              className="users-with-learning-page__pagination-link"
                              onClick={() => setPage(pagination.next_page_number)}
                            >
                              Следующая
                            </button>
                          </li>
                          <li className="users-with-learning-page__pagination-item">
                            <button
                              type="button"
                              className="users-with-learning-page__pagination-link"
                              onClick={() => setPage(pagination.num_pages)}
                            >
                              Последняя
                            </button>
                          </li>
                        </>
                      )}
                    </ul>
                  </nav>
                )}
              </>
            ) : (
              <div className="users-with-learning-page__empty" role="alert">
                <i className="fas fa-users users-with-learning-page__empty-icon" aria-hidden />
                <h3 className="users-with-learning-page__empty-title">Пользователи не найдены</h3>
                <p className="users-with-learning-page__empty-desc">
                  Попробуйте изменить параметры поиска или фильтры
                </p>
              </div>
            )}
          </div>
        </section>
      </div>
    </main>
  );
};

export default UsersWithLearningPage;
