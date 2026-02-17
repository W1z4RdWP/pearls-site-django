import { useSearchParams } from 'react-router-dom';
import './NoTransactions.css';

const NoTransactions = ({ currentFilter }) => {
  const [, setSearchParams] = useSearchParams();

  const handleShowAll = () => {
    setSearchParams({});
  };

  return (
    <div className="no-transactions">
      <i className="fa-solid fa-coins no-transactions__icon" aria-hidden="true" />
      <h4 className="no-transactions__title">
        {currentFilter
          ? `Транзакции типа "${currentFilter}" не найдены`
          : 'История транзакций пуста'}
      </h4>
      <p className="no-transactions__text">
        {currentFilter ? (
          <>
            Попробуйте выбрать другой фильтр или{' '}
            <button
              type="button"
              className="no-transactions__link"
              onClick={handleShowAll}
            >
              показать все транзакции
            </button>
          </>
        ) : (
          'У вас пока нет транзакций DASCOIN'
        )}
      </p>
    </div>
  );
};

export default NoTransactions;
