import { useState, useCallback } from 'react';
import './AdminDascoinDashboardFilters.css';

const AdminDascoinDashboardFilters = ({
  groups,
  roles,
  selectedGroup,
  selectedRole,
  pointsMin,
  pointsMax,
  topUsers,
  zeroPoints,
  approvedOnly,
  showAll,
  isMentorOnly,
  onFilterChange,
  onQuickFilter,
}) => {
  const [localFilters, setLocalFilters] = useState({
    group: selectedGroup,
    role: selectedRole,
    points_min: pointsMin,
    points_max: pointsMax,
  });

  const handleInputChange = useCallback((field, value) => {
    setLocalFilters((prev) => ({ ...prev, [field]: value }));
  }, []);

  const handleSubmit = useCallback(
    (e) => {
      e.preventDefault();
      onFilterChange(localFilters);
    },
    [localFilters, onFilterChange]
  );

  return (
    <div className="admin-dascoin-dashboard-filters">
      <form onSubmit={handleSubmit} className="admin-dascoin-dashboard-filters__form">
        <div className="admin-dascoin-dashboard-filters__row">
          {!isMentorOnly && (
            <div className="admin-dascoin-dashboard-filters__field">
              <label htmlFor="group_filter" className="admin-dascoin-dashboard-filters__label">
                Группа:
              </label>
              <select
                id="group_filter"
                className="admin-dascoin-dashboard-filters__select"
                value={localFilters.group}
                onChange={(e) => handleInputChange('group', e.target.value)}
              >
                <option value="">Все группы</option>
                {groups.map((group) => (
                  <option key={group.id} value={group.id}>
                    {group.name}
                  </option>
                ))}
              </select>
            </div>
          )}
          <div className="admin-dascoin-dashboard-filters__field">
            <label htmlFor="role_filter" className="admin-dascoin-dashboard-filters__label">
              Должность:
            </label>
            <select
              id="role_filter"
              className="admin-dascoin-dashboard-filters__select"
              value={localFilters.role}
              onChange={(e) => handleInputChange('role', e.target.value)}
            >
              <option value="">Все должности</option>
              {roles.map((role) => (
                <option key={role.id} value={role.id}>
                  {role.name}
                </option>
              ))}
            </select>
          </div>
          <div className="admin-dascoin-dashboard-filters__field">
            <label htmlFor="points_min" className="admin-dascoin-dashboard-filters__label">
              Мин. баллов:
            </label>
            <input
              type="number"
              id="points_min"
              className="admin-dascoin-dashboard-filters__input"
              value={localFilters.points_min}
              onChange={(e) => handleInputChange('points_min', e.target.value)}
              placeholder="0"
            />
          </div>
          <div className="admin-dascoin-dashboard-filters__field">
            <label htmlFor="points_max" className="admin-dascoin-dashboard-filters__label">
              Макс. баллов:
            </label>
            <input
              type="number"
              id="points_max"
              className="admin-dascoin-dashboard-filters__input"
              value={localFilters.points_max}
              onChange={(e) => handleInputChange('points_max', e.target.value)}
              placeholder="1000"
            />
          </div>
          <div className="admin-dascoin-dashboard-filters__field">
            <label className="admin-dascoin-dashboard-filters__label">&nbsp;</label>
            <button type="submit" className="admin-dascoin-dashboard-filters__submit">
              <i className="fa-solid fa-search" aria-hidden="true" />
              Фильтр
            </button>
          </div>
        </div>
      </form>

      <div className="admin-dascoin-dashboard-filters__quick">
        <div className="admin-dascoin-dashboard-filters__quick-group" role="group">
          <button
            type="button"
            className={`admin-dascoin-dashboard-filters__quick-btn${
              showAll ? ' admin-dascoin-dashboard-filters__quick-btn--active' : ''
            }`}
            onClick={() => onQuickFilter('all')}
          >
            Все пользователи
          </button>
          <button
            type="button"
            className={`admin-dascoin-dashboard-filters__quick-btn admin-dascoin-dashboard-filters__quick-btn--warning${
              topUsers ? ' admin-dascoin-dashboard-filters__quick-btn--active' : ''
            }`}
            onClick={() => onQuickFilter('top10')}
          >
            Топ-10 по баллам
          </button>
          <button
            type="button"
            className={`admin-dascoin-dashboard-filters__quick-btn admin-dascoin-dashboard-filters__quick-btn--danger${
              zeroPoints ? ' admin-dascoin-dashboard-filters__quick-btn--active' : ''
            }`}
            onClick={() => onQuickFilter('zero')}
          >
            Без баллов
          </button>
          <button
            type="button"
            className={`admin-dascoin-dashboard-filters__quick-btn admin-dascoin-dashboard-filters__quick-btn--success${
              approvedOnly ? ' admin-dascoin-dashboard-filters__quick-btn--active' : ''
            }`}
            onClick={() => onQuickFilter('approved')}
          >
            Подтвержденные
          </button>
        </div>
      </div>
    </div>
  );
};

export default AdminDascoinDashboardFilters;
