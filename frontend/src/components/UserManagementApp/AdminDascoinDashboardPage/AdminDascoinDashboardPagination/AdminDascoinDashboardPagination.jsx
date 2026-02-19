import { useSearchParams } from 'react-router-dom';
import './AdminDascoinDashboardPagination.css';

const AdminDascoinDashboardPagination = ({ pagination, queryParams }) => {
  const [searchParams, setSearchParams] = useSearchParams();

  const handlePageChange = (pageNum) => {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      next.set('page', String(pageNum));
      return next;
    });
  };

  const getPageUrl = (pageNum) => {
    const params = new URLSearchParams(searchParams);
    params.set('page', String(pageNum));
    return `?${params.toString()}${queryParams || ''}`;
  };

  if (!pagination || pagination.num_pages <= 1) {
    return null;
  }

  const { page, num_pages, has_previous, has_next, previous_page_number, next_page_number, start_index, end_index, total_count } = pagination;

  const getPageNumbers = () => {
    const pages = [];
    const start = Math.max(1, page - 3);
    const end = Math.min(num_pages, page + 3);
    for (let i = start; i <= end; i++) {
      pages.push(i);
    }
    return pages;
  };

  return (
    <nav className="admin-dascoin-dashboard-pagination" aria-label="Навигация по страницам пользователей">
      <div className="admin-dascoin-dashboard-pagination__info">
        {start_index}-{end_index} из {total_count}
      </div>
      <ul className="admin-dascoin-dashboard-pagination__list">
        {has_previous ? (
          <>
            <li className="admin-dascoin-dashboard-pagination__item">
              <a
                href={getPageUrl(1)}
                className="admin-dascoin-dashboard-pagination__link"
                onClick={(e) => {
                  e.preventDefault();
                  handlePageChange(1);
                }}
                title="Первая страница"
              >
                <i className="fa-solid fa-angle-double-left" aria-hidden="true" />
              </a>
            </li>
            <li className="admin-dascoin-dashboard-pagination__item">
              <a
                href={getPageUrl(previous_page_number)}
                className="admin-dascoin-dashboard-pagination__link"
                onClick={(e) => {
                  e.preventDefault();
                  handlePageChange(previous_page_number);
                }}
                title="Предыдущая страница"
              >
                <i className="fa-solid fa-angle-left" aria-hidden="true" />
              </a>
            </li>
          </>
        ) : (
          <>
            <li className="admin-dascoin-dashboard-pagination__item admin-dascoin-dashboard-pagination__item--disabled">
              <span className="admin-dascoin-dashboard-pagination__link">
                <i className="fa-solid fa-angle-double-left" aria-hidden="true" />
              </span>
            </li>
            <li className="admin-dascoin-dashboard-pagination__item admin-dascoin-dashboard-pagination__item--disabled">
              <span className="admin-dascoin-dashboard-pagination__link">
                <i className="fa-solid fa-angle-left" aria-hidden="true" />
              </span>
            </li>
          </>
        )}

        {getPageNumbers().map((pageNum) => (
          <li
            key={pageNum}
            className={`admin-dascoin-dashboard-pagination__item${
              pageNum === page ? ' admin-dascoin-dashboard-pagination__item--active' : ''
            }`}
          >
            {pageNum === page ? (
              <span className="admin-dascoin-dashboard-pagination__link">{pageNum}</span>
            ) : (
              <a
                href={getPageUrl(pageNum)}
                className="admin-dascoin-dashboard-pagination__link"
                onClick={(e) => {
                  e.preventDefault();
                  handlePageChange(pageNum);
                }}
              >
                {pageNum}
              </a>
            )}
          </li>
        ))}

        {has_next ? (
          <>
            <li className="admin-dascoin-dashboard-pagination__item">
              <a
                href={getPageUrl(next_page_number)}
                className="admin-dascoin-dashboard-pagination__link"
                onClick={(e) => {
                  e.preventDefault();
                  handlePageChange(next_page_number);
                }}
                title="Следующая страница"
              >
                <i className="fa-solid fa-angle-right" aria-hidden="true" />
              </a>
            </li>
            <li className="admin-dascoin-dashboard-pagination__item">
              <a
                href={getPageUrl(num_pages)}
                className="admin-dascoin-dashboard-pagination__link"
                onClick={(e) => {
                  e.preventDefault();
                  handlePageChange(num_pages);
                }}
                title="Последняя страница"
              >
                <i className="fa-solid fa-angle-double-right" aria-hidden="true" />
              </a>
            </li>
          </>
        ) : (
          <>
            <li className="admin-dascoin-dashboard-pagination__item admin-dascoin-dashboard-pagination__item--disabled">
              <span className="admin-dascoin-dashboard-pagination__link">
                <i className="fa-solid fa-angle-right" aria-hidden="true" />
              </span>
            </li>
            <li className="admin-dascoin-dashboard-pagination__item admin-dascoin-dashboard-pagination__item--disabled">
              <span className="admin-dascoin-dashboard-pagination__link">
                <i className="fa-solid fa-angle-double-right" aria-hidden="true" />
              </span>
            </li>
          </>
        )}
      </ul>
    </nav>
  );
};

export default AdminDascoinDashboardPagination;
