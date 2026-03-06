import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { fetchCourseAssignmentsDetail } from '../../../api/reports_api';
import './CourseAssignmentsDetailPage.css';

const STATUS_BADGES = {
  completed: { label: 'Завершен', className: 'course-assignments-detail-page__badge--success' },
  started: { label: 'В процессе', className: 'course-assignments-detail-page__badge--warning' },
  available: { label: 'Не начат', className: 'course-assignments-detail-page__badge--secondary' },
  blocked: { label: 'Заблокирован', className: 'course-assignments-detail-page__badge--danger' },
};

const CourseAssignmentsDetailPage = () => {
  const { courseId } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1);

  const loadData = useCallback(async () => {
    if (!courseId) return;
    setLoading(true);
    setError(null);
    try {
      const result = await fetchCourseAssignmentsDetail(Number(courseId), { page });
      setData(result);
    } catch (err) {
      setError(err.message || 'Ошибка загрузки данных');
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [courseId, page]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleBack = () => {
    navigate('/reports/courses-progress');
  };

  const handleRowDoubleClick = (userId) => {
    navigate(`/user_management/users/${userId}/progress`);
  };

  const getStatusBadge = (status) => {
    const config = STATUS_BADGES[status] || { label: '-', className: 'course-assignments-detail-page__badge--default' };
    return (
      <span className={`course-assignments-detail-page__badge ${config.className}`}>
        {config.label}
      </span>
    );
  };

  if (loading && !data) {
    return (
      <main className="course-assignments-detail-page" aria-label="Назначения курса">
        <div className="course-assignments-detail-page__loading">Загрузка...</div>
      </main>
    );
  }

  if (error && !data) {
    return (
      <main className="course-assignments-detail-page" aria-label="Назначения курса">
        <div className="course-assignments-detail-page__error" role="alert">
          <p>{error}</p>
          <button type="button" className="course-assignments-detail-page__btn course-assignments-detail-page__btn--primary" onClick={handleBack}>
            К списку курсов
          </button>
        </div>
      </main>
    );
  }

  const course = data?.course ?? {};
  const items = data?.items ?? [];
  const pagination = data?.pagination ?? {};

  return (
    <main className="course-assignments-detail-page" aria-label="Назначения курса">
      <div className="course-assignments-detail-page__container">
        <header className="course-assignments-detail-page__header">
          <div className="course-assignments-detail-page__title-wrap">
            <h1 className="course-assignments-detail-page__title">
              <i className="fa-solid fa-book-open-reader" aria-hidden />
              Назначения курса
            </h1>
            <p className="course-assignments-detail-page__subtitle">
              Курс: <strong>{course.title}</strong>
            </p>
          </div>
          <div className="course-assignments-detail-page__actions">
            <button
              type="button"
              className="course-assignments-detail-page__btn course-assignments-detail-page__btn--secondary"
              onClick={handleBack}
              aria-label="Вернуться к списку курсов"
            >
              <i className="fas fa-arrow-left" aria-hidden />
              К списку курсов
            </button>
          </div>
        </header>

        <section className="course-assignments-detail-page__stats" aria-label="Сводка по назначениям">
          <div className="course-assignments-detail-page__stat-card">
            <div className="course-assignments-detail-page__stat-body">
              <p className="course-assignments-detail-page__stat-label">Всего назначений</p>
              <h3 className="course-assignments-detail-page__stat-value">{data?.total_assignments ?? 0}</h3>
            </div>
          </div>
          <div className="course-assignments-detail-page__stat-card">
            <div className="course-assignments-detail-page__stat-body">
              <p className="course-assignments-detail-page__stat-label">Завершено</p>
              <h3 className="course-assignments-detail-page__stat-value course-assignments-detail-page__stat-value--success">
                {data?.completed_assignments ?? 0}
              </h3>
            </div>
          </div>
          <div className="course-assignments-detail-page__stat-card">
            <div className="course-assignments-detail-page__stat-body">
              <p className="course-assignments-detail-page__stat-label">В процессе</p>
              <h3 className="course-assignments-detail-page__stat-value course-assignments-detail-page__stat-value--warning">
                {data?.in_progress_assignments ?? 0}
              </h3>
            </div>
          </div>
          <div className="course-assignments-detail-page__stat-card">
            <div className="course-assignments-detail-page__stat-body">
              <p className="course-assignments-detail-page__stat-label">Не начато</p>
              <h3 className="course-assignments-detail-page__stat-value course-assignments-detail-page__stat-value--secondary">
                {data?.available_assignments ?? 0}
              </h3>
            </div>
          </div>
        </section>

        <section className="course-assignments-detail-page__card">
          <div className="course-assignments-detail-page__card-header">
            <h2 className="course-assignments-detail-page__card-title">
              Пользователи ({items.length})
            </h2>
            <small className="course-assignments-detail-page__card-subtitle">
              Средний прогресс: <strong>{data?.learning_percentage ?? 0}%</strong>
            </small>
          </div>
          <div className="course-assignments-detail-page__card-body">
            {items.length > 0 ? (
              <>
                <div className="course-assignments-detail-page__table-wrap">
                  <table className="course-assignments-detail-page__table">
                    <thead>
                      <tr>
                        <th className="course-assignments-detail-page__th course-assignments-detail-page__th--user">Пользователь</th>
                        <th className="course-assignments-detail-page__th course-assignments-detail-page__th--email">Email</th>
                        <th className="course-assignments-detail-page__th course-assignments-detail-page__th--status">Статус</th>
                        <th className="course-assignments-detail-page__th course-assignments-detail-page__th--date">Назначено</th>
                        <th className="course-assignments-detail-page__th course-assignments-detail-page__th--date">Завершено</th>
                      </tr>
                    </thead>
                    <tbody>
                      {items.map((assignment) => (
                        <tr
                          key={assignment.user_id}
                          className="course-assignments-detail-page__row course-assignments-detail-page__row--clickable"
                          onDoubleClick={() => handleRowDoubleClick(assignment.user_id)}
                          role="button"
                          tabIndex={0}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter' || e.key === ' ') {
                              e.preventDefault();
                              handleRowDoubleClick(assignment.user_id);
                            }
                          }}
                          aria-label={`${assignment.user_full_name}, переход к прогрессу по двойному щелчку`}
                        >
                          <td className="course-assignments-detail-page__td">
                            <strong>{assignment.user_full_name}</strong>
                          </td>
                          <td className="course-assignments-detail-page__td">
                            <small>{assignment.user_email}</small>
                          </td>
                          <td className="course-assignments-detail-page__td">
                            {getStatusBadge(assignment.status)}
                          </td>
                          <td className="course-assignments-detail-page__td">
                            <small>{assignment.start_date}</small>
                          </td>
                          <td className="course-assignments-detail-page__td">
                            <small>{assignment.end_date ?? '—'}</small>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {pagination.num_pages > 1 && (
                  <nav className="course-assignments-detail-page__pagination" aria-label="Навигация по страницам">
                    <ul className="course-assignments-detail-page__pagination-list">
                      {pagination.has_previous && (
                        <>
                          <li className="course-assignments-detail-page__pagination-item">
                            <button
                              type="button"
                              className="course-assignments-detail-page__pagination-link"
                              onClick={() => setPage(1)}
                            >
                              Первая
                            </button>
                          </li>
                          <li className="course-assignments-detail-page__pagination-item">
                            <button
                              type="button"
                              className="course-assignments-detail-page__pagination-link"
                              onClick={() => setPage(pagination.previous_page_number)}
                            >
                              Предыдущая
                            </button>
                          </li>
                        </>
                      )}
                      <li className="course-assignments-detail-page__pagination-item course-assignments-detail-page__pagination-item--current">
                        <span className="course-assignments-detail-page__pagination-current">
                          Страница {pagination.page} из {pagination.num_pages}
                        </span>
                      </li>
                      {pagination.has_next && (
                        <>
                          <li className="course-assignments-detail-page__pagination-item">
                            <button
                              type="button"
                              className="course-assignments-detail-page__pagination-link"
                              onClick={() => setPage(pagination.next_page_number)}
                            >
                              Следующая
                            </button>
                          </li>
                          <li className="course-assignments-detail-page__pagination-item">
                            <button
                              type="button"
                              className="course-assignments-detail-page__pagination-link"
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
              <div className="course-assignments-detail-page__empty" role="alert">
                <i className="fas fa-info-circle" aria-hidden />
                Нет назначений для этого курса.
              </div>
            )}
          </div>
        </section>
      </div>
    </main>
  );
};

export default CourseAssignmentsDetailPage;
