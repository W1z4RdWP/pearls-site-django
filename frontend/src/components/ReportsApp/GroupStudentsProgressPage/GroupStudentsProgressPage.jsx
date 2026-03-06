import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { fetchGroupStudentsProgress } from '../../../api/reports_api';
import './GroupStudentsProgressPage.css';

const GroupStudentsProgressPage = () => {
  const { groupId } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1);

  const loadData = useCallback(async () => {
    if (!groupId) return;
    setLoading(true);
    setError(null);
    try {
      const result = await fetchGroupStudentsProgress(Number(groupId), { page });
      setData(result);
    } catch (err) {
      setError(err.message || 'Ошибка загрузки данных');
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [groupId, page]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleBack = () => {
    navigate('/reports/groups-progress');
  };

  const handleRowClick = (userId) => {
    navigate(`/user_management/users/${userId}/progress`);
  };

  const getProgressBarClass = (pct) => {
    if (pct >= 80) return 'group-students-progress-page__progress-bar--success';
    if (pct >= 50) return 'group-students-progress-page__progress-bar--warning';
    return 'group-students-progress-page__progress-bar--danger';
  };

  if (loading && !data) {
    return (
      <main className="group-students-progress-page" aria-label="Прогресс студентов группы">
        <div className="group-students-progress-page__loading">Загрузка...</div>
      </main>
    );
  }

  if (error && !data) {
    return (
      <main className="group-students-progress-page" aria-label="Прогресс студентов группы">
        <div className="group-students-progress-page__error" role="alert">
          <p>{error}</p>
          <button
            type="button"
            className="group-students-progress-page__btn group-students-progress-page__btn--secondary"
            onClick={handleBack}
          >
            <i className="fas fa-arrow-left" aria-hidden />
            К списку групп
          </button>
        </div>
      </main>
    );
  }

  const group = data?.group ?? {};
  const items = data?.items ?? [];
  const pagination = data?.pagination ?? {};

  return (
    <main className="group-students-progress-page" aria-label="Прогресс студентов группы">
      <div className="group-students-progress-page__container">
        <header className="group-students-progress-page__header">
          <div className="group-students-progress-page__title-wrap">
            <h1 className="group-students-progress-page__title">
              <i className="fas fa-user-graduate" aria-hidden />
              Прогресс студентов
            </h1>
            <p className="group-students-progress-page__subtitle">
              Группа: <strong>{group.name}</strong>
            </p>
          </div>
          <div className="group-students-progress-page__actions">
            <button
              type="button"
              className="group-students-progress-page__btn group-students-progress-page__btn--secondary"
              onClick={handleBack}
              aria-label="Вернуться к списку групп"
            >
              <i className="fas fa-arrow-left" aria-hidden />
              К списку групп
            </button>
          </div>
        </header>

        <section className="group-students-progress-page__card">
          <div className="group-students-progress-page__card-header">
            <h2 className="group-students-progress-page__card-title">Студенты ({items.length})</h2>
          </div>
          <div className="group-students-progress-page__card-body">
            {items.length > 0 ? (
              <>
                <div className="group-students-progress-page__table-wrap">
                  <table className="group-students-progress-page__table">
                    <thead>
                      <tr>
                        <th className="group-students-progress-page__th group-students-progress-page__th--student">
                          Студент
                        </th>
                        <th className="group-students-progress-page__th group-students-progress-page__th--email">
                          Email
                        </th>
                        <th className="group-students-progress-page__th group-students-progress-page__th--courses">
                          Курсы
                        </th>
                        <th className="group-students-progress-page__th group-students-progress-page__th--progress">
                          Прогресс
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {items.map((student) => (
                        <tr
                          key={student.id}
                          className="group-students-progress-page__row group-students-progress-page__row--clickable"
                          onClick={() => handleRowClick(student.id)}
                          role="button"
                          tabIndex={0}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter' || e.key === ' ') {
                              e.preventDefault();
                              handleRowClick(student.id);
                            }
                          }}
                          aria-label={`Студент ${student.full_name}, переход к прогрессу`}
                        >
                          <td className="group-students-progress-page__td">
                            <strong>{student.full_name}</strong>
                          </td>
                          <td className="group-students-progress-page__td">
                            <small>{student.email}</small>
                          </td>
                          <td className="group-students-progress-page__td group-students-progress-page__td--center">
                            <strong className="group-students-progress-page__courses-num">
                              {student.completed_courses}/{student.total_courses}
                            </strong>
                          </td>
                          <td className="group-students-progress-page__td">
                            <div
                              className="group-students-progress-page__progress"
                              role="progressbar"
                              aria-valuenow={student.learning_percentage}
                              aria-valuemin={0}
                              aria-valuemax={100}
                              title={`${student.learning_percentage}% обученность`}
                            >
                              <div
                                className={`group-students-progress-page__progress-bar ${getProgressBarClass(student.learning_percentage)}`}
                                style={{ width: `${student.learning_percentage}%` }}
                              >
                                <span className="group-students-progress-page__progress-text">
                                  {student.learning_percentage}%
                                </span>
                              </div>
                            </div>
                            <small className="group-students-progress-page__progress-legend">
                              <i className="fa-solid fa-check-circle group-students-progress-page__icon-success" aria-hidden />
                              {student.completed_courses}
                              {' / '}
                              <i className="fa-solid fa-spinner group-students-progress-page__icon-warning" aria-hidden />
                              {student.in_progress_courses}
                            </small>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {pagination.num_pages > 1 && (
                  <nav className="group-students-progress-page__pagination" aria-label="Навигация по страницам">
                    <ul className="group-students-progress-page__pagination-list">
                      {pagination.has_previous && (
                        <>
                          <li className="group-students-progress-page__pagination-item">
                            <button
                              type="button"
                              className="group-students-progress-page__pagination-link"
                              onClick={() => setPage(1)}
                            >
                              Первая
                            </button>
                          </li>
                          <li className="group-students-progress-page__pagination-item">
                            <button
                              type="button"
                              className="group-students-progress-page__pagination-link"
                              onClick={() => setPage(pagination.previous_page_number)}
                            >
                              Предыдущая
                            </button>
                          </li>
                        </>
                      )}
                      <li className="group-students-progress-page__pagination-item group-students-progress-page__pagination-item--current">
                        <span className="group-students-progress-page__pagination-current">
                          Страница {pagination.page} из {pagination.num_pages}
                        </span>
                      </li>
                      {pagination.has_next && (
                        <>
                          <li className="group-students-progress-page__pagination-item">
                            <button
                              type="button"
                              className="group-students-progress-page__pagination-link"
                              onClick={() => setPage(pagination.next_page_number)}
                            >
                              Следующая
                            </button>
                          </li>
                          <li className="group-students-progress-page__pagination-item">
                            <button
                              type="button"
                              className="group-students-progress-page__pagination-link"
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
              <div className="group-students-progress-page__empty" role="alert">
                <i className="fas fa-info-circle" aria-hidden />
                В этой группе нет студентов с назначенным обучением.
              </div>
            )}
          </div>
        </section>
      </div>
    </main>
  );
};

export default GroupStudentsProgressPage;
