/**
 * Пагинация: первая, предыдущая, текущая страница, следующая, последняя.
 */
const CourseListPagination = ({ pagination, onPageChange }) => {
  if (!pagination || pagination.num_pages <= 1) return null;

  const { page, num_pages, has_previous, has_next, previous_page_number, next_page_number } = pagination;

  const handleClick = (e, pageNum) => {
    e.preventDefault();
    onPageChange(pageNum);
  };

  return (
    <nav className="course-list__pagination" aria-label="Навигация по страницам">
      <ul className="course-list__pagination-list">
        {has_previous && (
          <>
            <li className="course-list__pagination-item">
              <a
                className="course-list__pagination-link"
                href="#"
                onClick={(e) => handleClick(e, 1)}
              >
                <span className="course-list__pagination-text--full">&laquo; Первая</span>
                <span className="course-list__pagination-text--short">&laquo;</span>
              </a>
            </li>
            <li className="course-list__pagination-item">
              <a
                className="course-list__pagination-link"
                href="#"
                onClick={(e) => handleClick(e, previous_page_number)}
              >
                <span className="course-list__pagination-text--full">Предыдущая</span>
                <span className="course-list__pagination-text--short">Пред</span>
              </a>
            </li>
          </>
        )}
        <li className="course-list__pagination-item course-list__pagination-item--current">
          <span className="course-list__pagination-current">
            <span className="course-list__pagination-text--full">
              Страница {page} из {num_pages}
            </span>
            <span className="course-list__pagination-text--short">
              {page}/{num_pages}
            </span>
          </span>
        </li>
        {has_next && (
          <>
            <li className="course-list__pagination-item">
              <a
                className="course-list__pagination-link"
                href="#"
                onClick={(e) => handleClick(e, next_page_number)}
              >
                <span className="course-list__pagination-text--full">Следующая</span>
                <span className="course-list__pagination-text--short">След</span>
              </a>
            </li>
            <li className="course-list__pagination-item">
              <a
                className="course-list__pagination-link"
                href="#"
                onClick={(e) => handleClick(e, num_pages)}
              >
                <span className="course-list__pagination-text--full">Последняя &raquo;</span>
                <span className="course-list__pagination-text--short">&raquo;</span>
              </a>
            </li>
          </>
        )}
      </ul>
    </nav>
  );
};

export default CourseListPagination;
