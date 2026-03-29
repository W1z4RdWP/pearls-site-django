import { useState, useEffect, useCallback } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { fetchLessonUpdateControl } from '../../../api/builder_api';
import './LessonUpdateControlPage.css';

const formatDateRu = (iso) => {
  if (!iso) return '—';
  const parts = iso.split('-');
  if (parts.length !== 3) return '—';
  const [y, m, d] = parts;
  return `${d}.${m}.${y}`;
};

const LessonUpdateControlPage = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [payload, setPayload] = useState(null);
  const [filterForm, setFilterForm] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const queryKey = searchParams.toString();

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchLessonUpdateControl(queryKey);
      setPayload(res);
      if (res.filters) {
        setFilterForm(res.filters);
      }
    } catch (err) {
      setError(err.message || 'Ошибка загрузки');
    } finally {
      setLoading(false);
    }
  }, [queryKey]);

  useEffect(() => {
    load();
  }, [load]);

  const handleFilterChange = (field, value) => {
    setFilterForm((prev) => (prev ? { ...prev, [field]: value } : prev));
  };

  const handleSubmitFilters = (e) => {
    e.preventDefault();
    if (!filterForm) return;
    const p = new URLSearchParams();
    const t = (filterForm.title || '').trim();
    if (t) p.set('title', t);
    if (filterForm.created_from) p.set('created_from', filterForm.created_from);
    if (filterForm.created_to) p.set('created_to', filterForm.created_to);
    if (filterForm.show_overdue) p.set('overdue', '1');
    if (filterForm.show_no_next) p.set('no_next', '1');
    if (filterForm.show_no_responsible) p.set('no_responsible', '1');
    if (filterForm.selected_responsible) p.set('responsible', filterForm.selected_responsible);
    setSearchParams(p);
  };

  const handleMyActualization = () => {
    const name = payload?.user_role_name;
    if (!name) return;
    const p = new URLSearchParams();
    p.set('responsible', name);
    p.set('overdue', '1');
    p.set('no_next', '1');
    p.set('all_dates', '1');
    setSearchParams(p);
  };

  if (loading && !payload) {
    return (
      <main className="lesson-update-control">
        <div className="lesson-update-control__loading" role="status" aria-label="Загрузка">
          <p>Загрузка...</p>
        </div>
      </main>
    );
  }

  if (error && !payload) {
    return (
      <main className="lesson-update-control">
        <div className="lesson-update-control__error" role="alert">
          <p>{error}</p>
        </div>
      </main>
    );
  }

  if (!payload || !filterForm) {
    return null;
  }

  const { rows, roles, user_role_name, urls } = payload;
  const contentBase = urls?.content || '/builder/content/';

  return (
    <main className="lesson-update-control">
      <div className="lesson-update-control__bg">
        <div className="lesson-update-control__card">
          <h1 className="lesson-update-control__title">Контроль актуальности уроков</h1>
          {error && (
            <p className="lesson-update-control__banner-error" role="alert">
              {error}
            </p>
          )}
          {loading && (
            <p className="lesson-update-control__refreshing" role="status">
              Обновление…
            </p>
          )}
          <Link
            to={contentBase}
            className="lesson-update-control__close"
            aria-label="Вернуться к содержанию"
          >
            &times;
          </Link>

          <form className="lesson-update-control__filters" onSubmit={handleSubmitFilters}>
            <input
              type="text"
              name="title"
              placeholder="Название урока"
              value={filterForm.title}
              onChange={(e) => handleFilterChange('title', e.target.value)}
              className="lesson-update-control__input lesson-update-control__input--title"
            />
            <input
              type="date"
              name="created_from"
              value={filterForm.created_from}
              onChange={(e) => handleFilterChange('created_from', e.target.value)}
              className="lesson-update-control__input lesson-update-control__input--date"
            />
            <input
              type="date"
              name="created_to"
              value={filterForm.created_to}
              onChange={(e) => handleFilterChange('created_to', e.target.value)}
              className="lesson-update-control__input lesson-update-control__input--date"
            />
            <label className="lesson-update-control__check">
              <input
                type="checkbox"
                name="overdue"
                checked={filterForm.show_overdue}
                onChange={(e) => handleFilterChange('show_overdue', e.target.checked)}
              />
              <span className="lesson-update-control__check-label">Просроченные</span>
            </label>
            <label className="lesson-update-control__check">
              <input
                type="checkbox"
                name="no_next"
                checked={filterForm.show_no_next}
                onChange={(e) => handleFilterChange('show_no_next', e.target.checked)}
              />
              <span className="lesson-update-control__check-label">Без даты обновления</span>
            </label>
            <label className="lesson-update-control__check">
              <input
                type="checkbox"
                name="no_responsible"
                checked={filterForm.show_no_responsible}
                onChange={(e) => handleFilterChange('show_no_responsible', e.target.checked)}
              />
              <span className="lesson-update-control__check-label">Без ответственных</span>
            </label>
            <select
              name="responsible"
              value={filterForm.selected_responsible}
              onChange={(e) => handleFilterChange('selected_responsible', e.target.value)}
              className="lesson-update-control__select"
            >
              <option value="">— Все —</option>
              {roles.map((role) => (
                <option key={role.id} value={role.name}>{role.name}</option>
              ))}
            </select>
            <button type="submit" className="lesson-update-control__btn lesson-update-control__btn--primary">
              Фильтровать
            </button>
            {user_role_name && (
              <button
                type="button"
                className="lesson-update-control__btn lesson-update-control__btn--my"
                title="Показать уроки моей должности: просроченные и без даты обновления"
                onClick={handleMyActualization}
              >
                Мои к актуализации
              </button>
            )}
          </form>

          <div className="lesson-update-control__table-wrap">
            <table className="lesson-update-control__table">
              <thead>
                <tr>
                  <th>№</th>
                  <th>Дата создания</th>
                  <th>Название урока</th>
                  <th>Категория</th>
                  <th>Дата последнего обновления</th>
                  <th>Период между обновлениями (дней)</th>
                  <th>Дата следующего обновления</th>
                  <th>Должность</th>
                  <th>Ответственный</th>
                </tr>
              </thead>
              <tbody>
                {rows.length === 0 ? (
                  <tr>
                    <td colSpan={9} className="lesson-update-control__empty">
                      Нет данных
                    </td>
                  </tr>
                ) : (
                  rows.map((row) => (
                    <tr key={row.lesson_id}>
                      <td>{row.index}</td>
                      <td>{formatDateRu(row.created)}</td>
                      <td>
                        <a
                          href={`${contentBase}?lesson_id=${row.lesson_id}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="lesson-update-control__lesson-link"
                        >
                          {row.title}
                        </a>
                      </td>
                      <td>{row.category}</td>
                      <td>{formatDateRu(row.last_update)}</td>
                      <td>{row.period_between != null ? row.period_between : '—'}</td>
                      <td
                        className={
                          row.is_overdue
                            ? 'lesson-update-control__cell lesson-update-control__cell--overdue'
                            : 'lesson-update-control__cell'
                        }
                      >
                        {formatDateRu(row.next_update)}
                      </td>
                      <td>{row.responsible_position}</td>
                      <td>{row.responsible_fio}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </main>
  );
};

export default LessonUpdateControlPage;
