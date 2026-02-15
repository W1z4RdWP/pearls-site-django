import { useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import './UsersWithOrdersPagination.css';

const UsersWithOrdersPagination = ({ page, numPages, hasPrevious, hasNext, searchQuery }) => {
  const [searchParams, setSearchParams] = useSearchParams();

  const handlePage = useCallback(
    (newPage) => {
      setSearchParams((prev) => {
        const next = new URLSearchParams(prev);
        next.set('page', String(newPage));
        if (searchQuery) next.set('q', searchQuery);
        return next;
      });
    },
    [setSearchParams, searchQuery]
  );

  if (numPages <= 1) return null;

  return (
    <nav className="users-with-orders-pagination" aria-label="Навигация по страницам">
      <ul className="users-with-orders-pagination__list">
        {hasPrevious && (
          <>
            <li className="users-with-orders-pagination__item">
              <button
                type="button"
                className="users-with-orders-pagination__link"
                onClick={() => handlePage(1)}
                aria-label="Первая страница"
              >
                Первая
              </button>
            </li>
            <li className="users-with-orders-pagination__item">
              <button
                type="button"
                className="users-with-orders-pagination__link"
                onClick={() => handlePage(page - 1)}
                aria-label="Предыдущая страница"
              >
                Предыдущая
              </button>
            </li>
          </>
        )}
        <li className="users-with-orders-pagination__item users-with-orders-pagination__item--current">
          <span className="users-with-orders-pagination__current">
            Страница {page} из {numPages}
          </span>
        </li>
        {hasNext && (
          <>
            <li className="users-with-orders-pagination__item">
              <button
                type="button"
                className="users-with-orders-pagination__link"
                onClick={() => handlePage(page + 1)}
                aria-label="Следующая страница"
              >
                Следующая
              </button>
            </li>
            <li className="users-with-orders-pagination__item">
              <button
                type="button"
                className="users-with-orders-pagination__link"
                onClick={() => handlePage(numPages)}
                aria-label="Последняя страница"
              >
                Последняя
              </button>
            </li>
          </>
        )}
      </ul>
    </nav>
  );
};

export default UsersWithOrdersPagination;
