import './ProfileActions.css';

const ProfileActions = ({ isExternal, onEditClick, isEditing }) => {
  return (
    <div className="profile-actions">
      {!isEditing && (
        <button
          type="button"
          className="profile-actions__btn"
          onClick={onEditClick}
          aria-label="Редактировать профиль"
        >
          <i className="fa fa-edit" aria-hidden="true" /> Редактировать
        </button>
      )}
      {!isEditing && (isExternal ? (
        <a
          href="https://t.me/das_metrics_bot"
          target="_blank"
          rel="noopener noreferrer"
          className="profile-actions__btn profile-actions__btn--link"
          aria-label="Отдел заботы в Telegram"
        >
          <i className="fa fa-telegram" aria-hidden="true" /> Отдел заботы
        </a>
      ) : (
        <a
          href="https://mail.smileterritory.ru"
          target="_blank"
          rel="noopener noreferrer"
          className="profile-actions__btn profile-actions__btn--link"
          aria-label="Почта"
        >
          <i className="fa fa-envelope" aria-hidden="true" /> Почта
        </a>
      ))}
    </div>
  );
};

export default ProfileActions;
