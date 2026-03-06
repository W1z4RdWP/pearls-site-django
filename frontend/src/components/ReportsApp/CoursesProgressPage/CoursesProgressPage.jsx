import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchCoursesProgress } from '../../../api/reports_api';
import './CoursesProgressPage.css';

const CoursesProgressPage = () => {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchInput, setSearchInput] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [page, setPage] = useState(1);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchCoursesProgress({ page, search: searchQuery });
      setData(result);
    } catch (err) {
      setError(err.message || 'Ошибка загрузки данных');
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [page, searchQuery]);

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

  const handleClearSearch = () => {
    setSearchInput('');
    setSearchQuery('');
    setPage(1);
  };

  const handleRowClick = (courseId) => {
    navigate(`/reports/courses-progress/${courseId}`);
  };

  const getProgressBarClass = (pct) => {
    if (pct >= 80) return 'courses-progress-page__progress-bar--success';
    if (pct >= 50) return 'courses-progress-page__progress-bar--warning';
    return 'courses-progress-page__progress-bar--danger';
  };

  if (loading && !data) {
    return (
      <main className="courses-progress-page" aria-label="Прогресс курсов">
        <div className="courses-progress-page__loading">Загрузка...</div>
      </main>
    );
  }

  if (error && !data) {
    return (
      <main className="courses-progress-page" aria-label="Прогресс курсов">
        <div className="courses-progress-page__error" role="alert">
          <p>{error}</p>
        </div>
      </main>
    );
  }

  const items = data?.items ?? [];
  const pagination = data?.pagination ?? {};
  const totalCourses = data?.total_courses ?? 0;
  const overallPct = data?.overall_learning_percentage ?? 0;

  return (
    <main className="courses-progress-page" aria-label="Прогресс курсов">
      <div className="courses-progress-page__container">
        <header className="courses-progress-page__header">
          <div className="courses-progress-page__title-wrap">
            <h1 className="courses-progress-page__title">
              <i className="fa-solid fa-book-open" aria-hidden />
              Прогресс курсов
            </h1>
            <p className="courses-progress-page__subtitle">
              Показываются только курсы, назначенные пользователям
            </p>
          </div>
          <div className="courses-progress-page__badge" aria-label="Средний процент завершения">
            <i className="fa-solid fa-signal" aria-hidden />
            Средний процент завершения: <strong>{overallPct}%</strong>
          </div>
        </header>

        <section className="courses-progress-page__stats" aria-label="Сводная статистика">
          <div className="courses-progress-page__stat-card">
            <div className="courses-progress-page__stat-body">
              <div className="courses-progress-page__stat-text">
                <p className="courses-progress-page__stat-label">Всего курсов</p>
                <h3 className="courses-progress-page__stat-value">{data?.total_courses ?? 0}</h3>
              </div>
              <span className="courses-progress-page__stat-icon courses-progress-page__stat-icon--primary" aria-hidden>
                <i className="fa-solid fa-layer-group" />
              </span>
            </div>
          </div>
          <div className="courses-progress-page__stat-card">
            <div className="courses-progress-page__stat-body">
              <div className="courses-progress-page__stat-text">
                <p className="courses-progress-page__stat-label">Завершено назначений</p>
                <h3 className="courses-progress-page__stat-value">{data?.completed_assignments_total ?? 0}</h3>
              </div>
              <span className="courses-progress-page__stat-icon courses-progress-page__stat-icon--success" aria-hidden>
                <i className="fa-solid fa-check-circle" />
              </span>
            </div>
          </div>
          <div className="courses-progress-page__stat-card">
            <div className="courses-progress-page__stat-body">
              <div className="courses-progress-page__stat-text">
                <p className="courses-progress-page__stat-label">В процессе</p>
                <h3 className="courses-progress-page__stat-value">{data?.in_progress_assignments_total ?? 0}</h3>
              </div>
              <span className="courses-progress-page__stat-icon courses-progress-page__stat-icon--warning" aria-hidden>
                <i className="fa-solid fa-spinner" />
              </span>
            </div>
          </div>
          <div className="courses-progress-page__stat-card">
            <div className="courses-progress-page__stat-body">
              <div className="courses-progress-page__stat-text">
                <p className="courses-progress-page__stat-label">Не начато</p>
                <h3 className="courses-progress-page__stat-value">{data?.available_assignments_total ?? 0}</h3>
              </div>
              <span className="courses-progress-page__stat-icon courses-progress-page__stat-icon--secondary" aria-hidden>
                <i className="fa-solid fa-circle" />
              </span>
            </div>
          </div>
        </section>

        <section className="courses-progress-page__card">
          <form
            method="get"
            onSubmit={handleSubmit}
            className="courses-progress-page__search-form"
            aria-label="Поиск по курсам"
          >
            <div className="courses-progress-page__search-wrap">
              <input
                type="text"
                name="search"
                className="courses-progress-page__search-input"
                placeholder="Поиск по названию курса..."
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                autoComplete="off"
                aria-label="Поиск по названию курса"
              />
            </div>
            <button type="submit" className="courses-progress-page__btn courses-progress-page__btn--primary">
              <i className="fa-solid fa-magnifying-glass" aria-hidden />
              Поиск
            </button>
            {searchQuery ? (
              <button
                type="button"
                className="courses-progress-page__btn courses-progress-page__btn--secondary"
                onClick={handleClearSearch}
                title="Очистить поиск"
              >
                <i className="fa-solid fa-times" aria-hidden />
                Очистить
              </button>
            ) : null}
          </form>
        </section>

        <section className="courses-progress-page__card">
          <div className="courses-progress-page__card-header">
            <h2 className="courses-progress-page__card-title">Курсы ({totalCourses})</h2>
          </div>
          <div className="courses-progress-page__card-body">
            {items.length > 0 ? (
              <>
                <div className="courses-progress-page__table-wrap">
                  <table className="courses-progress-page__table">
                    <thead>
                      <tr>
                        <th className="courses-progress-page__th courses-progress-page__th--course">Курс</th>
                        <th className="courses-progress-page__th courses-progress-page__th--assigned">Назначено</th>
                        <th className="courses-progress-page__th courses-progress-page__th--progress">
                          Прогресс завершения
                        </th>
                        <th className="courses-progress-page__th courses-progress-page__th--status">Статусы</th>
                      </tr>
                    </thead>
                    <tbody>
                      {items.map((course) => (
                        <tr
                          key={course.id}
                          className="courses-progress-page__row courses-progress-page__row--clickable"
                          onClick={() => handleRowClick(course.id)}
                          role="button"
                          tabIndex={0}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter' || e.key === ' ') {
                              e.preventDefault();
                              handleRowClick(course.id);
                            }
                          }}
                          aria-label={`Курс ${course.title}, переход к деталям`}
                        >
                          <td className="courses-progress-page__td">
                            <strong>{course.title}</strong>
                            <br />
                            <small className="courses-progress-page__td-muted">
                              Назначено пользователям: {course.assigned_users ?? 0}
                            </small>
                          </td>
                          <td className="courses-progress-page__td">
                            <span className="courses-progress-page__badge-num">{course.assigned_users ?? 0}</span>
                            <small className="courses-progress-page__td-muted courses-progress-page__td-block">
                              пользователей
                            </small>
                          </td>
                          <td className="courses-progress-page__td">
                            <div
                              className="courses-progress-page__progress"
                              role="progressbar"
                              aria-valuenow={course.learning_percentage}
                              aria-valuemin={0}
                              aria-valuemax={100}
                              title={`${course.learning_percentage}% завершено`}
                            >
                              <div
                                className={`courses-progress-page__progress-bar ${getProgressBarClass(course.learning_percentage)}`}
                                style={{ width: `${course.learning_percentage}%` }}
                              >
                                <span className="courses-progress-page__progress-text">
                                  {course.learning_percentage}%
                                </span>
                              </div>
                            </div>
                            <small className="courses-progress-page__td-muted courses-progress-page__progress-legend">
                              <i className="fa-solid fa-check-circle courses-progress-page__icon-success" aria-hidden />
                              {course.completed_assignments ?? 0}
                              {' / '}
                              <i className="fa-solid fa-spinner courses-progress-page__icon-warning" aria-hidden />
                              {course.in_progress_assignments ?? 0}
                              {' / '}
                              <i className="fa-solid fa-circle courses-progress-page__icon-secondary" aria-hidden />
                              {course.available_assignments ?? 0}
                            </small>
                          </td>
                          <td className="courses-progress-page__td">
                            <div className="courses-progress-page__status-badges">
                              <span className="courses-progress-page__status-badge courses-progress-page__status-badge--success">
                                Завершено: {course.completed_assignments ?? 0}
                              </span>
                              <span className="courses-progress-page__status-badge courses-progress-page__status-badge--warning">
                                В процессе: {course.in_progress_assignments ?? 0}
                              </span>
                              <span className="courses-progress-page__status-badge courses-progress-page__status-badge--secondary">
                                Не начато: {course.available_assignments ?? 0}
                              </span>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {pagination.num_pages > 1 && (
                  <nav className="courses-progress-page__pagination" aria-label="Навигация по страницам">
                    <ul className="courses-progress-page__pagination-list">
                      {pagination.has_previous && (
                        <>
                          <li className="courses-progress-page__pagination-item">
                            <button
                              type="button"
                              className="courses-progress-page__pagination-link"
                              onClick={() => setPage(1)}
                            >
                              Первая
                            </button>
                          </li>
                          <li className="courses-progress-page__pagination-item">
                            <button
                              type="button"
                              className="courses-progress-page__pagination-link"
                              onClick={() => setPage(pagination.previous_page_number)}
                            >
                              Предыдущая
                            </button>
                          </li>
                        </>
                      )}
                      <li className="courses-progress-page__pagination-item courses-progress-page__pagination-item--current">
                        <span className="courses-progress-page__pagination-current">
                          Страница {pagination.page} из {pagination.num_pages}
                        </span>
                      </li>
                      {pagination.has_next && (
                        <>
                          <li className="courses-progress-page__pagination-item">
                            <button
                              type="button"
                              className="courses-progress-page__pagination-link"
                              onClick={() => setPage(pagination.next_page_number)}
                            >
                              Следующая
                            </button>
                          </li>
                          <li className="courses-progress-page__pagination-item">
                            <button
                              type="button"
                              className="courses-progress-page__pagination-link"
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
              <div className="courses-progress-page__empty" role="alert">
                <i className="fas fa-info-circle" aria-hidden />
                Нет курсов с назначениями для отображения.
              </div>
            )}
          </div>
        </section>
      </div>
    </main>
  );
};

export default CoursesProgressPage;
