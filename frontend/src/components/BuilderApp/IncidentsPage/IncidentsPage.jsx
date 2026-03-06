import { useState, useEffect, useCallback, useRef } from 'react';
import { fetchIncidents, declineIncident } from '../../../api/builder_api';
import './IncidentsPage.css';

const COLUMN_TITLES_STORAGE_KEY = 'incidents_table_column_titles';

const DEFAULT_DATE_FROM = '2025-01-01';
function getDefaultDateTo() {
  return new Date().toISOString().split('T')[0];
}
const DEFAULT_STATUSES = ['new', 'accepted', 'assigned', 'studies_completed'];

function getSavedColumnTitles() {
  try {
    const saved = localStorage.getItem(COLUMN_TITLES_STORAGE_KEY);
    return saved ? JSON.parse(saved) : {};
  } catch {
    return {};
  }
}

function saveColumnTitles(titles) {
  localStorage.setItem(COLUMN_TITLES_STORAGE_KEY, JSON.stringify(titles));
}

function buildViolatorsUrl(incidentTitle) {
  const params = new URLSearchParams();
  params.set('violator_filter', 'yes');
  const today = new Date();
  const dateFrom = new Date(today);
  dateFrom.setDate(dateFrom.getDate() - 30);
  params.set('date_from', dateFrom.toISOString().split('T')[0]);
  params.set('date_to', today.toISOString().split('T')[0]);
  if (incidentTitle) params.set('search', incidentTitle);
  return `/builder/incidents/detail/?${params.toString()}`;
}

function getDetailUrl(searchTitle) {
  if (!searchTitle) return '/builder/incidents/detail/';
  return `/builder/incidents/detail/?search=${encodeURIComponent(searchTitle)}`;
}

const COLUMN_HEADERS = [
  { key: 'date', label: 'Дата', width: '8%' },
  { key: 'title', label: 'Описание', width: '18%' },
  { key: 'incident_type', label: 'Тип инцидента', width: '12%' },
  { key: 'user', label: 'Кто зафиксировал', width: '12%' },
  { key: 'assigned_total', label: 'Всего обучающихся', width: '7%' },
  { key: 'completed', label: 'Завершили обуч.', width: '7%' },
  { key: 'status', label: 'Статус', width: '8%' },
  { key: 'comment', label: 'Комментарий (опционально)', width: '5%', className: 'comment-column' },
];

const IncidentsPage = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  /** Текущие значения формы фильтров (как в get_context_data: date_from, date_to, selected_statuses, selected_incident_type) */
  const [filters, setFilters] = useState({
    date_from: DEFAULT_DATE_FROM,
    date_to: getDefaultDateTo(),
    incident_type: '',
    status: DEFAULT_STATUSES,
  });
  const [selectedIncident, setSelectedIncident] = useState(null);
  const [columnTitles, setColumnTitles] = useState(getSavedColumnTitles);
  const [columnModalOpen, setColumnModalOpen] = useState(false);
  const [columnForm, setColumnForm] = useState({});
  const [declineLoading, setDeclineLoading] = useState(false);
  const clickTimeoutRef = useRef(null);

  /**
   * Загрузка данных. Как в IncidentListView:
   * - params === undefined: использовать текущие filters (после применения или после decline).
   * - params === null или пустой: первый заход / сброс — запрос без GET, бэкенд подставляет дефолты.
   * - params объект: передать как GET-параметры.
   */
  const loadData = useCallback(async (params) => {
    setLoading(true);
    setError(null);
    try {
      const queryParams = params === undefined ? filters : params === null ? {} : params;
      const res = await fetchIncidents(queryParams);
      setData(res);
      setFilters({
        date_from: res.date_from ?? DEFAULT_DATE_FROM,
        date_to: res.date_to ?? getDefaultDateTo(),
        incident_type: res.selected_incident_type ?? '',
        status: res.selected_statuses ?? DEFAULT_STATUSES,
      });
    } catch (err) {
      setError(err.message || 'Ошибка загрузки инцидентов');
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  /** Первая загрузка: без GET (бэкенд сам подставляет дефолты). */
  useEffect(() => {
    loadData(null);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  /** Применить фильтры: отправить текущие значения формы как GET. */
  const handleApplyFilters = (e) => {
    e.preventDefault();
    loadData(filters);
  };

  /** Сбросить: запрос без GET (как ссылка на builder:incidents без query). */
  const handleResetFilters = () => {
    setSelectedIncident(null);
    loadData(null);
  };

  const handleRowClick = (incident, e) => {
    if (e.detail === 2) {
      if (clickTimeoutRef.current) clearTimeout(clickTimeoutRef.current);
      clickTimeoutRef.current = null;
      if (!data?.readonly) {
        window.location.href = `/builder/incidents/${incident.pk}/edit/`;
      }
      return;
    }
    if (clickTimeoutRef.current) clearTimeout(clickTimeoutRef.current);
    clickTimeoutRef.current = setTimeout(() => {
      setSelectedIncident(incident);
      clickTimeoutRef.current = null;
    }, 200);
  };

  const handleContainerClick = (e) => {
    if (e.target.closest('.incidents-page__row') || e.target.closest('.incidents-page__details-buttons')) return;
    if (clickTimeoutRef.current) {
      clearTimeout(clickTimeoutRef.current);
      clickTimeoutRef.current = null;
    }
    setSelectedIncident(null);
  };

  const handleDeclineResume = async () => {
    if (!selectedIncident) return;
    setDeclineLoading(true);
    try {
      const res = await declineIncident(selectedIncident.pk);
      setSelectedIncident((prev) => (prev ? { ...prev, status: res.status, status_display: res.status_display } : null));
      loadData();
    } catch (err) {
      setError(err.message || 'Ошибка действия');
    } finally {
      setDeclineLoading(false);
    }
  };

  const openColumnModal = () => {
    const titles = getSavedColumnTitles();
    const initial = {};
    COLUMN_HEADERS.forEach((col) => {
      initial[col.label] = titles[col.label] ?? col.label;
    });
    setColumnForm(initial);
    setColumnModalOpen(true);
  };

  const handleSaveColumnTitles = (e) => {
    e.preventDefault();
    saveColumnTitles(columnForm);
    setColumnTitles(columnForm);
    setColumnModalOpen(false);
  };

  const getColumnTitle = (label) => columnTitles[label] || label;

  if (!data && !loading && !error) return null;

  const readonly = data?.readonly ?? false;
  const incidents = data?.incidents ?? [];
  const statusChoices = data?.status_choices ?? [];
  const incidentTypeChoices = data?.incident_type_choices ?? [];
  const selectedStatuses = filters.status;

  const truncatedTitle = (title, max = 30) =>
    title && title.length > max ? `${title.slice(0, max)}...` : title || '';

  return (
    <div className="incidents-page" onClick={handleContainerClick}>
      <div className="incidents-page__card">
        <form className="incidents-page__form mb-4" onSubmit={handleApplyFilters} id="incidents-filter-form">
          <div className="incidents-page__form-row">
            <input
              type="date"
              className="incidents-page__input incidents-page__input--date"
              name="date_from"
              id="date_from"
              value={filters.date_from}
              onChange={(e) => setFilters((p) => ({ ...p, date_from: e.target.value }))}
            />
            <input
              type="date"
              className="incidents-page__input incidents-page__input--date"
              name="date_to"
              id="date_to"
              value={filters.date_to}
              onChange={(e) => setFilters((p) => ({ ...p, date_to: e.target.value }))}
            />
            <select
              className="incidents-page__select"
              id="incident_type"
              name="incident_type"
              value={filters.incident_type}
              onChange={(e) => setFilters((p) => ({ ...p, incident_type: e.target.value }))}
            >
              <option value="">Тип инцидента</option>
              {incidentTypeChoices.map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
            {!readonly && (
              <div className="incidents-page__form-actions">
                <a href="/builder/incident/export_excel_report/" className="incidents-page__btn incidents-page__btn--outline">
                  <i className="fas fa-file-excel me-1" aria-hidden />
                  Excel
                </a>
                <a href="/builder/incidents/add/" className="incidents-page__btn incidents-page__btn--primary">
                  + Новый инцидент
                </a>
                <button
                  type="button"
                  className="incidents-page__btn incidents-page__btn--secondary"
                  title="Комментарий к столбцам"
                  onClick={openColumnModal}
                  aria-label="Комментарий к столбцам"
                >
                  К
                </button>
              </div>
            )}
          </div>

          <div className="incidents-page__status-filters">
            {statusChoices.map(([value, label]) => (
              <div key={value} className="incidents-page__form-check">
                <input
                  type="checkbox"
                  className="incidents-page__checkbox"
                  name="status"
                  value={value}
                  id={`status_${value}`}
                  checked={selectedStatuses.includes(value)}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setFilters((p) => ({ ...p, status: [...p.status, value] }));
                    } else {
                      setFilters((p) => ({ ...p, status: p.status.filter((s) => s !== value) }));
                    }
                  }}
                />
                <label className="incidents-page__form-check-label" htmlFor={`status_${value}`}>
                  {label}
                </label>
              </div>
            ))}
            <div className="incidents-page__filter-buttons">
              <button type="submit" className="incidents-page__btn incidents-page__btn--primary">
                Применить фильтры
              </button>
              <button
                type="button"
                className="incidents-page__btn incidents-page__btn--secondary"
                onClick={handleResetFilters}
              >
                Сбросить
              </button>
            </div>
          </div>
        </form>

        <div className="incidents-page__details-buttons">
          <a
            href={selectedIncident ? getDetailUrl(selectedIncident.title) : '/builder/incidents/detail/'}
            className="incidents-page__btn incidents-page__btn--primary"
            title="Подробнее по выбранному инциденту"
          >
            {selectedIncident ? `Подробнее по "${truncatedTitle(selectedIncident.title)}"` : 'Подробнее'}
          </a>
          <a
            href={buildViolatorsUrl(selectedIncident?.title || null)}
            className="incidents-page__btn incidents-page__btn--primary"
            title="Нарушители за последние 30 дней"
          >
            {selectedIncident ? `Нарушители по "${truncatedTitle(selectedIncident.title)}"` : 'Нарушители'}
          </a>
          {!readonly && selectedIncident && (
            <button
              type="button"
              className={selectedIncident.status === 'declined' ? 'incidents-page__btn incidents-page__btn--success' : 'incidents-page__btn incidents-page__btn--danger'}
              onClick={handleDeclineResume}
              disabled={declineLoading}
            >
              {selectedIncident.status === 'declined' ? 'Возобновить' : 'Отклонить'}
            </button>
          )}
        </div>

        {loading && (
          <div className="incidents-page__loading" role="status">
            Загрузка...
          </div>
        )}
        {error && (
          <div className="incidents-page__error" role="alert">
            {error}
          </div>
        )}
        {!loading && !error && (
          <div className="incidents-page__table-wrap">
            <table className="incidents-page__table">
              <thead>
                <tr>
                  {COLUMN_HEADERS.map((col) => (
                    <th
                      key={col.key}
                      style={{ width: col.width }}
                      className={col.className}
                      title={getColumnTitle(col.label)}
                    >
                      {col.label}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {incidents.length === 0 ? (
                  <tr>
                    <td colSpan={COLUMN_HEADERS.length} className="incidents-page__empty">
                      Нет инцидентов
                    </td>
                  </tr>
                ) : (
                  incidents.map((inc) => (
                    <tr
                      key={inc.pk}
                      className={`incidents-page__row status-row-${inc.status} ${selectedIncident?.pk === inc.pk ? 'incidents-page__row--selected' : ''}`}
                      onClick={(e) => handleRowClick(inc, e)}
                      role="button"
                      tabIndex={0}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          e.preventDefault();
                          handleRowClick(inc, e);
                        }
                      }}
                      aria-label={`Инцидент ${inc.title}`}
                    >
                      <td>{inc.created_at}</td>
                      <td>{inc.title}</td>
                      <td>{inc.incident_type_display}</td>
                      <td>{inc.user_name}</td>
                      <td style={{ textAlign: 'center' }}>{inc.course ? (inc.assigned_users_count ?? 0) : '—'}</td>
                      <td style={{ textAlign: 'center' }}>{inc.course ? (inc.completed_users_count ?? 0) : '—'}</td>
                      <td className={`status-${inc.status}`}>{inc.status_display}</td>
                      <td className="incidents-page__comment-cell comment-column">{inc.description}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {columnModalOpen && (
        <div
          className="incidents-page__modal-overlay"
          role="dialog"
          aria-labelledby="column-modal-title"
          aria-modal="true"
        >
          <div className="incidents-page__modal">
            <h4 id="column-modal-title" className="incidents-page__modal-title">
              Комментарий к столбцам
            </h4>
            <form onSubmit={handleSaveColumnTitles}>
              <div className="incidents-page__modal-body">
                {COLUMN_HEADERS.map((col) => (
                  <div key={col.key} className="incidents-page__modal-field">
                    <label htmlFor={`col-${col.key}`}>{col.label}</label>
                    <textarea
                      id={`col-${col.key}`}
                      value={columnForm[col.label] ?? ''}
                      onChange={(e) => setColumnForm((prev) => ({ ...prev, [col.label]: e.target.value }))}
                      rows={3}
                    />
                  </div>
                ))}
              </div>
              <div className="incidents-page__modal-footer">
                <button type="button" className="incidents-page__btn incidents-page__btn--secondary" onClick={() => setColumnModalOpen(false)}>
                  Отмена
                </button>
                <button type="submit" className="incidents-page__btn incidents-page__btn--primary">
                  Сохранить
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default IncidentsPage;
