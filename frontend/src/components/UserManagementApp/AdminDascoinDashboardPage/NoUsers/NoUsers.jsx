import { Link } from 'react-router-dom';
import './NoUsers.css';

const NoUsers = () => {
  return (
    <div className="admin-dascoin-dashboard-no-users">
      <i className="fa-solid fa-users admin-dascoin-dashboard-no-users__icon" aria-hidden="true" />
      <h4 className="admin-dascoin-dashboard-no-users__title">Пользователи не найдены</h4>
      <p className="admin-dascoin-dashboard-no-users__text">
        Попробуйте изменить параметры фильтрации или{' '}
        <Link to="/user_management/admin/dascoin_dashboard/" className="admin-dascoin-dashboard-no-users__link">
          показать всех пользователей
        </Link>
      </p>
    </div>
  );
};

export default NoUsers;
