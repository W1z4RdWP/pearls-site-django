import './NoOrdersAdmin.css';

const NoOrdersAdmin = () => {
  return (
    <div className="no-orders-admin">
      <i className="fas fa-shopping-bag no-orders-admin__icon" aria-hidden />
      <h3 className="no-orders-admin__title">У пользователя нет заказов</h3>
    </div>
  );
};

export default NoOrdersAdmin;
