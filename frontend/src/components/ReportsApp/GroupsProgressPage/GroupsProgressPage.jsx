import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { fetchGroupsProgress } from '../../../api/reports_api';
import './GroupsProgressPage.css';

const GROUPS_PROGRESS_PAGE_CHART_SIZE = 200;
const GROUPS_PROGRESS_PAGE_CHART_R = 70;
const GROUPS_PROGRESS_PAGE_CHART_STROKE = 28;

/** Строит сегменты круговой диаграммы (доли от 0 до 1). */
function buildDonutSegments(learningData) {
  const total = learningData.reduce((acc, item) => acc + item.value, 0);
  if (total === 0) return [];
  let offset = 0;
  return learningData.map((item) => {
    const fraction = item.value / total;
    const segment = {
      label: item.label,
      color: item.color,
      value: item.value,
      fraction,
      offset,
    };
    offset += fraction;
    return segment;
  });
}

const GroupsProgressPage = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedGroup, setSelectedGroup] = useState('');

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchGroupsProgress({ group: selectedGroup || undefined });
      setData(result);
    } catch (err) {
      setError(err.message || 'Ошибка загрузки данных');
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [selectedGroup]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleFilterChange = (e) => {
    setSelectedGroup(e.target.value);
  };

  const handleResetFilter = () => {
    setSelectedGroup('');
  };

  const getProgressBarClass = (pct) => {
    if (pct >= 80) return 'groups-progress-page__progress-bar--success';
    if (pct >= 50) return 'groups-progress-page__progress-bar--warning';
    return 'groups-progress-page__progress-bar--danger';
  };

  if (loading && !data) {
    return (
      <main className="groups-progress-page" aria-label="Прогресс групп">
        <div className="groups-progress-page__loading">Загрузка...</div>
      </main>
    );
  }

  if (error && !data) {
    return (
      <main className="groups-progress-page" aria-label="Прогресс групп">
        <div className="groups-progress-page__error" role="alert">
          <p>{error}</p>
        </div>
      </main>
    );
  }

  const isAdmin = data?.is_admin ?? false;
  const subtitle = isAdmin
    ? 'Общая статистика по всем группам'
    : 'Статистика по вашим группам';
  const groups = data?.groups ?? [];
  const allAvailableGroups = data?.all_available_groups ?? [];
  const learningData = data?.learning_data ?? [];
  const segments = buildDonutSegments(learningData);
  const totalForChart = learningData.reduce((acc, item) => acc + item.value, 0);

  return (
    <main className="groups-progress-page" aria-label="Прогресс групп">
      <div className="groups-progress-page__container">
        <header className="groups-progress-page__header">
          <div className="groups-progress-page__title-wrap">
            <h1 className="groups-progress-page__title">
              <i className="fas fa-users" aria-hidden />
              Прогресс групп
            </h1>
            <p className="groups-progress-page__subtitle">{subtitle}</p>
          </div>
          <div className="groups-progress-page__actions">
            <Link to="/reports/homework-check-dashboard" className="groups-progress-page__btn-back">
              <i className="fas fa-arrow-left" aria-hidden />
              Назад к панели
            </Link>
          </div>
        </header>

        <section className="groups-progress-page__card groups-progress-page__filter-card">
          <div className="groups-progress-page__card-body">
            <form className="groups-progress-page__filter-form" onSubmit={(e) => e.preventDefault()}>
              <div className="groups-progress-page__filter-wrap">
                <label htmlFor="groupFilter" className="groups-progress-page__filter-label">
                  <i className="fas fa-filter" aria-hidden />
                  Фильтр по группе
                </label>
                <select
                  id="groupFilter"
                  name="group"
                  className="groups-progress-page__select"
                  value={selectedGroup}
                  onChange={handleFilterChange}
                  aria-label="Фильтр по группе"
                >
                  <option value="">Все группы ({allAvailableGroups.length})</option>
                  {allAvailableGroups.map((g) => (
                    <option key={g.id} value={String(g.id)}>
                      {g.name}
                    </option>
                  ))}
                </select>
              </div>
              {selectedGroup ? (
                <button
                  type="button"
                  className="groups-progress-page__btn groups-progress-page__btn--secondary"
                  onClick={handleResetFilter}
                >
                  <i className="fas fa-times" aria-hidden />
                  Сбросить фильтр
                </button>
              ) : null}
            </form>
          </div>
        </section>

        <section className="groups-progress-page__card">
          <div className="groups-progress-page__card-header">
            <h2 className="groups-progress-page__card-title">Общая статистика</h2>
          </div>
          <div className="groups-progress-page__card-body groups-progress-page__stats-body">
            <div className="groups-progress-page__chart-wrap">
              {totalForChart > 0 ? (
                <svg
                  className="groups-progress-page__chart"
                  width={GROUPS_PROGRESS_PAGE_CHART_SIZE}
                  height={GROUPS_PROGRESS_PAGE_CHART_SIZE}
                  viewBox={`0 0 ${GROUPS_PROGRESS_PAGE_CHART_SIZE} ${GROUPS_PROGRESS_PAGE_CHART_SIZE}`}
                  aria-hidden
                >
                  <circle
                    cx={GROUPS_PROGRESS_PAGE_CHART_SIZE / 2}
                    cy={GROUPS_PROGRESS_PAGE_CHART_SIZE / 2}
                    r={GROUPS_PROGRESS_PAGE_CHART_R}
                    fill="none"
                    stroke="var(--color-bg)"
                    strokeWidth={GROUPS_PROGRESS_PAGE_CHART_STROKE}
                  />
                  {segments.map((seg, i) => {
                    const circumference = 2 * Math.PI * GROUPS_PROGRESS_PAGE_CHART_R;
                    const dashLength = seg.fraction * circumference;
                    const dashOffset = -seg.offset * circumference;
                    return (
                      <circle
                        key={i}
                        cx={GROUPS_PROGRESS_PAGE_CHART_SIZE / 2}
                        cy={GROUPS_PROGRESS_PAGE_CHART_SIZE / 2}
                        r={GROUPS_PROGRESS_PAGE_CHART_R}
                        fill="none"
                        stroke={seg.color}
                        strokeWidth={GROUPS_PROGRESS_PAGE_CHART_STROKE}
                        strokeDasharray={`${dashLength} ${circumference}`}
                        strokeDashoffset={dashOffset}
                        transform={`rotate(-90 ${GROUPS_PROGRESS_PAGE_CHART_SIZE / 2} ${GROUPS_PROGRESS_PAGE_CHART_SIZE / 2})`}
                      />
                    );
                  })}
                </svg>
              ) : (
                <div className="groups-progress-page__chart-empty">Нет данных</div>
              )}
              <div className="groups-progress-page__chart-center">
                <span className="groups-progress-page__chart-value">
                  {data?.overall_learning_percentage ?? 0}%
                </span>
                <span className="groups-progress-page__chart-label">Обученность</span>
              </div>
            </div>
            <div className="groups-progress-page__stats-grid">
              <div className="groups-progress-page__stat-item">
                <span className="groups-progress-page__stat-value groups-progress-page__stat-value--success">
                  {data?.completed_courses ?? 0}
                </span>
                <span className="groups-progress-page__stat-label">Завершено</span>
              </div>
              <div className="groups-progress-page__stat-item">
                <span className="groups-progress-page__stat-value groups-progress-page__stat-value--warning">
                  {data?.in_progress_courses ?? 0}
                </span>
                <span className="groups-progress-page__stat-label">В процессе</span>
              </div>
              <div className="groups-progress-page__stat-item">
                <span className="groups-progress-page__stat-value groups-progress-page__stat-value--secondary">
                  {data?.available_courses ?? 0}
                </span>
                <span className="groups-progress-page__stat-label">Не начато</span>
              </div>
              <div className="groups-progress-page__stat-item">
                <span className="groups-progress-page__stat-value groups-progress-page__stat-value--info">
                  {data?.total_courses ?? 0}
                </span>
                <span className="groups-progress-page__stat-label">Всего</span>
              </div>
            </div>
          </div>
        </section>

        <section className="groups-progress-page__card">
          <div className="groups-progress-page__card-header groups-progress-page__card-header--flex">
            <div>
              <h2 className="groups-progress-page__card-title">Список групп</h2>
              <p className="groups-progress-page__card-desc">Все группы платформы</p>
            </div>
            <span className="groups-progress-page__badge" aria-label="Количество групп">
              {groups.length} групп
            </span>
          </div>
          <div className="groups-progress-page__card-body">
            {groups.length > 0 ? (
              <div className="groups-progress-page__table-wrap">
                <table className="groups-progress-page__table">
                  <thead>
                    <tr>
                      <th className="groups-progress-page__th groups-progress-page__th--n">#</th>
                      <th className="groups-progress-page__th groups-progress-page__th--name">
                        Название группы
                      </th>
                      <th className="groups-progress-page__th groups-progress-page__th--users">
                        Пользователей
                      </th>
                      <th className="groups-progress-page__th groups-progress-page__th--courses">
                        Курсов
                      </th>
                      <th className="groups-progress-page__th groups-progress-page__th--progress">
                        Прогресс
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {groups.map((group, index) => (
                      <tr
                        key={group.id}
                        className="groups-progress-page__row groups-progress-page__row--clickable"
                      >
                        <td className="groups-progress-page__td groups-progress-page__td--muted">
                          {index + 1}
                        </td>
                        <td className="groups-progress-page__td">
                          <a
                            href={`/reports/groups/${group.id}/students-progress/`}
                            className="groups-progress-page__row-link"
                          >
                            <strong>{group.name}</strong>
                          </a>
                        </td>
                        <td className="groups-progress-page__td">
                          <span className="groups-progress-page__stat-badge groups-progress-page__stat-badge--users">
                            <i className="fas fa-users" aria-hidden />
                            {group.total_users}
                          </span>
                        </td>
                        <td className="groups-progress-page__td">
                          <span className="groups-progress-page__stat-badge groups-progress-page__stat-badge--courses">
                            <i className="fas fa-book" aria-hidden />
                            {group.total_courses}
                          </span>
                        </td>
                        <td className="groups-progress-page__td">
                          <div
                            className="groups-progress-page__progress"
                            role="progressbar"
                            aria-valuenow={group.learning_percentage}
                            aria-valuemin={0}
                            aria-valuemax={100}
                            title={`${group.learning_percentage}% обученность`}
                          >
                            <div
                              className={`groups-progress-page__progress-bar ${getProgressBarClass(group.learning_percentage)}`}
                              style={{ width: `${group.learning_percentage}%` }}
                            >
                              <span className="groups-progress-page__progress-text">
                                {group.learning_percentage}%
                              </span>
                            </div>
                          </div>
                          <small className="groups-progress-page__progress-legend">
                            <i className="fa-solid fa-check-circle groups-progress-page__icon-success" aria-hidden />
                            {group.completed_courses}/{group.total_courses}
                          </small>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="groups-progress-page__empty" role="alert">
                <i className="fas fa-users groups-progress-page__empty-icon" aria-hidden />
                <h3 className="groups-progress-page__empty-title">Группы не найдены</h3>
                <p className="groups-progress-page__empty-desc">Нет групп на платформе</p>
              </div>
            )}
          </div>
        </section>
      </div>
    </main>
  );
};

export default GroupsProgressPage;
