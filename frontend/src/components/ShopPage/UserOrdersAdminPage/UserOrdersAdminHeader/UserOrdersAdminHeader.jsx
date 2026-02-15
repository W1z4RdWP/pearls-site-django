import { Link } from 'react-router-dom';
import './UserOrdersAdminHeader.css';

const UserOrdersAdminHeader = () => {
  return (
    <header className="user-orders-admin-header">
      <Link
        to="/shop/admin/users"
        className="user-orders-admin-header__back-link"
        aria-label="Вернуться к списку пользователей"
      >
        <i className="fas fa-arrow-left" aria-hidden />
        <span className="user-orders-admin-header__back-text">Вернуться к списку пользователей</span>
      </Link>
      <h1 className="user-orders-admin-header__title">
        <i className="fas fa-shopping-bag user-orders-admin-header__icon" aria-hidden />
        История покупок
      </h1>
    </header>
  );
};

export default UserOrdersAdminHeader;
