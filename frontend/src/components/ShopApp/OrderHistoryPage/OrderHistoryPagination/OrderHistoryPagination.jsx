import { useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import './OrderHistoryPagination.css';

const OrderHistoryPagination = ({ page, numPages, hasPrevious, hasNext }) => {
  const [searchParams, setSearchParams] = useSearchParams();

  const handlePage = useCallback(
    (newPage) => {
      setSearchParams((prev) => {
        const next = new URLSearchParams(prev);
        next.set('page', String(newPage));
        return next;
      });
    },
    [setSearchParams]
  );

  if (numPages <= 1) return null;

  return (
    <nav className="order-history-pagination" aria-label="Навигация по страницам">
      <ul className="order-history-pagination__list">
        {hasPrevious && (
          <>
            <li className="order-history-pagination__item">
              <button
                type="button"
                className="order-history-pagination__link"
                onClick={() => handlePage(1)}
                aria-label="Первая страница"
              >
                Первая
              </button>
            </li>
            <li className="order-history-pagination__item">
              <button
                type="button"
                className="order-history-pagination__link"
                onClick={() => handlePage(page - 1)}
                aria-label="Предыдущая страница"
              >
                Предыдущая
              </button>
            </li>
          </>
        )}
        <li className="order-history-pagination__item order-history-pagination__item--current">
          <span className="order-history-pagination__current">
            Страница {page} из {numPages}
          </span>
        </li>
        {hasNext && (
          <>
            <li className="order-history-pagination__item">
              <button
                type="button"
                className="order-history-pagination__link"
                onClick={() => handlePage(page + 1)}
                aria-label="Следующая страница"
              >
                Следующая
              </button>
            </li>
            <li className="order-history-pagination__item">
              <button
                type="button"
                className="order-history-pagination__link"
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

export default OrderHistoryPagination;
