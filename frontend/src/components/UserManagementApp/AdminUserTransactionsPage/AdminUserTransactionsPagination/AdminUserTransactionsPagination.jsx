import { useSearchParams } from 'react-router-dom';
import './AdminUserTransactionsPagination.css';

const AdminUserTransactionsPagination = ({ pagination, currentFilter, userId }) => {
  const [searchParams, setSearchParams] = useSearchParams();

  const handlePageChange = (pageNum) => {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      next.set('page', String(pageNum));
      return next;
    });
  };

  const getPageUrl = (pageNum) => {
    const params = new URLSearchParams();
    params.set('page', String(pageNum));
    if (currentFilter) params.set('type', currentFilter);
    return `?${params.toString()}`;
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
    <nav className="admin-user-transactions-pagination" aria-label="Навигация по страницам транзакций">
      <div className="admin-user-transactions-pagination__info">
        {start_index}-{end_index} из {total_count}
      </div>
      <ul className="admin-user-transactions-pagination__list">
        {has_previous ? (
          <>
            <li className="admin-user-transactions-pagination__item">
              <a
                href={getPageUrl(1)}
                className="admin-user-transactions-pagination__link"
                onClick={(e) => {
                  e.preventDefault();
                  handlePageChange(1);
                }}
                title="Первая страница"
              >
                <i className="fa-solid fa-angle-double-left" aria-hidden="true" />
              </a>
            </li>
            <li className="admin-user-transactions-pagination__item">
              <a
                href={getPageUrl(previous_page_number)}
                className="admin-user-transactions-pagination__link"
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
            <li className="admin-user-transactions-pagination__item admin-user-transactions-pagination__item--disabled">
              <span className="admin-user-transactions-pagination__link">
                <i className="fa-solid fa-angle-double-left" aria-hidden="true" />
              </span>
            </li>
            <li className="admin-user-transactions-pagination__item admin-user-transactions-pagination__item--disabled">
              <span className="admin-user-transactions-pagination__link">
                <i className="fa-solid fa-angle-left" aria-hidden="true" />
              </span>
            </li>
          </>
        )}

        {getPageNumbers().map((pageNum) => (
          <li
            key={pageNum}
            className={`admin-user-transactions-pagination__item${
              pageNum === page ? ' admin-user-transactions-pagination__item--active' : ''
            }`}
          >
            {pageNum === page ? (
              <span className="admin-user-transactions-pagination__link">{pageNum}</span>
            ) : (
              <a
                href={getPageUrl(pageNum)}
                className="admin-user-transactions-pagination__link"
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
            <li className="admin-user-transactions-pagination__item">
              <a
                href={getPageUrl(next_page_number)}
                className="admin-user-transactions-pagination__link"
                onClick={(e) => {
                  e.preventDefault();
                  handlePageChange(next_page_number);
                }}
                title="Следующая страница"
              >
                <i className="fa-solid fa-angle-right" aria-hidden="true" />
              </a>
            </li>
            <li className="admin-user-transactions-pagination__item">
              <a
                href={getPageUrl(num_pages)}
                className="admin-user-transactions-pagination__link"
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
            <li className="admin-user-transactions-pagination__item admin-user-transactions-pagination__item--disabled">
              <span className="admin-user-transactions-pagination__link">
                <i className="fa-solid fa-angle-right" aria-hidden="true" />
              </span>
            </li>
            <li className="admin-user-transactions-pagination__item admin-user-transactions-pagination__item--disabled">
              <span className="admin-user-transactions-pagination__link">
                <i className="fa-solid fa-angle-double-right" aria-hidden="true" />
              </span>
            </li>
          </>
        )}
      </ul>
      <div className="admin-user-transactions-pagination__page-info">
        <small className="admin-user-transactions-pagination__page-text">
          {page}/{num_pages}
        </small>
      </div>
    </nav>
  );
};

export default AdminUserTransactionsPagination;
