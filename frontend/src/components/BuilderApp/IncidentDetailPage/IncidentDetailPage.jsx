import { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { fetchIncidentDetail, unassignIncidentUser } from '../../../api/builder_api';
import './IncidentDetailPage.css';

const COLUMN_TITLES_STORAGE_KEY = 'incident_detail_table_column_titles';
const LAZY_PAGE_SIZE = 30;

const DEFAULT_DATE_FROM = '2025-01-01';
function getDefaultDateTo() {
  return new Date().toISOString().split('T')[0];
}

/** Форматирует дедлайн: дата и время (время меньшим шрифтом). */
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
  { key: 'date', label: 'Дата назначения', sortType: 'date-dot', sortCol: 1 },
  { key: 'title', label: 'Название инцидента', sortType: 'text', sortCol: 2 },
  { key: 'assigned', label: 'Назначено', sortType: 'text', sortCol: 3 },
  { key: 'department', label: 'Подразделение', sortType: 'text', sortCol: 4 },
  { key: 'violator', label: 'Нарушитель', sortType: 'text', sortCol: 5 },
  { key: 'responsible', label: 'Ответственный', sortType: 'text', sortCol: 6 },
  { key: 'deadline', label: 'Дедлайн', sortType: 'datetime-dot', sortCol: 7 },
  { key: 'status', label: 'Статус', sortType: 'text', sortCol: 8 },
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

function parseDateDot(str) {
  if (!str || str === '—' || str === 'Без срока') return null;
  const m = str.trim().match(/(\d{2})\.(\d{2})\.(\d{4})/);
  return m ? new Date(Number(m[3]), Number(m[2]) - 1, Number(m[1])) : null;
}

function parseDatetimeDot(str) {
  if (!str || str === '—' || str === 'Без срока') return null;
  const m = str.trim().match(/(\d{2})\.(\d{2})\.(\d{4})\s+(\d{2}):(\d{2})/);
  if (m) return new Date(Number(m[3]), Number(m[2]) - 1, Number(m[1]), Number(m[4]), Number(m[5]));
  return parseDateDot(str);
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
    status: [],
    department_filter: [],
    only_overdue: false,
  });
  const [columnTitles, setColumnTitles] = useState(getSavedColumnTitles);
  const [columnModalOpen, setColumnModalOpen] = useState(false);
  const [columnForm, setColumnForm] = useState({});
  const [unassignLoading, setUnassignLoading] = useState(null);
  const [sortState, setSortState] = useState({ col: null, dir: 'asc' });
  const [departmentDropdownOpen, setDepartmentDropdownOpen] = useState(false);
  const { col: sortCol, dir: sortDir } = sortState;

  // Lazy rendering: показываем часть списка (30, 60, 90...) по мере прокрутки.
  const [visibleCount, setVisibleCount] = useState(LAZY_PAGE_SIZE);
  const [loadingMore, setLoadingMore] = useState(false);
  const sentinelRef = useRef(null);
  const loadingMoreRef = useRef(false);

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
        status: Array.isArray(query.status) && query.status.length ? query.status : undefined,
        department_filter: Array.isArray(query.department_filter) && query.department_filter.length ? query.department_filter : undefined,
        only_overdue: query.only_overdue === true ? true : undefined,
      });
      setData(res);
      setFilters({
        search: res.search ?? '',
        date_from: res.date_from ?? DEFAULT_DATE_FROM,
        date_to: res.date_to ?? getDefaultDateTo(),
        assigned_user: res.selected_user_id != null ? String(res.selected_user_id) : '',
        violator_filter: res.violator_filter ?? 'all',
        status: res.selected_statuses ?? [],
        department_filter: res.selected_department_filters ?? [],
        only_overdue: res.only_overdue ?? false,
      });
    } catch (err) {
      setError(err.message || 'Ошибка загрузки данных');
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  const buildParamsFromUrl = useCallback(() => {
    return {
      search: searchParams.get('search') ?? '',
      date_from: searchParams.get('date_from') ?? DEFAULT_DATE_FROM,
      date_to: searchParams.get('date_to') ?? getDefaultDateTo(),
      assigned_user: searchParams.get('assigned_user') ?? '',
      violator_filter: searchParams.get('violator_filter') ?? 'all',
      status: searchParams.getAll('status'),
      department_filter: searchParams.getAll('department_filter'),
      only_overdue: searchParams.get('only_overdue') === 'on',
    };
  }, [searchParams]);

  useEffect(() => {
    const fromUrl = buildParamsFromUrl();
    setFilters(fromUrl);
    loadData(fromUrl);
  }, [searchParams]);

  // Сброс lazy-рендера при повторной загрузке данных (смена фильтров/параметров).
  useEffect(() => {
    setVisibleCount(LAZY_PAGE_SIZE);
  }, [data?.incident_user_list]);

  const applyFiltersToUrl = useCallback((q) => {
    const params = new URLSearchParams();
    if (q.search) params.set('search', q.search);
    if (q.date_from) params.set('date_from', q.date_from);
    if (q.date_to) params.set('date_to', q.date_to);
    if (q.assigned_user) params.set('assigned_user', q.assigned_user);
    if (q.violator_filter) params.set('violator_filter', q.violator_filter);
    (q.status || []).forEach((s) => params.append('status', s));
    (q.department_filter || []).forEach((d) => params.append('department_filter', d));
    if (q.only_overdue) params.set('only_overdue', 'on');
    setSearchParams(params);
  }, [setSearchParams]);

  const handleApplyFilters = useCallback((e) => {
    e?.preventDefault();
    const q = {
      ...filters,
      date_from: filters.date_from || undefined,
      date_to: filters.date_to || undefined,
      assigned_user: filters.assigned_user || undefined,
      violator_filter: filters.violator_filter || undefined,
      status: filters.status?.length ? filters.status : undefined,
      department_filter: filters.department_filter?.length ? filters.department_filter : undefined,
      only_overdue: filters.only_overdue || undefined,
    };
    applyFiltersToUrl(q);
  }, [filters, applyFiltersToUrl]);

  const handleReset = useCallback(() => {
    if (data?.violator_filter_locked) {
      const q = {
        search: '',
        date_from: data.date_from ?? DEFAULT_DATE_FROM,
        date_to: data.date_to ?? getDefaultDateTo(),
        assigned_user: '',
        violator_filter: 'yes',
        status: [],
        department_filter: [],
        only_overdue: false,
      };
      applyFiltersToUrl(q);
      setFilters(q);
      loadData(q);
    } else {
      const q = {
        search: '',
        date_from: DEFAULT_DATE_FROM,
        date_to: getDefaultDateTo(),
        assigned_user: '',
        violator_filter: 'all',
        status: [],
        department_filter: [],
        only_overdue: false,
      };
      setSearchParams({});
      setFilters(q);
      loadData(q);
    }
  }, [data?.violator_filter_locked, data?.date_from, data?.date_to, loadData, setSearchParams, applyFiltersToUrl]);

  const handleDateLastWeek = useCallback(() => {
    const today = new Date();
    const dateTo = today.toISOString().split('T')[0];
    const dateFrom = new Date(today);
    dateFrom.setDate(dateFrom.getDate() - 7);
    const dateFromStr = dateFrom.toISOString().split('T')[0];
    setFilters((f) => ({ ...f, date_from: dateFromStr, date_to: dateTo }));
    applyFiltersToUrl({ ...filters, date_from: dateFromStr, date_to: dateTo });
    loadData({ ...filters, date_from: dateFromStr, date_to: dateTo });
  }, [filters, loadData, applyFiltersToUrl]);

  const handleDateReset = useCallback(() => {
    setFilters((f) => ({ ...f, date_from: '', date_to: '' }));
    const q = { ...filters, date_from: '', date_to: '' };
    applyFiltersToUrl(q);
    loadData(q);
  }, [filters, loadData, applyFiltersToUrl]);

  const dateQuickActive = useMemo(() => {
    const from = filters.date_from || '';
    const to = filters.date_to || '';
    if (!from && !to) return 'reset';
    const today = new Date();
    const todayStr = today.toISOString().split('T')[0];
    const weekAgo = new Date(today);
    weekAgo.setDate(weekAgo.getDate() - 7);
    const weekAgoStr = weekAgo.toISOString().split('T')[0];
    if (from === weekAgoStr && to === todayStr) return 'lastWeek';
    return null;
  }, [filters.date_from, filters.date_to]);

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

  const closeColumnModal = useCallback(() => setColumnModalOpen(false), []);

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

  const handleSort = useCallback((sortColIdx) => {
    setSortState((prev) => ({
      col: sortColIdx,
      dir: prev.col === sortColIdx ? (prev.dir === 'asc' ? 'desc' : 'asc') : 'asc',
    }));
  }, []);

  const sortedList = useMemo(() => {
    const list = data?.incident_user_list ?? [];
    if (sortCol == null || sortCol === 0 || sortCol === 9) return list;
    const header = COLUMN_HEADERS.find((h) => h.sortCol === sortCol);
    if (!header) return list;
    const type = header.sortType || 'text';
    const getVal = (item) => {
      let text = '';
      switch (sortCol) {
        case 1: text = item.incident.created_at; break;
        case 2: text = item.incident.title; break;
        case 3: text = item.user.full_name; break;
        case 4: text = item.user.department ?? '—'; break;
        case 5: text = item.is_violator ? 'Да' : 'Нет'; break;
        case 6: text = item.incident.responsible_mentor ?? '—'; break;
        case 7: text = item.course_deadline ?? (item.incident.course ? 'Без срока' : '—'); break;
        case 8: text = item.incident_status_display ?? '—'; break;
        default: return '';
      }
      if (type === 'date-dot') return parseDateDot(text);
      if (type === 'datetime-dot') return parseDatetimeDot(text);
      return (text || '').toLowerCase();
    };
    const arr = [...list].sort((a, b) => {
      const va = getVal(a);
      const vb = getVal(b);
      let cmp = 0;
      if (va === null && vb === null) cmp = 0;
      else if (va === null) cmp = 1;
      else if (vb === null) cmp = -1;
      else if (type === 'text') cmp = va < vb ? -1 : va > vb ? 1 : 0;
      else cmp = va - vb;
      return sortDir === 'asc' ? cmp : -cmp;
    });
    return arr;
  }, [data?.incident_user_list, sortCol, sortDir]);

  const totalCount = sortedList.length;
  const hasMore = totalCount > visibleCount;

  // Infinite scroll trigger (добавляет следующие 30 строк).
  useEffect(() => {
    if (!hasMore) return;
    if (!sentinelRef.current) return;

    const observer = new IntersectionObserver(
      (entries) => {
        const first = entries[0];
        if (!first?.isIntersecting) return;
        if (loadingMoreRef.current) return;

        loadingMoreRef.current = true;
        setLoadingMore(true);

        setVisibleCount((prev) => {
          if (prev >= totalCount) return prev;
          return Math.min(prev + LAZY_PAGE_SIZE, totalCount);
        });

        // Небольшой кулдаун для UX и чтобы не триггерилось несколько раз подряд.
        setTimeout(() => {
          loadingMoreRef.current = false;
          setLoadingMore(false);
        }, 250);
      },
      { root: null, rootMargin: '300px 0px', threshold: 0.01 }
    );

    observer.observe(sentinelRef.current);
    return () => observer.disconnect();
  }, [hasMore, totalCount]);

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

  const list = sortedList.slice(0, visibleCount);
  const users = data?.users ?? [];
  const statusChoices = data?.status_choices ?? [];
  const departments = data?.departments ?? [];
  const violatorFilterLocked = data?.violator_filter_locked ?? false;

  return (
    <main className="incident-detail">
      <div className="incident-detail__card">
        <div className="incident-detail__header">
          <h2 className="incident-detail__title">Детали инцидентов</h2>
          <div className="incident-detail__header-actions">
            <Link to="/builder/incidents/statuses-report/" className="incident-detail__btn incident-detail__btn--primary">Отчёт</Link>
            <Link to="/builder/incidents" className="incident-detail__back">← Назад к списку</Link>
          </div>
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
            <div className="incident-detail__date-wrap">
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
                min={filters.date_from || undefined}
                onChange={(e) => setFilters((f) => ({ ...f, date_to: e.target.value }))}
                aria-label="Дата по"
              />
              <div className="incident-detail__date-quick">
                <button type="button" className={`incident-detail__btn incident-detail__btn--outline incident-detail__date-quick-btn ${dateQuickActive === 'lastWeek' ? 'incident-detail__date-quick-btn--active' : ''}`} onClick={handleDateLastWeek} title="Инциденты за прошлую неделю">-1нед.</button>
                <button type="button" className={`incident-detail__btn incident-detail__btn--outline incident-detail__date-quick-btn ${dateQuickActive === 'reset' ? 'incident-detail__date-quick-btn--active' : ''}`} onClick={handleDateReset} title="Весь период, сбросить фильтр по дате">&lt;-&gt;</button>
              </div>
            </div>
            <select
              className="incident-detail__select"
              value={filters.assigned_user}
              onChange={(e) => setFilters((f) => ({ ...f, assigned_user: e.target.value }))}
              aria-label="Пользователь"
            >
              <option value="">Все пользователи</option>
              {users.map((u) => (
                <option key={u.id} value={u.id}>{u.full_name}</option>
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
          <div className="incident-detail__filters-status-row">
            <div className="incident-detail__status-filters">
              {statusChoices.map(([value, label]) => (
                <label key={value} className="incident-detail__checkbox-label">
                  <input
                    type="checkbox"
                    className="incident-detail__checkbox"
                    checked={filters.status?.includes(value)}
                    onChange={(e) => {
                      const next = e.target.checked
                        ? [...(filters.status || []), value]
                        : (filters.status || []).filter((s) => s !== value);
                      setFilters((f) => ({ ...f, status: next }));
                    }}
                  />
                  {label}
                </label>
              ))}
            </div>
            <div className="incident-detail__department-dropdown">
              <button
                type="button"
                className="incident-detail__btn incident-detail__btn--outline incident-detail__department-toggle"
                onClick={() => setDepartmentDropdownOpen((o) => !o)}
                aria-expanded={departmentDropdownOpen}
                aria-haspopup="true"
              >
                {filters.department_filter?.length ? `${filters.department_filter.length} выбрано` : 'Все подразделения'}
              </button>
              {departmentDropdownOpen && (
                <ul className="incident-detail__department-menu" role="menu">
                  {departments.map((d) => (
                    <li key={d.name} className="incident-detail__department-item">
                      <label className="incident-detail__checkbox-label">
                        <input
                          type="checkbox"
                          className="incident-detail__checkbox"
                          checked={filters.department_filter?.includes(d.name)}
                          onChange={(e) => {
                            const next = e.target.checked
                              ? [...(filters.department_filter || []), d.name]
                              : (filters.department_filter || []).filter((x) => x !== d.name);
                            setFilters((f) => ({ ...f, department_filter: next }));
                          }}
                        />
                        {d.name}
                      </label>
                    </li>
                  ))}
                </ul>
              )}
            </div>
            <label className="incident-detail__checkbox-label">
              <input
                type="checkbox"
                className="incident-detail__checkbox"
                checked={filters.only_overdue}
                onChange={(e) => setFilters((f) => ({ ...f, only_overdue: e.target.checked }))}
              />
              Только просроченные
            </label>
          </div>
          <div className="incident-detail__filters-actions">
            <button type="submit" className="incident-detail__btn incident-detail__btn--primary">Применить фильтры</button>
            <button type="button" className="incident-detail__btn incident-detail__btn--secondary" onClick={handleReset}>Сбросить</button>
            <button type="button" className="incident-detail__btn incident-detail__btn--secondary" onClick={openColumnModal} title="Комментарий к столбцам">К</button>
          </div>
        </form>

        <h3 className="incident-detail__subtitle">Назначенные пользователи</h3>

        <div className="incident-detail__table-wrap">
          <table className="incident-detail__table">
            <thead>
              <tr>
                {COLUMN_HEADERS.map(({ key, label, sortType, sortCol: colIdx }) => (
                  <th
                    key={key}
                    title={getColumnTitle(label)}
                    className={colIdx != null ? 'incident-detail__th sortable' : ''}
                    style={key === 'num' ? { width: '5%' } : key === 'date' ? { width: '10%' } : key === 'title' ? { width: '20%' } : key === 'assigned' || key === 'responsible' ? { width: '15%' } : key === 'department' ? { width: '15%' } : key === 'violator' || key === 'deadline' || key === 'status' ? { width: '10%' } : { width: '5%' }}
                    onClick={colIdx != null ? () => handleSort(colIdx) : undefined}
                  >
                    {label}
                    {colIdx != null && (
                      <span className="incident-detail__sort-icon">
                        <span className={sortCol === colIdx && sortDir === 'asc' ? 'incident-detail__sort-active' : ''}>&#9650;</span>
                        <span className={sortCol === colIdx && sortDir === 'desc' ? 'incident-detail__sort-active' : ''}>&#9660;</span>
                      </span>
                    )}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {list.length === 0 ? (
                <tr>
                  <td colSpan={COLUMN_HEADERS.length} className="incident-detail__empty">Нет назначенных пользователей</td>
                </tr>
              ) : (
                list.map((item, index) => (
                  <tr key={`${item.incident.id}-${item.user.id}`} className="incident-detail__row">
                    <td>{index + 1}</td>
                    <td>{item.incident.created_at}</td>
                    <td>{item.incident.title}</td>
                    <td>{item.user.full_name}</td>
                    <td style={{ whiteSpace: 'normal', wordWrap: 'break-word' }}>{item.user.department ?? '—'}</td>
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
                    <td
                      className={item.incident_status ? `incident-detail__status-cell incident-detail__status-cell--${item.incident_status}` : ''}
                      style={{ textAlign: 'center' }}
                    >
                      {item.incident_status_display ? (item.incident_status_display.charAt(0).toUpperCase() + item.incident_status_display.slice(1)) : '—'}
                    </td>
                    <td style={{ textAlign: 'center' }}>
                      <button
                        type="button"
                        className="incident-detail__unassign-btn"
                        onClick={(e) => { e.stopPropagation(); handleUnassign(item.incident.id, item.user.id); }}
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

        {hasMore && (
          <>
            <div ref={sentinelRef} style={{ height: 1 }} />
            {loadingMore && (
              <div style={{ textAlign: 'center', marginTop: 8, color: '#6c757d' }}>
                Подгружаем...
              </div>
            )}
          </>
        )}
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
                    <textarea id={`col-${label}`} value={columnForm[label] ?? ''} onChange={(e) => handleColumnFormChange(label, e.target.value)} rows={3} className="incident-detail__textarea" />
                  </div>
                ))}
              </div>
              <div className="incident-detail__modal-actions">
                <button type="button" className="incident-detail__btn incident-detail__btn--secondary" onClick={closeColumnModal}>Отмена</button>
                <button type="submit" className="incident-detail__btn incident-detail__btn--primary">Сохранить</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </main>
  );
};

export default IncidentDetailPage;
