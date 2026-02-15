import { Link } from 'react-router-dom';
import './OrderHistoryHeader.css';

const OrderHistoryHeader = ({ isStaff, isSuperuser }) => {
  const showUsersLink = isStaff || isSuperuser;

  return (
    <header className="order-history-header">
      <Link to="/shop/catalog" className="order-history-header__back-link" aria-label="Вернуться в магазин">
        <i className="fas fa-arrow-left" aria-hidden />
        <span className="order-history-header__back-text">Вернуться в магазин</span>
      </Link>
      <div className="order-history-header__row">
        <h1 className="order-history-header__title">
          <i className="fas fa-shopping-bag order-history-header__icon" aria-hidden />
          История покупок
        </h1>
        {showUsersLink && (
          <a href="/shop/admin/users/" className="order-history-header__btn" aria-label="Пользователи с покупками">
            <i className="fas fa-users" aria-hidden />
            <span>Пользователи с покупками</span>
          </a>
        )}
      </div>
    </header>
  );
};

export default OrderHistoryHeader;
