import { Link } from 'react-router-dom';
import './UsersWithOrdersHeader.css';

const UsersWithOrdersHeader = () => {
  return (
    <header className="users-with-orders-header">
      <Link
        to="/shop/history"
        className="users-with-orders-header__back-link"
        aria-label="Вернуться к истории покупок"
      >
        <i className="fas fa-arrow-left" aria-hidden />
        <span className="users-with-orders-header__back-text">Вернуться к истории покупок</span>
      </Link>
      <h1 className="users-with-orders-header__title">
        <i className="fas fa-users users-with-orders-header__icon" aria-hidden />
        Пользователи с покупками
      </h1>
    </header>
  );
};

export default UsersWithOrdersHeader;
