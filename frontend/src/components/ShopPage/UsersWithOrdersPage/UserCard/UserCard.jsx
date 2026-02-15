import { Link } from 'react-router-dom';
import './UserCard.css';

const UserCard = ({ user }) => {
  return (
    <article className="user-card" aria-labelledby={`user-name-${user.id}`}>
      <div className="user-card__header">
        <div className="user-card__info">
          <h3 id={`user-name-${user.id}`} className="user-card__name">
            {user.full_name}
          </h3>
          {user.email && (
            <div className="user-card__email">
              <i className="fas fa-envelope" aria-hidden />
              {user.email}
            </div>
          )}
          <div className="user-card__stats">
            <div className="user-card__stat-item">
              <span className="user-card__stat-label">Заказов</span>
              <span className="user-card__stat-value">{user.orders_count}</span>
            </div>
            <div className="user-card__stat-item">
              <span className="user-card__stat-label">Потрачено баллов</span>
              <span className="user-card__stat-value">{user.total_spent}</span>
            </div>
            {user.last_order_date && (
              <div className="user-card__stat-item">
                <span className="user-card__stat-label">Последний заказ</span>
                <span className="user-card__stat-value user-card__stat-value--date">
                  {user.last_order_date}
                </span>
              </div>
            )}
          </div>
        </div>
        <Link
          to={`/shop/admin/user/${user.id}/orders`}
          className="user-card__link"
          aria-label={`История покупок: ${user.full_name}`}
        >
          <i className="fas fa-shopping-bag" aria-hidden />
          История покупок
        </Link>
      </div>
    </article>
  );
};

export default UserCard;
