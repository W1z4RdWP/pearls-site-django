import './AdminUserInfo.css';

const AdminUserInfo = ({ user }) => {
  const getUserStatusBadge = () => {
    if (!user.is_active) {
      return (
        <span className="admin-user-info__badge admin-user-info__badge--danger">
          <i className="fa-solid fa-ban" aria-hidden="true" />
          Неактивен
        </span>
      );
    }
    if (user.profile.is_approved) {
      return (
        <span className="admin-user-info__badge admin-user-info__badge--success">
          <i className="fa-solid fa-check" aria-hidden="true" />
          Активен
        </span>
      );
    }
    return (
      <span className="admin-user-info__badge admin-user-info__badge--warning">
        <i className="fa-solid fa-clock" aria-hidden="true" />
        Ожидает
      </span>
    );
  };

  return (
    <div className="admin-user-info">
      <div className="admin-user-info__row">
        <div className="admin-user-info__left">
          <div className="admin-user-info__user">
            {user.profile.image ? (
              <img
                src={user.profile.image}
                className="admin-user-info__avatar"
                alt={user.full_name}
                width="64"
                height="64"
              />
            ) : (
              <div className="admin-user-info__avatar admin-user-info__avatar--placeholder">
                <i className="fa-solid fa-user" aria-hidden="true" />
              </div>
            )}
            <div className="admin-user-info__details">
              <h5 className="admin-user-info__name">{user.full_name}</h5>
              <p className="admin-user-info__email">{user.email}</p>
              <div className="admin-user-info__points">
                <span className="admin-user-info__points-value">
                  {user.profile.dascoin_points} DASCOIN
                </span>
                {user.profile.dascoin_points > 0 && (
                  <i className="fa-solid fa-coins admin-user-info__points-icon" aria-hidden="true" />
                )}
              </div>
            </div>
          </div>
        </div>
        <div className="admin-user-info__right">
          <div className="admin-user-info__meta">
            {user.groups && user.groups.length > 0 && (
              <div className="admin-user-info__meta-item">
                <strong>Группы:</strong>
                <br />
                {user.groups.map((group) => (
                  <span key={group.id} className="admin-user-info__badge admin-user-info__badge--secondary">
                    {group.name}
                  </span>
                ))}
              </div>
            )}
            {user.profile.role && (
              <div className="admin-user-info__meta-item">
                <strong>Должность:</strong>
                <br />
                <span className="admin-user-info__badge admin-user-info__badge--info">
                  {user.profile.role.name}
                </span>
              </div>
            )}
            <div className="admin-user-info__meta-item">
              <strong>Статус:</strong>
              <br />
              {getUserStatusBadge()}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminUserInfo;
