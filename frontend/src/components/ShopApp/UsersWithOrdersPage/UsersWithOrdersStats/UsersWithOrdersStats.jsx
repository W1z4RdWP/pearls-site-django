import './UsersWithOrdersStats.css';

const UsersWithOrdersStats = ({ totalUsers, totalOrders, totalPointsSpent }) => {
  return (
    <section className="users-with-orders-stats" aria-label="Статистика">
      <div className="users-with-orders-stats__item">
        <div className="users-with-orders-stats__label">Всего пользователей</div>
        <div className="users-with-orders-stats__value">{totalUsers}</div>
      </div>
      <div className="users-with-orders-stats__item">
        <div className="users-with-orders-stats__label">Всего заказов</div>
        <div className="users-with-orders-stats__value">{totalOrders}</div>
      </div>
      <div className="users-with-orders-stats__item">
        <div className="users-with-orders-stats__label">Потрачено баллов</div>
        <div className="users-with-orders-stats__value">{totalPointsSpent}</div>
      </div>
    </section>
  );
};

export default UsersWithOrdersStats;
