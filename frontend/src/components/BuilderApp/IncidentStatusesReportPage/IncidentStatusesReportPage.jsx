import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { fetchIncidentStatusesReport } from '../../../api/builder_api';
import './IncidentStatusesReportPage.css';

const IncidentStatusesReportPage = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({
    date_from: '',
    date_to: '',
    department_filter: '',
  });

  const loadData = useCallback(async (params) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchIncidentStatusesReport(params ?? filters);
      setData(res);
      setFilters({
        date_from: res.date_from ?? '',
        date_to: res.date_to ?? '',
        department_filter: res.department_filter ?? '',
      });
    } catch (err) {
      setError(err.message || 'Ошибка загрузки отчёта');
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    loadData(null);
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    loadData(undefined);
  };

  const handleLastWeek = () => {
    const today = new Date();
    const dateTo = today.toISOString().split('T')[0];
    const dateFrom = new Date(today);
    dateFrom.setDate(dateFrom.getDate() - 7);
    const dateFromStr = dateFrom.toISOString().split('T')[0];
    setFilters((prev) => ({
      ...prev,
      date_from: dateFromStr,
      date_to: dateTo,
    }));
    loadData({ ...filters, date_from: dateFromStr, date_to: dateTo });
  };

  const handleResetDates = () => {
    setFilters((prev) => ({
      ...prev,
      date_from: '',
      date_to: '',
    }));
    loadData({
      ...filters,
      date_from: '',
      date_to: '',
    });
  };

  const todayStr = new Date().toISOString().split('T')[0];
  const weekAgoStr = (() => {
    const d = new Date();
    d.setDate(d.getDate() - 7);
    return d.toISOString().split('T')[0];
  })();
  const isLastWeekActive = data && data.date_from === weekAgoStr && data.date_to === todayStr;
  const isResetActive = data && (data.date_from === '' || data.date_from == null) && (data.date_to === '' || data.date_to == null);

  if (loading && !data) {
    return (
      <main className="incident-statuses-report">
        <div className="incident-statuses-report__card">
          <p className="incident-statuses-report__loading">Загрузка…</p>
        </div>
      </main>
    );
  }

  if (error && !data) {
    return (
      <main className="incident-statuses-report">
        <div className="incident-statuses-report__card">
          <p className="incident-statuses-report__error" role="alert">{error}</p>
        </div>
      </main>
    );
  }

  const reportData = data?.report_data ?? [];
  const departments = data?.departments ?? [];

  return (
    <main className="incident-statuses-report">
      <div className="incident-statuses-report__card">
        <header className="incident-statuses-report__header">
          <h1 className="incident-statuses-report__title">Отчет по инцидентам</h1>
          <Link to="/builder/incidents/detail/" className="incident-statuses-report__back">
            ← Назад к деталям
          </Link>
        </header>

        <form
          className="incident-statuses-report__form"
          onSubmit={handleSubmit}
          aria-label="Фильтр по датам и подразделению"
        >
          <div className="incident-statuses-report__filters-row">
            <div className="incident-statuses-report__date-wrap">
              <input
                type="date"
                className="incident-statuses-report__input"
                id="date_from"
                name="date_from"
                value={filters.date_from}
                onChange={(e) => {
                  const v = e.target.value;
                  setFilters((prev) => ({
                    ...prev,
                    date_from: v,
                    date_to: v && prev.date_to && prev.date_to < v ? v : prev.date_to,
                  }));
                }}
                aria-label="Дата с"
              />
              <input
                type="date"
                className="incident-statuses-report__input"
                id="date_to"
                name="date_to"
                value={filters.date_to}
                min={filters.date_from || undefined}
                onChange={(e) => {
                  const v = e.target.value;
                  setFilters((prev) => ({
                    ...prev,
                    date_to: filters.date_from && v && v < filters.date_from ? filters.date_from : v,
                  }));
                }}
                aria-label="Дата по"
              />
              <div className="incident-statuses-report__quick-buttons">
                <button
                  type="button"
                  className={`incident-statuses-report__quick-btn ${isLastWeekActive ? 'incident-statuses-report__quick-btn--active' : ''}`}
                  onClick={handleLastWeek}
                  title="Инциденты за прошлую неделю"
                >
                  -1нед.
                </button>
                <button
                  type="button"
                  className={`incident-statuses-report__quick-btn ${isResetActive ? 'incident-statuses-report__quick-btn--active' : ''}`}
                  onClick={handleResetDates}
                  title="Весь период, сбросить фильтр по дате"
                >
                  &lt;-&gt;
                </button>
              </div>
            </div>
            <div className="incident-statuses-report__department-wrap">
              <select
                className="incident-statuses-report__select"
                id="department_filter"
                name="department_filter"
                value={filters.department_filter}
                onChange={(e) => setFilters((prev) => ({ ...prev, department_filter: e.target.value }))}
                aria-label="Подразделение"
              >
                <option value="">Все подразделения</option>
                {departments.map((d) => (
                  <option key={d.name} value={d.name}>
                    {d.name}
                  </option>
                ))}
              </select>
            </div>
            <button type="submit" className="incident-statuses-report__submit">
              Применить
            </button>
          </div>
        </form>

        <div className="incident-statuses-report__table-wrap">
          <table className="incident-statuses-report__table">
            <thead>
              <tr>
                <th style={{ width: '5%' }}>№</th>
                <th style={{ width: '20%' }}>ФИО</th>
                <th style={{ width: '20%' }}>Подразделение</th>
                <th style={{ width: '15%' }}>Назначено</th>
                <th style={{ width: '15%' }}>Просрочено</th>
                <th style={{ width: '15%' }}>Завершено</th>
                <th style={{ width: '15%' }}>Обучение завершено</th>
              </tr>
            </thead>
            <tbody>
              {reportData.length > 0 ? (
                reportData.map((item, index) => (
                  <tr key={`${item.full_name}-${item.department}-${index}`}>
                    <td>{index + 1}</td>
                    <td>{item.full_name}</td>
                    <td>{item.department}</td>
                    <td className="incident-statuses-report__cell--center">{item.assigned_count}</td>
                    <td className="incident-statuses-report__cell--center">
                      {item.overdue_count > 0 ? (
                        <span className="incident-statuses-report__badge incident-statuses-report__badge--danger">
                          {item.overdue_count}
                        </span>
                      ) : (
                        item.overdue_count
                      )}
                    </td>
                    <td className="incident-statuses-report__cell--center">{item.resolved_count}</td>
                    <td className="incident-statuses-report__cell--center">{item.studies_completed_count}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7} className="incident-statuses-report__empty">
                    Нет данных за указанный период
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </main>
  );
};

export default IncidentStatusesReportPage;
