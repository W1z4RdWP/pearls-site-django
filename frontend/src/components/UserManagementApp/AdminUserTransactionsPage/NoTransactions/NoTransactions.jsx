import { Link } from 'react-router-dom';
import './NoTransactions.css';

const NoTransactions = ({ currentFilter, userId }) => {
  return (
    <div className="admin-user-transactions-no-transactions">
      <i className="fa-solid fa-coins admin-user-transactions-no-transactions__icon" aria-hidden="true" />
      <h4 className="admin-user-transactions-no-transactions__title">
        {currentFilter
          ? `Транзакции типа "${currentFilter}" не найдены`
          : 'История транзакций пуста'}
      </h4>
      <p className="admin-user-transactions-no-transactions__text">
        {currentFilter ? (
          <>
            Попробуйте выбрать другой фильтр или{' '}
            <Link
              to={`/user_management/admin/user/${userId}/transactions/`}
              className="admin-user-transactions-no-transactions__link"
            >
              показать все транзакции
            </Link>
          </>
        ) : (
          'У пользователя пока нет транзакций DASCOIN'
        )}
      </p>
    </div>
  );
};

export default NoTransactions;
