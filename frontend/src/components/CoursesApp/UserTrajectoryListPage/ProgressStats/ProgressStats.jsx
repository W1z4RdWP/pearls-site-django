import './ProgressStats.css';

/**
 * Статистика и фильтры по статусу курсов: Новые, В процессе, Инциденты, Завершено.
 */
const ProgressStats = ({
  availableCount,
  inProgressCount,
  incidentCount,
  completedCount,
  statusFilter,
  incidentFilter,
  onStatusFilterChange,
  onIncidentFilterChange,
  searchQuery,
}) => {
  const isAvailableActive = statusFilter === 'available';
  const isInProgressActive = statusFilter === 'in_progress';
  const isIncidentActive = incidentFilter === 'true';
  const isCompletedActive = statusFilter === 'completed';

  return (
    <div className="progress-stats">
      <button
        type="button"
        className={`progress-stats__item progress-stats__item--available filter-btn ${isAvailableActive ? 'active' : ''}`}
        onClick={() => onStatusFilterChange('available')}
        aria-pressed={isAvailableActive}
      >
        <span className="progress-stats__number">{availableCount}</span>
        <span className="progress-stats__label">Новые</span>
      </button>
      <button
        type="button"
        className={`progress-stats__item progress-stats__item--in-progress filter-btn ${isInProgressActive ? 'active' : ''}`}
        onClick={() => onStatusFilterChange('in_progress')}
        aria-pressed={isInProgressActive}
      >
        <span className="progress-stats__number">{inProgressCount}</span>
        <span className="progress-stats__label">В процессе</span>
      </button>
      <button
        type="button"
        className={`progress-stats__item filter-btn ${isIncidentActive ? 'active' : ''}`}
        onClick={() => onIncidentFilterChange(isIncidentActive ? 'all' : 'true')}
        aria-pressed={isIncidentActive}
      >
        <span className="progress-stats__number progress-stats__number--incident">{incidentCount}</span>
        <span className="progress-stats__label">Инциденты</span>
      </button>
      <button
        type="button"
        className={`progress-stats__item progress-stats__item--completed filter-btn ${isCompletedActive ? 'active' : ''}`}
        onClick={() => onStatusFilterChange('completed')}
        aria-pressed={isCompletedActive}
      >
        <span className="progress-stats__number">{completedCount}</span>
        <span className="progress-stats__label">Завершено</span>
      </button>
    </div>
  );
};

export default ProgressStats;
