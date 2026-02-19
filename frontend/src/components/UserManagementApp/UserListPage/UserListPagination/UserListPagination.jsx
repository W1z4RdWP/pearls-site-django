import { useCallback, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import './UserListPagination.css';

const WINDOW_SIZE = 2;

const UserListPagination = ({ pagination, currentFilters }) => {
  const [, setSearchParams] = useSearchParams();
  const { page, num_pages, has_previous, has_next, start_index, end_index, total_count } = pagination;

  const handlePage = useCallback(
    (newPage) => {
      setSearchParams((prev) => {
        const next = new URLSearchParams(prev);
        next.set('page', String(newPage));
        
        // Сохраняем все фильтры
        if (currentFilters.q) {
          next.set('q', currentFilters.q);
        }
        if (currentFilters.filter) {
          next.set('filter', currentFilters.filter);
        }
        if (currentFilters.group) {
          next.set('group', currentFilters.group);
        }
        next.set('exclude_external', currentFilters.exclude_external ? '1' : '0');
        
        return next;
      });
    },
    [setSearchParams, currentFilters]
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
    <nav className="user-list-pagination" aria-label="Навигация по страницам пользователей">
      <div className="user-list-pagination__row">
        <div className="user-list-pagination__info">
          {start_index}–{end_index} из {total_count}
        </div>
        <ul className="user-list-pagination__list">
          {has_previous ? (
            <>
              <li className="user-list-pagination__item">
                <button
                  type="button"
                  className="user-list-pagination__link"
                  onClick={() => handlePage(1)}
                  aria-label="Первая страница"
                >
                  Первая
                </button>
              </li>
              <li className="user-list-pagination__item">
                <button
                  type="button"
                  className="user-list-pagination__link"
                  onClick={() => handlePage(page - 1)}
                  aria-label="Предыдущая страница"
                >
                  Назад
                </button>
              </li>
            </>
          ) : (
            <>
              <li className="user-list-pagination__item user-list-pagination__item--disabled">
                <span className="user-list-pagination__link">Первая</span>
              </li>
              <li className="user-list-pagination__item user-list-pagination__item--disabled">
                <span className="user-list-pagination__link">Назад</span>
              </li>
            </>
          )}

          {pageNumbers.map((num) => (
            <li
              key={num}
              className={`user-list-pagination__item${
                num === page ? ' user-list-pagination__item--active' : ''
              }`}
            >
              {num === page ? (
                <span className="user-list-pagination__link" aria-current="page">{num}</span>
              ) : (
                <button
                  type="button"
                  className="user-list-pagination__link"
                  onClick={() => handlePage(num)}
                >
                  {num}
                </button>
              )}
            </li>
          ))}

          {has_next ? (
            <>
              <li className="user-list-pagination__item">
                <button
                  type="button"
                  className="user-list-pagination__link"
                  onClick={() => handlePage(page + 1)}
                  aria-label="Следующая страница"
                >
                  Вперед
                </button>
              </li>
              <li className="user-list-pagination__item">
                <button
                  type="button"
                  className="user-list-pagination__link"
                  onClick={() => handlePage(num_pages)}
                  aria-label="Последняя страница"
                >
                  Последняя
                </button>
              </li>
            </>
          ) : (
            <>
              <li className="user-list-pagination__item user-list-pagination__item--disabled">
                <span className="user-list-pagination__link">Вперед</span>
              </li>
              <li className="user-list-pagination__item user-list-pagination__item--disabled">
                <span className="user-list-pagination__link">Последняя</span>
              </li>
            </>
          )}
        </ul>
      </div>
    </nav>
  );
};

export default UserListPagination;
