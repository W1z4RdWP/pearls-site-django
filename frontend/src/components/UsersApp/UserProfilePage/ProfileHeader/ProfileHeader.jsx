import './ProfileHeader.css';

const ProfileHeader = ({ user, profile, dateJoined, groups }) => {
  const displayName = [user?.first_name || '-', user?.last_name]
    .filter(Boolean)
    .filter((s) => s !== 'tg_none')
    .join(' ') || user?.username || '-';
  const showEmail = user?.email && user.email !== user?.first_name;
  const avatarUrl = profile?.avatar_url || '/media/profile_pics/default.jpg';
  const bio = profile?.bio?.trim() || 'О себе: нет информации';
  const role = profile?.role || 'Отсутствует';
  const dateOfBirth = profile?.date_of_birth || 'Отсутствует';
  const phone = profile?.phone_number || 'Отсутствует';
  const dascoinPoints = profile?.dascoin_points ?? 0;

  return (
    <header className="profile-header">
      <div className="profile-header__avatar-wrap">
        <img
          className="profile-header__avatar"
          src={avatarUrl}
          alt="Аватар"
        />
        <div className="profile-header__dascoin" aria-label="Баллы DASCOIN">
          <i className="fa fa-coins" aria-hidden="true" />
          <span className="profile-header__dascoin-value">{dascoinPoints}</span>
        </div>
      </div>
      <div className="profile-header__main">
        <div className="profile-header__top">
          <h2 className="profile-header__title">{displayName}</h2>
          {dateJoined && (
            <span className="profile-header__registered">
              Дата регистрации: {dateJoined}
            </span>
          )}
        </div>
        <div className="profile-header__details">
          {showEmail && (
            <p className="profile-header__email">{user.email}</p>
          )}
          <div className="profile-header__bio">{bio}</div>
          <div className="profile-header__fields">
            <span>Должность: <b>{role}</b></span>
            <span>Дата рождения: <b>{dateOfBirth}</b></span>
            <span>Телефон: <b>{phone}</b></span>
          </div>
          <div className="profile-header__groups">
            {groups?.length === 1 && (
              <p>Вы состоите в группе: <b>{groups[0].name}</b></p>
            )}
            {groups?.length > 1 && (
              <>
                <p>Группы пользователя:</p>
                <ul>
                  {groups.map((g) => (
                    <li key={g.id}><b>{g.name}</b></li>
                  ))}
                </ul>
              </>
            )}
            {(!groups || groups.length === 0) && (
              <p>Пользователь не состоит в группах</p>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

export default ProfileHeader;
