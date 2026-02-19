import { useState, useCallback, useEffect } from 'react';
import './UserListFilter.css';

const FILTER_OPTIONS = [
  { value: '', label: 'Все' },
  { value: 'approved', label: 'Только подтверждённые' },
  { value: 'not_approved', label: 'Только не подтверждённые' },
  { value: 'responsible', label: 'Только ответственные' },
  { value: 'not_responsible', label: 'Только не ответственные' },
];

const UserListFilter = ({ groups, isMentorOnly, currentFilters, onFilterChange }) => {
  const [q, setQ] = useState(currentFilters.q || '');
  const [filter, setFilter] = useState(currentFilters.filter || 'approved');
  const [group, setGroup] = useState(currentFilters.group || '');
  const [excludeExternal, setExcludeExternal] = useState(currentFilters.exclude_external !== false);

  useEffect(() => {
    setQ(currentFilters.q || '');
    setFilter(currentFilters.filter || 'approved');
    setGroup(currentFilters.group || '');
    setExcludeExternal(currentFilters.exclude_external !== false);
  }, [currentFilters]);

  const handleSubmit = useCallback((e) => {
    e.preventDefault();
    onFilterChange({
      q,
      filter,
      group,
      exclude_external: excludeExternal,
    });
  }, [q, filter, group, excludeExternal, onFilterChange]);

  const handleQChange = useCallback((e) => {
    setQ(e.target.value);
  }, []);

  const handleFilterChange = useCallback((e) => {
    setFilter(e.target.value);
  }, []);

  const handleGroupChange = useCallback((e) => {
    setGroup(e.target.value);
  }, []);

  const handleExcludeExternalChange = useCallback((e) => {
    setExcludeExternal(e.target.checked);
  }, []);

  return (
    <form className="user-list-filter" onSubmit={handleSubmit}>
      <input
        type="text"
        name="q"
        className="user-list-filter__search"
        placeholder="Поиск по имени или email"
        value={q}
        onChange={handleQChange}
        autoComplete="off"
      />
      
      <select
        name="filter"
        className="user-list-filter__select"
        value={filter}
        onChange={handleFilterChange}
      >
        {FILTER_OPTIONS.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>

      {!isMentorOnly && (
        <>
          <select
            name="group"
            className="user-list-filter__select user-list-filter__select--group"
            value={group}
            onChange={handleGroupChange}
          >
            <option value="">Все группы</option>
            {groups.map((g) => (
              <option key={g.id} value={g.id}>
                {g.name}
              </option>
            ))}
          </select>

          <div className="user-list-filter__checkbox-wrapper" title="Исключить из выборки внешних пользователей">
            <input
              type="hidden"
              name="exclude_external"
              value="0"
            />
            <input
              type="checkbox"
              name="exclude_external"
              id="exclude_external"
              className="user-list-filter__checkbox"
              checked={excludeExternal}
              onChange={handleExcludeExternalChange}
            />
            <label htmlFor="exclude_external" className="user-list-filter__checkbox-label">
              Исключить «Внешний пользователь»
            </label>
          </div>
        </>
      )}

      <button type="submit" className="user-list-filter__submit">
        Фильтровать
      </button>
    </form>
  );
};

export default UserListFilter;
