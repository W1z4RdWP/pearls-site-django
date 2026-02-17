import { useCallback, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import './TransactionsPagination.css';

const WINDOW_SIZE = 2;

const TransactionsPagination = ({ pagination, currentFilter }) => {
  const [, setSearchParams] = useSearchParams();
  const { page, num_pages, has_previous, has_next, start_index, end_index, total_count } = pagination;

  const handlePage = useCallback(
    (newPage) => {
      setSearchParams((prev) => {
        const next = new URLSearchParams(prev);
        next.set('page', String(newPage));
        if (currentFilter) {
          next.set('type', currentFilter);
        }
        return next;
      });
    },
    [setSearchParams, currentFilter]
  );

  const pageNumbers = useMemo(() => {
    const pages = [];
    const from = Math.max(1, page - WINDOW_SIZE);
    const to = Math.min(num_pages, page + WINDOW_SIZE);
    for (let i = from; i <= to; i++) {
      pages.push(i);
    }
    return pages;
  }, [page, num_pages]);

  if (num_pages <= 1) return null;

  return (
    <nav className="transactions-pagination" aria-label="Навигация по страницам транзакций">
      <div className="transactions-pagination__row">
        <div className="transactions-pagination__info">
          {start_index}–{end_index} из {total_count}
        </div>
        <ul className="transactions-pagination__list">
          {has_previous ? (
            <>
              <li className="transactions-pagination__item">
                <button
                  type="button"
                  className="transactions-pagination__link"
                  onClick={() => handlePage(1)}
                  aria-label="Первая страница"
                >
                  <i className="fa-solid fa-angles-left" aria-hidden="true" />
                </button>
              </li>
              <li className="transactions-pagination__item">
                <button
                  type="button"
                  className="transactions-pagination__link"
                  onClick={() => handlePage(page - 1)}
                  aria-label="Предыдущая страница"
                >
                  <i className="fa-solid fa-angle-left" aria-hidden="true" />
                </button>
              </li>
            </>
          ) : (
            <>
              <li className="transactions-pagination__item transactions-pagination__item--disabled">
                <span className="transactions-pagination__link">
                  <i className="fa-solid fa-angles-left" aria-hidden="true" />
                </span>
              </li>
              <li className="transactions-pagination__item transactions-pagination__item--disabled">
                <span className="transactions-pagination__link">
                  <i className="fa-solid fa-angle-left" aria-hidden="true" />
                </span>
              </li>
            </>
          )}

          {pageNumbers.map((num) => (
            <li
              key={num}
              className={`transactions-pagination__item${
                num === page ? ' transactions-pagination__item--active' : ''
              }`}
            >
              {num === page ? (
                <span className="transactions-pagination__link" aria-current="page">{num}</span>
              ) : (
                <button
                  type="button"
                  className="transactions-pagination__link"
                  onClick={() => handlePage(num)}
                >
                  {num}
                </button>
              )}
            </li>
          ))}

          {has_next ? (
            <>
              <li className="transactions-pagination__item">
                <button
                  type="button"
                  className="transactions-pagination__link"
                  onClick={() => handlePage(page + 1)}
                  aria-label="Следующая страница"
                >
                  <i className="fa-solid fa-angle-right" aria-hidden="true" />
                </button>
              </li>
              <li className="transactions-pagination__item">
                <button
                  type="button"
                  className="transactions-pagination__link"
                  onClick={() => handlePage(num_pages)}
                  aria-label="Последняя страница"
                >
                  <i className="fa-solid fa-angles-right" aria-hidden="true" />
                </button>
              </li>
            </>
          ) : (
            <>
              <li className="transactions-pagination__item transactions-pagination__item--disabled">
                <span className="transactions-pagination__link">
                  <i className="fa-solid fa-angle-right" aria-hidden="true" />
                </span>
              </li>
              <li className="transactions-pagination__item transactions-pagination__item--disabled">
                <span className="transactions-pagination__link">
                  <i className="fa-solid fa-angles-right" aria-hidden="true" />
                </span>
              </li>
            </>
          )}
        </ul>
      </div>
      <div className="transactions-pagination__counter">
        {page} / {num_pages}
      </div>
    </nav>
  );
};

export default TransactionsPagination;
