/**
 * Форма поиска и фильтров: текст, автор, группа.
 */
const CourseListFilters = ({
  searchQuery,
  selectedAuthor,
  selectedGroup,
  authors,
  groups,
  onSearchChange,
  onAuthorChange,
  onGroupChange,
  onSubmit,
}) => (
  <section className="course-list__filters">
    <div className="course-list__filters-card">
      <form
        className="course-list__filters-form"
        onSubmit={(e) => {
          e.preventDefault();
          onSubmit();
        }}
      >
        <div className="course-list__filters-row">
          <div className="course-list__filters-search-wrap">
            <input
              type="text"
              className="course-list__filters-input"
              name="search"
              placeholder="Поиск по названию курса..."
              value={searchQuery}
              onChange={(e) => onSearchChange(e.target.value)}
              aria-label="Поиск по названию курса"
            />
            <button type="submit" className="course-list__filters-search-btn" aria-label="Искать">
              <i className="fas fa-search" aria-hidden />
            </button>
          </div>
          <div className="course-list__filters-select-wrap">
            <select
              className="course-list__filters-select"
              name="author"
              value={selectedAuthor}
              onChange={(e) => onAuthorChange(e.target.value)}
              aria-label="Фильтр по автору"
            >
              <option value="">Все авторы</option>
              {authors?.map((a) => (
                <option key={a.id} value={String(a.id)}>
                  {a.name}
                </option>
              ))}
            </select>
          </div>
          <div className="course-list__filters-select-wrap">
            <select
              className="course-list__filters-select"
              name="group"
              value={selectedGroup}
              onChange={(e) => onGroupChange(e.target.value)}
              aria-label="Фильтр по группе"
            >
              <option value="">Все группы</option>
              {groups?.map((g) => (
                <option key={g.id} value={String(g.id)}>
                  {g.name}
                </option>
              ))}
            </select>
          </div>
        </div>
      </form>
    </div>
  </section>
);

export default CourseListFilters;
