import { useState, useEffect, useCallback } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { fetchIncidentDetail, unassignIncidentUser } from '../../../api/builder_api';
import './IncidentDetailPage.css';

const COLUMN_TITLES_STORAGE_KEY = 'incident_detail_table_column_titles';

const DEFAULT_DATE_FROM = '2025-01-01';
function getDefaultDateTo() {
  return new Date().toISOString().split('T')[0];
}

/** Форматирует дедлайн как в incident_detail.html: дата и время (время меньшим шрифтом). */
function formatDeadlineCell(hasCourse, courseDeadlineStr) {
  if (!hasCourse) return '—';
  if (!courseDeadlineStr) return 'Без срока';
  const parts = courseDeadlineStr.trim().split(/\s+/);
  const datePart = parts[0] ?? courseDeadlineStr;
  const timePart = parts[1];
  return (
    <>
      <span className="incident-detail__deadline-date">{datePart}</span>
      {timePart != null && timePart !== '' && <span className="incident-detail__deadline-time"> {timePart}</span>}
    </>
  );
}

const COLUMN_HEADERS = [
  { key: 'num', label: '№' },
  { key: 'date', label: 'Дата назначения' },
  { key: 'title', label: 'Название инцидента' },
  { key: 'assigned', label: 'Назначено' },
  { key: 'group', label: 'Группа' },
  { key: 'violator', label: 'Нарушитель' },
  { key: 'responsible', label: 'Ответственный' },
  { key: 'deadline', label: 'Дедлайн' },
  { key: 'status', label: 'Статус' },
  { key: 'actions', label: 'Действия' },
];

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

const IncidentDetailPage = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({
    search: '',
    date_from: DEFAULT_DATE_FROM,
    date_to: getDefaultDateTo(),
    assigned_user: '',
    violator_filter: 'all',
  });
  const [columnTitles, setColumnTitles] = useState(getSavedColumnTitles);
  const [columnModalOpen, setColumnModalOpen] = useState(false);
  const [columnForm, setColumnForm] = useState({});
  const [unassignLoading, setUnassignLoading] = useState(null);

  const loadData = useCallback(async (params) => {
    setLoading(true);
    setError(null);
    const query = params ?? filters;
    try {
      const res = await fetchIncidentDetail({
        search: query.search || undefined,
        date_from: query.date_from || undefined,
        date_to: query.date_to || undefined,
        assigned_user: query.assigned_user || undefined,
        violator_filter: query.violator_filter || undefined,
      });
      setData(res);
      setFilters({
        search: res.search ?? '',
        date_from: res.date_from ?? DEFAULT_DATE_FROM,
        date_to: res.date_to ?? getDefaultDateTo(),
        assigned_user: res.selected_user_id != null ? String(res.selected_user_id) : '',
        violator_filter: res.violator_filter ?? 'all',
      });
    } catch (err) {
      setError(err.message || 'Ошибка загрузки данных');
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const fromUrl = {
      search: searchParams.get('search') ?? '',
      date_from: searchParams.get('date_from') ?? DEFAULT_DATE_FROM,
      date_to: searchParams.get('date_to') ?? getDefaultDateTo(),
      assigned_user: searchParams.get('assigned_user') ?? '',
      violator_filter: searchParams.get('violator_filter') ?? 'all',
    };
    setFilters(fromUrl);
    loadData(fromUrl);
  }, [searchParams]);

  const handleApplyFilters = useCallback((e) => {
    e?.preventDefault();
    const q = {
      ...filters,
      date_from: filters.date_from || undefined,
      date_to: filters.date_to || undefined,
      assigned_user: filters.assigned_user || undefined,
      violator_filter: filters.violator_filter || undefined,
    };
    setSearchParams(
      Object.fromEntries(
        Object.entries(q).filter(([, v]) => v != null && v !== '')
      )
    );
  }, [filters, setSearchParams]);

  const handleReset = useCallback(() => {
    if (data?.violator_filter_locked) {
      const q = {
        search: '',
        date_from: data.date_from ?? DEFAULT_DATE_FROM,
        date_to: data.date_to ?? getDefaultDateTo(),
        assigned_user: '',
        violator_filter: 'yes',
      };
      setSearchParams({ violator_filter: 'yes', date_from: q.date_from, date_to: q.date_to });
      setFilters(q);
      loadData(q);
    } else {
      const q = {
        search: '',
        date_from: DEFAULT_DATE_FROM,
        date_to: getDefaultDateTo(),
        assigned_user: '',
        violator_filter: 'all',
      };
      setSearchParams({});
      setFilters(q);
      loadData(q);
    }
  }, [data?.violator_filter_locked, data?.date_from, data?.date_to, loadData, setSearchParams]);

  const handleUnassign = useCallback(async (incidentId, userId) => {
    if (!window.confirm('Вы уверены, что хотите отменить назначение этого пользователя на инцидент?')) return;
    setUnassignLoading(`${incidentId}-${userId}`);
    try {
      await unassignIncidentUser(incidentId, userId);
      await loadData(filters);
    } catch (err) {
      window.alert(err.message || 'Ошибка при отмене назначения');
    } finally {
      setUnassignLoading(null);
    }
  }, [filters, loadData]);

  const openColumnModal = useCallback(() => {
    const saved = getSavedColumnTitles();
    const form = {};
    COLUMN_HEADERS.forEach(({ label }) => {
      form[label] = saved[label] ?? '';
    });
    setColumnForm(form);
    setColumnModalOpen(true);
  }, []);

  const closeColumnModal = useCallback(() => {
    setColumnModalOpen(false);
  }, []);

  const handleColumnFormChange = useCallback((label, value) => {
    setColumnForm((prev) => ({ ...prev, [label]: value }));
  }, []);

  const handleColumnFormSubmit = useCallback((e) => {
    e.preventDefault();
    saveColumnTitles(columnForm);
    setColumnTitles(columnForm);
    closeColumnModal();
  }, [columnForm, closeColumnModal]);

  const getColumnTitle = useCallback((label) => columnTitles[label] || '', [columnTitles]);

  if (loading && !data) {
    return (
      <main className="incident-detail">
        <div className="incident-detail__loading" role="status" aria-label="Загрузка">
          <p>Загрузка...</p>
        </div>
      </main>
    );
  }

  if (error) {
    return (
      <main className="incident-detail">
        <div className="incident-detail__error" role="alert">
          <p>{error}</p>
          <Link to="/builder/incidents" className="incident-detail__back">← Назад к списку</Link>
        </div>
      </main>
    );
  }

  const list = data?.incident_user_list ?? [];
  const users = data?.users ?? [];
  const violatorFilterLocked = data?.violator_filter_locked ?? false;

  return (
    <main className="incident-detail">
      <div className="incident-detail__card">
        <div className="incident-detail__header">
          <h2 className="incident-detail__title">Детали инцидентов</h2>
          <Link to="/builder/incidents" className="incident-detail__back">← Назад к списку</Link>
        </div>

        <form className="incident-detail__filters" onSubmit={handleApplyFilters}>
          <div className="incident-detail__filters-row">
            <input
              type="text"
              className="incident-detail__input"
              placeholder="Поиск по названию инцидента..."
              value={filters.search}
              onChange={(e) => setFilters((f) => ({ ...f, search: e.target.value }))}
              aria-label="Поиск по названию"
            />
            <input
              type="date"
              className="incident-detail__input incident-detail__input--date"
              value={filters.date_from}
              onChange={(e) => setFilters((f) => ({ ...f, date_from: e.target.value }))}
              aria-label="Дата с"
            />
            <input
              type="date"
              className="incident-detail__input incident-detail__input--date"
              value={filters.date_to}
              onChange={(e) => setFilters((f) => ({ ...f, date_to: e.target.value }))}
              aria-label="Дата по"
            />
            <select
              className="incident-detail__select"
              value={filters.assigned_user}
              onChange={(e) => setFilters((f) => ({ ...f, assigned_user: e.target.value }))}
              aria-label="Пользователь"
            >
              <option value="">Все пользователи</option>
              {users.map((u) => (
                <option key={u.id} value={u.id}>
                  {u.full_name}
                </option>
              ))}
            </select>
            <select
              className="incident-detail__select"
              value={filters.violator_filter}
              onChange={(e) => setFilters((f) => ({ ...f, violator_filter: e.target.value }))}
              disabled={violatorFilterLocked}
              aria-label="Тип участника"
              style={violatorFilterLocked ? { backgroundColor: '#e9ecef', cursor: 'not-allowed' } : undefined}
            >
              <option value="all">Тип участника: Все</option>
              <option value="yes">Только нарушители</option>
              <option value="no">Только не нарушители</option>
            </select>
          </div>
          <div className="incident-detail__filters-actions">
            <button type="submit" className="incident-detail__btn incident-detail__btn--primary">
              Применить фильтры
            </button>
            <button type="button" className="incident-detail__btn incident-detail__btn--secondary" onClick={handleReset}>
              Сбросить
            </button>
            <button
              type="button"
              className="incident-detail__btn incident-detail__btn--secondary"
              onClick={openColumnModal}
              title="Комментарий к столбцам"
            >
              К
            </button>
          </div>
        </form>

        <h3 className="incident-detail__subtitle">Назначенные пользователи</h3>

        <div className="incident-detail__table-wrap">
          <table className="incident-detail__table">
            <thead>
              <tr>
                {COLUMN_HEADERS.map(({ key, label }) => (
                  <th key={key} title={getColumnTitle(label)} style={key === 'num' ? { width: '5%' } : key === 'date' ? { width: '10%' } : key === 'title' ? { width: '20%' } : key === 'assigned' || key === 'responsible' ? { width: '15%' } : key === 'group' ? { width: '15%' } : key === 'violator' || key === 'deadline' || key === 'status' ? { width: '10%' } : { width: '5%' }}>
                    {label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {list.length === 0 ? (
                <tr>
                  <td colSpan={COLUMN_HEADERS.length} className="incident-detail__empty">
                    Нет назначенных пользователей
                  </td>
                </tr>
              ) : (
                list.map((item, index) => (
                  <tr key={`${item.incident.id}-${item.user.id}`} className="incident-detail__row">
                    <td>{index + 1}</td>
                    <td>{item.incident.created_at}</td>
                    <td>{item.incident.title}</td>
                    <td>{item.user.full_name}</td>
                    <td style={{ whiteSpace: 'normal', wordWrap: 'break-word' }}>
                      {item.user.groups?.length ? item.user.groups.join(', ') : 'Без групп'}
                    </td>
                    <td>
                      {item.is_violator ? (
                        <span className="incident-detail__badge incident-detail__badge--danger">Да</span>
                      ) : (
                        <span className="incident-detail__badge incident-detail__badge--secondary">Нет</span>
                      )}
                    </td>
                    <td>{item.incident.responsible_mentor ?? '—'}</td>
                    <td className="incident-detail__deadline-cell">
                      {formatDeadlineCell(item.incident.course, item.course_deadline)}
                    </td>
                    <td style={{ textAlign: 'center' }}>
                      {item.course_status_display ? (
                        <span className={`incident-detail__status incident-detail__status--${item.course_status}`}>
                          {item.course_status_display.charAt(0).toUpperCase() + item.course_status_display.slice(1)}
                        </span>
                      ) : (
                        '—'
                      )}
                    </td>
                    <td style={{ textAlign: 'center' }}>
                      <button
                        type="button"
                        className="incident-detail__unassign-btn"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleUnassign(item.incident.id, item.user.id);
                        }}
                        disabled={unassignLoading === `${item.incident.id}-${item.user.id}`}
                        title="Отменить назначение"
                        aria-label="Отменить назначение"
                      >
                        <span className="incident-detail__unassign-icon" aria-hidden>×</span>
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {columnModalOpen && (
        <div className="incident-detail__modal" role="dialog" aria-labelledby="column-modal-title">
          <div className="incident-detail__modal-content">
            <h4 id="column-modal-title" className="incident-detail__modal-title">Комментарий к столбцам</h4>
            <form onSubmit={handleColumnFormSubmit}>
              <div className="incident-detail__modal-body">
                {COLUMN_HEADERS.map(({ label }) => (
                  <div key={label} className="incident-detail__modal-field">
                    <label htmlFor={`col-${label}`}>{label}</label>
                    <textarea
                      id={`col-${label}`}
                      value={columnForm[label] ?? ''}
                      onChange={(e) => handleColumnFormChange(label, e.target.value)}
                      rows={3}
                      className="incident-detail__textarea"
                    />
                  </div>
                ))}
              </div>
              <div className="incident-detail__modal-actions">
                <button type="button" className="incident-detail__btn incident-detail__btn--secondary" onClick={closeColumnModal}>
                  Отмена
                </button>
                <button type="submit" className="incident-detail__btn incident-detail__btn--primary">
                  Сохранить
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </main>
  );
};

export default IncidentDetailPage;
