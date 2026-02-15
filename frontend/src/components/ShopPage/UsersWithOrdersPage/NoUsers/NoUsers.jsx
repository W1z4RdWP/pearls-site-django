import './NoUsers.css';

const NoUsers = ({ hasSearchQuery }) => {
  return (
    <div className="no-users">
      <i className="fas fa-users no-users__icon" aria-hidden />
      <h3 className="no-users__title">Пользователи не найдены</h3>
      <p className="no-users__text">
        {hasSearchQuery
          ? 'Попробуйте изменить поисковый запрос.'
          : 'Пока нет пользователей с покупками.'}
      </p>
    </div>
  );
};

export default NoUsers;
