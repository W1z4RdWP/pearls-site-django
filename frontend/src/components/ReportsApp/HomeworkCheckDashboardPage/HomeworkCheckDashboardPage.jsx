import { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { fetchHomeworkCheckDashboard } from '../../../api/reports_api';
import './HomeworkCheckDashboardPage.css';

const HomeworkCheckDashboardPage = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchHomeworkCheckDashboard();
      setData(result);
    } catch (err) {
      setError(err.message || 'Ошибка загрузки данных');
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleRowClick = (userId) => {
    navigate(`/user_management/users/${userId}/progress`);
  };

  if (loading) {
    return (
      <main className="homework-check-dashboard" aria-label="Проверка заданий">
        <div className="homework-check-dashboard__loading">Загрузка...</div>
      </main>
    );
  }

  if (error) {
    return (
      <main className="homework-check-dashboard" aria-label="Проверка заданий">
        <div className="homework-check-dashboard__error" role="alert">
          <p>{error}</p>
        </div>
      </main>
    );
  }

  const isAdmin = data?.is_admin ?? false;
  const subtitle = isAdmin
    ? 'Общая статистика платформы'
    : 'Статистика по вашим группам';

  return (
    <main className="homework-check-dashboard" aria-label="Проверка заданий">
      <div className="homework-check-dashboard__container">
        <header className="homework-check-dashboard__header">
          <div className="homework-check-dashboard__title-wrap">
            <h1 className="homework-check-dashboard__title">
              <i className="fas fa-clipboard-check" aria-hidden />
              Проверка заданий
            </h1>
            <p className="homework-check-dashboard__subtitle">{subtitle}</p>
          </div>
          <div className="homework-check-dashboard__actions">
            <Link to="/builder" className="homework-check-dashboard__btn-back">
              <i className="fas fa-arrow-left" aria-hidden />
              Назад к панели
            </Link>
          </div>
        </header>

        <section className="homework-check-dashboard__stats" aria-label="Статистика">
          <Link to="/reports/courses-progress" className="homework-check-dashboard__stat-card">
            <div className="homework-check-dashboard__stat-body">
              <i className="fas fa-file-alt homework-check-dashboard__stat-icon homework-check-dashboard__stat-icon--primary" aria-hidden />
              <h3 className="homework-check-dashboard__stat-value">{data.total_materials}</h3>
              <p className="homework-check-dashboard__stat-label">
                {isAdmin ? 'материала' : 'материала в ваших группах'}
              </p>
              <small className="homework-check-dashboard__stat-meta">
                {data.total_lessons} уроков + {data.total_quizzes} тестов
              </small>
            </div>
          </Link>
          <Link to="/reports/users-with-learning" className="homework-check-dashboard__stat-card homework-check-dashboard__stat-card--hover">
            <div className="homework-check-dashboard__stat-body">
              <i className="fas fa-user homework-check-dashboard__stat-icon homework-check-dashboard__stat-icon--success" aria-hidden />
              <h3 className="homework-check-dashboard__stat-value">{data.active_users}</h3>
              <p className="homework-check-dashboard__stat-label">
                {isAdmin ? 'пользователей' : 'студентов в ваших группах'}
              </p>
            </div>
          </Link>
          <Link to="/reports/groups-progress" className="homework-check-dashboard__stat-card homework-check-dashboard__stat-card--hover">
            <div className="homework-check-dashboard__stat-body">
              <i className="fas fa-users homework-check-dashboard__stat-icon homework-check-dashboard__stat-icon--info" aria-hidden />
              <h3 className="homework-check-dashboard__stat-value">{data.total_groups}</h3>
              <p className="homework-check-dashboard__stat-label">
                {isAdmin ? 'групп' : 'ваших групп'}
              </p>
            </div>
          </Link>
          <a href="/quizzes/pending/" className="homework-check-dashboard__stat-card homework-check-dashboard__stat-card--hover">
            <div className="homework-check-dashboard__stat-body">
              <i className="fas fa-clipboard-check homework-check-dashboard__stat-icon homework-check-dashboard__stat-icon--warning" aria-hidden />
              <h3 className="homework-check-dashboard__stat-value">{data.pending_tests_count}</h3>
              <p className="homework-check-dashboard__stat-label">тестов на проверку</p>
            </div>
          </a>
        </section>

        <section className="homework-check-dashboard__card">
          <div className="homework-check-dashboard__card-header">
            <h2 className="homework-check-dashboard__card-title">Последние завершения</h2>
            <p className="homework-check-dashboard__card-desc">
              10 последних пользователей, завершивших урок/тест
            </p>
          </div>
          <div className="homework-check-dashboard__card-body">
            <div className="homework-check-dashboard__table-wrap">
              <table className="homework-check-dashboard__table">
                <thead>
                  <tr>
                    <th className="homework-check-dashboard__th homework-check-dashboard__th--n">#</th>
                    <th className="homework-check-dashboard__th">ФИО</th>
                    <th className="homework-check-dashboard__th">Курс</th>
                    <th className="homework-check-dashboard__th">Урок/Тест</th>
                    <th className="homework-check-dashboard__th">Время завершения</th>
                  </tr>
                </thead>
                <tbody>
                  {data.recent_completions && data.recent_completions.length > 0 ? (
                    data.recent_completions.map((item, index) => (
                      <tr
                        key={`${item.user_id}-${item.completed_at}-${index}`}
                        className="homework-check-dashboard__row homework-check-dashboard__row--clickable"
                        onClick={() => handleRowClick(item.user_id)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' || e.key === ' ') {
                            e.preventDefault();
                            handleRowClick(item.user_id);
                          }
                        }}
                        role="button"
                        tabIndex={0}
                        aria-label={`Перейти к прогрессу: ${item.fio_short}`}
                      >
                        <td className="homework-check-dashboard__td homework-check-dashboard__td--muted">{index + 1}</td>
                        <td className="homework-check-dashboard__td">{item.fio_short}</td>
                        <td className="homework-check-dashboard__td">{item.course_title || '—'}</td>
                        <td className="homework-check-dashboard__td">{item.material_title || '—'}</td>
                        <td className="homework-check-dashboard__td">{item.completed_at}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={5} className="homework-check-dashboard__td homework-check-dashboard__td--empty">
                        <i className="fas fa-clipboard-list homework-check-dashboard__empty-icon" aria-hidden />
                        <br />
                        Нет данных о завершениях
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
};

export default HomeworkCheckDashboardPage;
