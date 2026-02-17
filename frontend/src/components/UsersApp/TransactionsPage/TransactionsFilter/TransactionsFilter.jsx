import { useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import './TransactionsFilter.css';

const FILTER_TYPES = [
  { key: '', label: 'Все', icon: null, variant: 'secondary' },
  { key: 'award', label: 'Начисление', icon: 'fa-solid fa-plus', variant: 'success' },
  { key: 'deduct', label: 'Списание', icon: 'fa-solid fa-minus', variant: 'danger' },
  { key: 'set', label: 'Установка', icon: 'fa-solid fa-equals', variant: 'info' },
  { key: 'correction', label: 'Корректировка', icon: 'fa-solid fa-tools', variant: 'warning' },
];

const STAT_ITEMS = [
  { key: 'award', icon: 'fa-solid fa-circle-plus', variant: 'success' },
  { key: 'deduct', icon: 'fa-solid fa-circle-minus', variant: 'danger' },
  { key: 'set', icon: 'fa-solid fa-equals', variant: 'info' },
  { key: 'correction', icon: 'fa-solid fa-tools', variant: 'warning' },
];

const TransactionsFilter = ({ stats, totalTransactions, currentFilter }) => {
  const [, setSearchParams] = useSearchParams();

  const handleFilter = useCallback(
    (type) => {
      setSearchParams((prev) => {
        const next = new URLSearchParams(prev);
        if (type) {
          next.set('type', type);
        } else {
          next.delete('type');
        }
        next.set('page', '1');
        return next;
      });
    },
    [setSearchParams]
  );

  const getCount = (key) => {
    if (!key) return totalTransactions;
    return stats?.[key] ?? 0;
  };

  return (
    <div className="transactions-filter">
      <div className="transactions-filter__row">
        <div className="transactions-filter__buttons">
          <span className="transactions-filter__label">Фильтр по типу:</span>
          <div className="transactions-filter__group" role="group" aria-label="Фильтры транзакций">
            {FILTER_TYPES.map(({ key, label, icon, variant }) => (
              <button
                key={key || 'all'}
                type="button"
                className={`transactions-filter__btn transactions-filter__btn--${variant}${
                  currentFilter === key ? ' transactions-filter__btn--active' : ''
                }`}
                onClick={() => handleFilter(key)}
                title={label}
              >
                {icon && <i className={icon} aria-hidden="true" />}
                {!icon && <span>{label}</span>}
                <span className="transactions-filter__count">({getCount(key)})</span>
              </button>
            ))}
          </div>
        </div>
        <div className="transactions-filter__stats">
          <span className="transactions-filter__stats-label">Статистика:</span>
          <div className="transactions-filter__stats-grid">
            {STAT_ITEMS.map(({ key, icon, variant }) => (
              <div
                key={key}
                className={`transactions-filter__stat transactions-filter__stat--${variant}`}
              >
                <i className={icon} aria-hidden="true" />
                <span className="transactions-filter__stat-value">{stats?.[key] ?? 0}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default TransactionsFilter;
