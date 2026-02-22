import './CourseSearch.css';

/**
 * Поиск по названию курса и кнопка «Очистить».
 */
const CourseSearch = ({ searchQuery, onSearchChange, onClear, hasActiveFilters }) => {
  const handleSubmit = (e) => {
    e.preventDefault();
  };

  return (
    <div className="course-search">
      <form onSubmit={handleSubmit} className="course-search__form">
        <div className="course-search__input-group input-group">
          <input
            type="text"
            className="form-control course-search__input"
            placeholder="Поиск по названию курса..."
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            autoComplete="off"
            aria-label="Поиск по названию курса"
          />
          <button type="submit" className="btn btn-primary course-search__submit" aria-label="Искать">
            <i className="fa fa-search" aria-hidden="true" />
          </button>
          {hasActiveFilters && (
            <button
              type="button"
              className="btn btn-outline-secondary course-search__clear"
              onClick={onClear}
            >
              <i className="fa fa-times" aria-hidden="true" /> Очистить
            </button>
          )}
        </div>
      </form>
    </div>
  );
};

export default CourseSearch;
