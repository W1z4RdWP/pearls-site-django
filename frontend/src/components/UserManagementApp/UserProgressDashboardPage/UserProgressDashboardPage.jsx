import { useState, useEffect, useCallback } from 'react';
import { Link, useParams, useSearchParams } from 'react-router-dom';
import { fetchUserProgressDashboard } from '../../../api/user_management_api';
import './UserProgressDashboardPage.css';

const formatAttempts = (n) => {
  if (n === 1) return '1 попытка';
  if (n >= 2 && n < 5) return `${n} попытки`;
  return `${n} попыток`;
};

const UserProgressDashboardPage = () => {
  const { userId } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const courseFilter = searchParams.get('course_filter') || 'completed';
  const coursesPage = Math.max(1, parseInt(searchParams.get('courses_page') || '1', 10) || 1);

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadData = useCallback(async () => {
    if (!userId) return;
    setLoading(true);
    setError(null);
    try {
      const result = await fetchUserProgressDashboard(userId, courseFilter, coursesPage);
      setData(result);
    } catch (err) {
      setError(err.message || 'Ошибка загрузки прогресса');
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [userId, courseFilter, coursesPage]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleFilterChange = (filter) => {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      next.set('course_filter', filter);
      next.delete('courses_page');
      return next;
    });
  };

  const handlePageChange = (page) => {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      next.set('courses_page', String(page));
      return next;
    });
  };

  if (loading) {
    return (
      <main className="user-progress-dashboard" aria-label="Прогресс пользователя">
        <div className="user-progress-dashboard__loading">Загрузка...</div>
      </main>
    );
  }

  if (error) {
    return (
      <main className="user-progress-dashboard" aria-label="Прогресс пользователя">
        <div className="user-progress-dashboard__error" role="alert">
          <p>{error}</p>
          <Link to="/user_management/users" className="user-progress-dashboard__link">
            Вернуться к списку пользователей
          </Link>
        </div>
      </main>
    );
  }

  if (!data) return null;

  const {
    target_user: targetUser,
    overall_progress: overallProgress,
    total_lessons_completed: totalLessonsCompleted,
    total_lessons_available: totalLessonsAvailable,
    total_courses: totalCourses,
    completed_courses: completedCourses,
    started_courses: startedCourses,
    course_filter: currentFilter,
    items,
    pagination,
  } = data;

  const completedPercent = totalCourses > 0 ? Math.round((completedCourses / totalCourses) * 100) : 0;
  const exportExcelUrl = `/user_management/users/${targetUser.id}/progress/export_excel/`;
  const quizReportUrl = (quizResultId) => `/user_management/users/quiz_report/${quizResultId}/`;

  return (
    <main className="user-progress-dashboard" aria-label="Прогресс пользователя">
      <div className="user-progress-dashboard__wrapper">
        <header className="user-progress-dashboard__header">
          <h1 className="user-progress-dashboard__title">
            <i className="fas fa-chart-line" aria-hidden />
            Прогресс пользователя
          </h1>
          <div className="user-progress-dashboard__actions">
            <a href={exportExcelUrl} className="user-progress-dashboard__btn user-progress-dashboard__btn--success">
              <i className="fas fa-file-excel" aria-hidden /> Экспорт в Excel
            </a>
            <Link to="/user_management/users" className="user-progress-dashboard__btn user-progress-dashboard__btn--secondary">
              <i className="fas fa-arrow-left" aria-hidden /> Вернуться к списку пользователей
            </Link>
          </div>
        </header>

        <section className="user-progress-dashboard__user-card">
          <div className="user-progress-dashboard__user-row">
            <div className="user-progress-dashboard__user-avatar-wrap">
              {targetUser.profile?.image_url ? (
                <img
                  src={targetUser.profile.image_url}
                  alt=""
                  className="user-progress-dashboard__user-avatar"
                />
              ) : (
                <div className="user-progress-dashboard__user-avatar user-progress-dashboard__user-avatar--placeholder" aria-hidden />
              )}
            </div>
            <div className="user-progress-dashboard__user-info">
              {(targetUser.is_staff || targetUser.is_superuser) && (
                <span className="user-progress-dashboard__admin-badge">
                  <i className="fas fa-user-shield" aria-hidden /> Администратор УЦ
                </span>
              )}
              <h2 className="user-progress-dashboard__user-name">{targetUser.full_name}</h2>
              <p className="user-progress-dashboard__user-email">{targetUser.email}</p>
              <p className="user-progress-dashboard__user-groups">
                <strong>Группы:</strong>{' '}
                {targetUser.groups?.length > 0
                  ? targetUser.groups.map((g) => (
                      <span key={g} className="user-progress-dashboard__badge">
                        {g}
                      </span>
                    ))
                  : <span className="user-progress-dashboard__muted">Не назначены</span>}
              </p>
            </div>
          </div>
        </section>

        <section className="user-progress-dashboard__stats" aria-label="Общая статистика">
          <div className="user-progress-dashboard__stats-grid">
            <button
              type="button"
              className={`user-progress-dashboard__stat-card ${currentFilter === 'all' ? 'user-progress-dashboard__stat-card--active' : ''}`}
              onClick={() => handleFilterChange('all')}
            >
              <h3>Общий прогресс</h3>
              <div className="user-progress-dashboard__stat-value">{overallProgress}%</div>
              <div className="user-progress-dashboard__stat-desc">
                {totalLessonsCompleted} из {totalLessonsAvailable} уроков
              </div>
            </button>
            <button
              type="button"
              className={`user-progress-dashboard__stat-card ${currentFilter === 'all' ? 'user-progress-dashboard__stat-card--active' : ''}`}
              onClick={() => handleFilterChange('all')}
            >
              <h3>Всего курсов</h3>
              <div className="user-progress-dashboard__stat-value">{totalCourses}</div>
              <div className="user-progress-dashboard__stat-desc">
                {completedCourses} завершено, {startedCourses} в процессе
              </div>
            </button>
            <button
              type="button"
              className={`user-progress-dashboard__stat-card ${currentFilter === 'completed' ? 'user-progress-dashboard__stat-card--active' : ''}`}
              onClick={() => handleFilterChange('completed')}
            >
              <h3>Завершенные курсы</h3>
              <div className="user-progress-dashboard__stat-value">{completedCourses}</div>
              <div className="user-progress-dashboard__stat-desc">
                {totalCourses > 0 ? `${completedPercent}% от общего числа` : 'Нет курсов'}
              </div>
            </button>
            <button
              type="button"
              className={`user-progress-dashboard__stat-card ${currentFilter === 'started' ? 'user-progress-dashboard__stat-card--active' : ''}`}
              onClick={() => handleFilterChange('started')}
            >
              <h3>Курсы в процессе</h3>
              <div className="user-progress-dashboard__stat-value">{startedCourses}</div>
              <div className="user-progress-dashboard__stat-desc">Активно изучаются</div>
            </button>
          </div>
        </section>

        <section className="user-progress-dashboard__courses">
          <h2 className="user-progress-dashboard__courses-title">Детальный прогресс по курсам</h2>

          {items && items.length > 0 ? (
            <>
              {items.map((cp) => (
                <article key={cp.course.title} className="user-progress-dashboard__course-card">
                  <div className="user-progress-dashboard__course-header">
                    <div className="user-progress-dashboard__course-info">
                      <h3 className="user-progress-dashboard__course-title">{cp.course.title}</h3>
                      <div className="user-progress-dashboard__course-meta">
                        <span className={`user-progress-dashboard__course-status user-progress-dashboard__course-status--${cp.user_course.status}`}>
                          {cp.user_course.status === 'completed' && 'Завершен'}
                          {cp.user_course.status === 'started' && 'В процессе'}
                          {cp.user_course.status === 'available' && 'Доступен'}
                        </span>
                        <span className="user-progress-dashboard__course-date">
                          Начат: {cp.user_course.start_date}
                        </span>
                        {cp.user_course.end_date && (
                          <span className="user-progress-dashboard__course-date">
                            Завершен: {cp.user_course.end_date}
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="user-progress-dashboard__course-stats">
                      <div className="user-progress-dashboard__course-progress">
                        <div className="user-progress-dashboard__progress-bar">
                          <div
                            className="user-progress-dashboard__progress-bar-fill"
                            style={{ width: `${cp.progress_percent}%` }}
                          />
                        </div>
                        <span className="user-progress-dashboard__progress-percent">{cp.progress_percent}%</span>
                      </div>
                      <div className="user-progress-dashboard__lessons-count">
                        {cp.completed_lessons} из {cp.total_lessons} уроков
                        {cp.total_quizzes > 0 && `, ${cp.completed_quizzes} из ${cp.total_quizzes} тестов`}
                      </div>
                    </div>
                  </div>

                  {cp.course.final_quiz && (
                    <div className="user-progress-dashboard__quiz-info">
                      <h4>Финальный тест: {cp.course.final_quiz.name}</h4>
                      <div className="user-progress-dashboard__quiz-status">
                        {cp.quiz_passed ? (
                          <span className="user-progress-dashboard__quiz-passed">✓ Пройден</span>
                        ) : (
                          <span className="user-progress-dashboard__quiz-not-passed">✗ Не пройден</span>
                        )}
                        {cp.best_attempt_id && (
                          <a
                            href={quizReportUrl(cp.best_attempt_id)}
                            className="user-progress-dashboard__btn user-progress-dashboard__btn--outline"
                          >
                            Отчёт
                          </a>
                        )}
                      </div>
                    </div>
                  )}

                  <div className="user-progress-dashboard__lessons-detail">
                    <h4>Материалы курса</h4>
                    <ul className="user-progress-dashboard__lessons-list">
                      {cp.lessons_detail.map((material, idx) => (
                        <li
                          key={`${material.order}-${material.title}-${idx}`}
                          className={`user-progress-dashboard__lesson-item ${material.completed ? 'user-progress-dashboard__lesson-item--completed' : ''}`}
                        >
                          <div className="user-progress-dashboard__lesson-info">
                            <span className="user-progress-dashboard__lesson-order">{material.order}.</span>
                            <span className="user-progress-dashboard__lesson-title">
                              {material.type === 'lesson' && '📄 '}
                              {material.type === 'quiz' && '🎓 '}
                              {material.title}
                            </span>
                          </div>
                          <div className="user-progress-dashboard__lesson-status">
                            {material.completed ? (
                              <>
                                <span className="user-progress-dashboard__lesson-badge user-progress-dashboard__lesson-badge--done">✓</span>
                                <span className="user-progress-dashboard__lesson-date">{material.completed_at}</span>
                              </>
                            ) : (
                              <span className="user-progress-dashboard__lesson-badge">○</span>
                            )}
                            {material.type === 'quiz' && material.attempts_count > 0 && (
                              <div className="user-progress-dashboard__quiz-attempts">
                                <small className="user-progress-dashboard__attempts-count">
                                  {formatAttempts(material.attempts_count)}
                                </small>
                                {material.best_attempt_id && (
                                  <a
                                    href={quizReportUrl(material.best_attempt_id)}
                                    className="user-progress-dashboard__btn user-progress-dashboard__btn--sm"
                                    title="Лучший результат"
                                  >
                                    Отчёт
                                  </a>
                                )}
                              </div>
                            )}
                          </div>
                        </li>
                      ))}
                    </ul>
                  </div>

                  {cp.user_course.status === 'completed' && !cp.course.is_incident && (
                    <div className="user-progress-dashboard__rewards">
                      <h4>Награды за курс</h4>
                      <div className="user-progress-dashboard__rewards-grid">
                        <div className="user-progress-dashboard__reward-item">
                          <span className="user-progress-dashboard__reward-icon">💎</span>
                          <span className="user-progress-dashboard__reward-text">{cp.course.points} DASCOIN</span>
                        </div>
                        {cp.course_badges?.map((badge, idx) => (
                          <div key={idx} className="user-progress-dashboard__reward-item">
                            <span className="user-progress-dashboard__reward-icon">
                              {badge.icon_url ? (
                                <img src={badge.icon_url} alt="" className="user-progress-dashboard__badge-icon" />
                              ) : (
                                <i className="fas fa-medal" aria-hidden />
                              )}
                            </span>
                            <span className="user-progress-dashboard__reward-text">{badge.name}</span>
                            {badge.earned_at && (
                              <small className="user-progress-dashboard__reward-date">{badge.earned_at}</small>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </article>
              ))}

              {pagination && pagination.num_pages > 1 && (
                <nav className="user-progress-dashboard__pagination" aria-label="Навигация по страницам">
                  <ul className="user-progress-dashboard__pagination-list">
                    {pagination.has_previous && (
                      <li>
                        <button
                          type="button"
                          className="user-progress-dashboard__page-link"
                          onClick={() => handlePageChange(pagination.previous_page_number)}
                        >
                          Назад
                        </button>
                      </li>
                    )}
                    {Array.from({ length: pagination.num_pages }, (_, i) => i + 1).map((num) => (
                      <li key={num}>
                        <button
                          type="button"
                          className={`user-progress-dashboard__page-link ${pagination.page === num ? 'user-progress-dashboard__page-link--active' : ''}`}
                          onClick={() => handlePageChange(num)}
                        >
                          {num}
                        </button>
                      </li>
                    ))}
                    {pagination.has_next && (
                      <li>
                        <button
                          type="button"
                          className="user-progress-dashboard__page-link"
                          onClick={() => handlePageChange(pagination.next_page_number)}
                        >
                          Вперед
                        </button>
                      </li>
                    )}
                  </ul>
                </nav>
              )}
            </>
          ) : (
            <div className="user-progress-dashboard__no-courses">
              <p>У пользователя нет назначенных курсов.</p>
            </div>
          )}
        </section>
      </div>
    </main>
  );
};

export default UserProgressDashboardPage;
