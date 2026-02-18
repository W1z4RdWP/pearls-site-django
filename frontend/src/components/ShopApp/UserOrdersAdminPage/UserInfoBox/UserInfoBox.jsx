import './UserInfoBox.css';

const UserInfoBox = ({ targetUser }) => {
  if (!targetUser) return null;

  return (
    <div className="user-info-box">
      <h3 className="user-info-box__name">
        <i className="fas fa-user user-info-box__icon" aria-hidden />
        {targetUser.full_name}
      </h3>
      {targetUser.email && (
        <p className="user-info-box__row">
          <i className="fas fa-envelope" aria-hidden />
          {targetUser.email}
        </p>
      )}
      <p className="user-info-box__row">
        <i className="fas fa-user-tag" aria-hidden />
        @{targetUser.username}
      </p>
    </div>
  );
};

export default UserInfoBox;
