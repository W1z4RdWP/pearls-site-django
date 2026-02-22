import { useState, useEffect, useCallback } from 'react';
import { fetchTrajectoryManagementData } from '../../../api/builder_api';
import './TrajectoryManagementPage.css';

const STAT_CARDS = [
  { key: 'lessons', label: 'Уроки', valueKey: 'total_lessons', urlKey: 'lesson_master', icon: 'fas fa-book', variant: 'success' },
  { key: 'courses', label: 'Курсы', valueKey: 'total_courses', urlKey: 'course_list', icon: 'fas fa-graduation-cap', variant: 'primary' },
  { key: 'incident_courses', label: 'Курсы-инциденты', valueKey: 'total_incident_courses', urlKey: 'incident_course_list', icon: 'fas fa-exclamation-triangle', variant: 'danger' },
  { key: 'trajectories', label: 'Траектории', valueKey: 'total_trajectories', urlKey: 'trajectory_list', icon: 'fas fa-route', variant: 'info' },
  { key: 'quizzes', label: 'Тесты', valueKey: 'total_quizzes', urlKey: 'quizzes', icon: 'fas fa-question-circle', variant: 'warning' },
];

const QUICK_ACTIONS = [
  { label: 'Создать урок', urlKey: 'lesson_master', icon: 'fas fa-plus-circle', variant: 'success' },
  { label: 'Создать курс', urlKey: 'create_course', icon: 'fas fa-graduation-cap', variant: 'primary' },
  { label: 'Создать курс-инцидент', urlKey: 'create_course_incident', icon: 'fas fa-exclamation-triangle', variant: 'danger' },
  { label: 'Создать траекторию', urlKey: 'trajectory_create', icon: 'fas fa-route', variant: 'info' },
  { label: 'Создать тест', urlKey: 'quiz_create', icon: 'fas fa-question-circle', variant: 'warning', isExternal: true },
];

const TrajectoryManagementPage = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchTrajectoryManagementData();
      setData(res);
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

  if (loading) {
    return (
      <main className="trajectory-mgmt">
        <div className="trajectory-mgmt__loading" role="status" aria-label="Загрузка">
          <p>Загрузка...</p>
        </div>
      </main>
    );
  }

  if (error) {
    return (
      <main className="trajectory-mgmt">
        <div className="trajectory-mgmt__error" role="alert">
          <p>{error}</p>
        </div>
      </main>
    );
  }

  if (!data) return null;

  const urls = data.urls || {};

  return (
    <main className="trajectory-mgmt">
      <header className="trajectory-mgmt__header">
        <h1 className="trajectory-mgmt__title">
          <i className="fas fa-route trajectory-mgmt__title-icon" aria-hidden />
          Управление траекториями
        </h1>
        <p className="trajectory-mgmt__subtitle">Централизованное управление контентом платформы</p>
      </header>

      <section className="trajectory-mgmt__stats" aria-label="Статистика">
        <div className="trajectory-mgmt__stats-row">
          {STAT_CARDS.map(({ key, label, valueKey, urlKey, icon, variant }) => (
            <a
              key={key}
              href={urls[urlKey] || '#'}
              className="trajectory-mgmt__stat-link"
            >
              <div className={`trajectory-mgmt__stat-card trajectory-mgmt__stat-card--${variant}`}>
                <div className="trajectory-mgmt__stat-body">
                  <span className="trajectory-mgmt__stat-label">{label}</span>
                  <span className="trajectory-mgmt__stat-value">{data[valueKey] ?? 0}</span>
                </div>
                <div className="trajectory-mgmt__stat-icon">
                  <i className={`${icon} trajectory-mgmt__stat-icon-i`} aria-hidden />
                </div>
              </div>
            </a>
          ))}
        </div>
      </section>

      <section className="trajectory-mgmt__quick" aria-label="Быстрые действия">
        <div className="trajectory-mgmt__card">
          <div className="trajectory-mgmt__card-header">
            <h2 className="trajectory-mgmt__card-title">Быстрые действия</h2>
          </div>
          <div className="trajectory-mgmt__card-body">
            <div className="trajectory-mgmt__quick-row">
              {QUICK_ACTIONS.map(({ label, urlKey, icon, variant }) => (
                <a
                  key={urlKey}
                  href={urls[urlKey] || '#'}
                  className="trajectory-mgmt__quick-link"
                >
                  <div className={`trajectory-mgmt__quick-card trajectory-mgmt__quick-card--${variant}`}>
                    <i className={`${icon} trajectory-mgmt__quick-icon`} aria-hidden />
                    <h3 className="trajectory-mgmt__quick-title">{label}</h3>
                  </div>
                </a>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="trajectory-mgmt__recent" aria-label="Последние элементы">
        <div className="trajectory-mgmt__recent-grid">
          <RecentCard
            title="Последние уроки"
            href={urls.lesson_master}
            variant="success"
            items={data.recent_lessons}
            emptyText="Уроки не найдены"
            renderItem={(lesson) => (
              <>
                <div>
                  <h4 className="trajectory-mgmt__recent-item-title">{lesson.title}</h4>
                  <small className="trajectory-mgmt__recent-item-meta">
                    {lesson.category ? `Категория: ${lesson.category.name}` : 'Без категории'}
                  </small>
                </div>
                {lesson.video_id && (
                  <i className="fas fa-video trajectory-mgmt__recent-item-badge trajectory-mgmt__recent-item-badge--info" aria-hidden />
                )}
              </>
            )}
          />
          <RecentCard
            title="Последние курсы"
            href={urls.course_list}
            variant="primary"
            items={data.recent_courses}
            emptyText="Курсы не найдены"
            renderItem={(course) => (
              <>
                <div>
                  <h4 className="trajectory-mgmt__recent-item-title">{course.title}</h4>
                  <small className="trajectory-mgmt__recent-item-meta">Автор: {course.author_name}</small>
                </div>
                <span className="trajectory-mgmt__badge trajectory-mgmt__badge--primary">{course.lesson_count} уроков</span>
              </>
            )}
          />
          <RecentCard
            title="Последние траектории"
            href={urls.trajectory_list}
            variant="info"
            items={data.recent_trajectories}
            emptyText="Траектории не найдены"
            renderItem={(trajectory) => (
              <>
                <div>
                  <h4 className="trajectory-mgmt__recent-item-title">{trajectory.name}</h4>
                  <small className="trajectory-mgmt__recent-item-meta">{trajectory.course_count} курсов</small>
                </div>
                <span className="trajectory-mgmt__badge trajectory-mgmt__badge--info">{trajectory.group_count} групп</span>
              </>
            )}
          />
          <RecentCard
            title="Последние тесты"
            href={urls.quizzes}
            variant="warning"
            items={data.recent_quizzes}
            emptyText="Тесты не найдены"
            renderItem={(quiz) => (
              <>
                <div>
                  <h4 className="trajectory-mgmt__recent-item-title">{quiz.name}</h4>
                  <small className="trajectory-mgmt__recent-item-meta">{quiz.question_count} вопросов</small>
                </div>
                <span className="trajectory-mgmt__badge trajectory-mgmt__badge--warning">Тест</span>
              </>
            )}
          />
        </div>
      </section>
    </main>
  );
};

const RecentCard = ({ title, href, variant, items, emptyText, renderItem }) => (
  <a href={href} className="trajectory-mgmt__recent-link">
    <div className="trajectory-mgmt__card trajectory-mgmt__card--clickable">
      <div className={`trajectory-mgmt__card-header trajectory-mgmt__card-header--${variant}`}>
        <h2 className="trajectory-mgmt__card-title">{title}</h2>
      </div>
      <div className="trajectory-mgmt__card-body">
        {items && items.length > 0 ? (
          <ul className="trajectory-mgmt__recent-list">
            {items.map((item) => (
              <li key={item.id} className="trajectory-mgmt__recent-item">
                {renderItem(item)}
              </li>
            ))}
          </ul>
        ) : (
          <p className="trajectory-mgmt__recent-empty">{emptyText}</p>
        )}
      </div>
    </div>
  </a>
);

export default TrajectoryManagementPage;
