import { Link } from 'react-router-dom';
import './ShopHeader.css';

const ShopHeader = ({ isAuthenticated, isStaff, isSuperuser, ordersCount }) => {
  return (
    <header className="shop-header">
      <div className="shop-header__row">
        <div className="shop-header__text">
          <h1 className="shop-header__title">Магазин</h1>
          <p className="shop-header__subtitle">Потратьте свои баллы DASCOIN на товары и услуги</p>
        </div>
        <div className="shop-header__actions">
          {isAuthenticated && (
            <Link to="/shop/history/" className="shop-header__cart-link" title="История покупок" aria-label="История покупок">
              <i className="fas fa-shopping-cart" aria-hidden />
              {ordersCount > 0 && (
                <span className="shop-header__cart-badge" aria-label={`Заказов: ${ordersCount}`}>
                  {ordersCount}
                </span>
              )}
            </Link>
          )}
          {(isStaff || isSuperuser) && (
            <Link to="/shop/product/create/" className="shop-header__add-link" title="Добавить товар" aria-label="Добавить товар">
              <i className="fas fa-plus" aria-hidden />
            </Link>
          )}
        </div>
      </div>
    </header>
  );
};

export default ShopHeader;
