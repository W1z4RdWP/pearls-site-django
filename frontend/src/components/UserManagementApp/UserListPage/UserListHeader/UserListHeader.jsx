import { Link } from 'react-router-dom';
import './UserListHeader.css';

const UserListHeader = ({ isMentorOnly }) => {
  return (
    <div className="user-list-header">
      <h1 className="user-list-header__title">
        {isMentorOnly ? 'Моя группа' : 'Пользователи'}
      </h1>
      {!isMentorOnly && (
        <Link to="/user_management/users/add/step1/" className="user-list-header__btn">
          Добавить пользователя
        </Link>
      )}
    </div>
  );
};

export default UserListHeader;
