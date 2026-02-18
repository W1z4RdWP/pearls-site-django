import { Link } from 'react-router-dom';
import './NoOrders.css';

const NoOrders = () => {
  return (
    <div className="no-orders">
      <i className="fas fa-shopping-bag no-orders__icon" aria-hidden />
      <h3 className="no-orders__title">У вас пока нет заказов</h3>
      <p className="no-orders__text">
        Начните делать покупки в <Link to="/shop/catalog">магазине</Link>!
      </p>
    </div>
  );
};

export default NoOrders;
