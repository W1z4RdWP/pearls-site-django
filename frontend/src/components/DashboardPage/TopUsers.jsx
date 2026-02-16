const MEDAL_COLORS = {
  1: '#FFD700',
  2: '#C0C0C0',
  3: '#CD7F32',
};

const TopUsers = ({ topUsers }) => {
  if (!topUsers || topUsers.length === 0) {
    return (
      <div className="dashboard-page__alert dashboard-page__alert--info" role="status">
        <h3 className="dashboard-page__alert-title">
          <i className="fas fa-info-circle" aria-hidden /> Нет данных
        </h3>
        <p className="dashboard-page__alert-text">
          В вашей группе пока нет пользователей с баллами DASCOIN.
        </p>
      </div>
    );
  }

  return (
    <section className="dashboard-page__section" aria-labelledby="top-users-title">
      <h2 id="top-users-title" className="dashboard-page__section-title">
        <i className="fas fa-trophy dashboard-page__section-icon" aria-hidden />
        Топ-5 пользователей по баллам DASCOIN
      </h2>
      <div className="dashboard-page__table-wrap">
        <table className="dashboard-page__table">
          <thead>
            <tr>
              <th className="dashboard-page__th-num">№</th>
              <th className="dashboard-page__th-avatar" />
              <th>Пользователь</th>
              <th className="dashboard-page__th-points">Баллы DASCOIN</th>
            </tr>
          </thead>
          <tbody>
            {topUsers.map((userItem, index) => (
              <tr key={userItem.id}>
                <td className="dashboard-page__td-num">
                  {index + 1 <= 3 ? (
                    <i
                      className="fas fa-medal"
                      style={{ color: MEDAL_COLORS[index + 1] }}
                      title={`${index + 1} место`}
                      aria-hidden
                    />
                  ) : (
                    <span className="dashboard-page__place-num">{index + 1}</span>
                  )}
                </td>
                <td className="dashboard-page__td-avatar">
                  {userItem.profile?.image_url ? (
                    <img
                      src={userItem.profile.image_url}
                      alt=""
                      className="dashboard-page__avatar"
                      width={50}
                      height={50}
                    />
                  ) : (
                    <div className="dashboard-page__avatar dashboard-page__avatar--placeholder">
                      <i className="fas fa-user" aria-hidden />
                    </div>
                  )}
                </td>
                <td>
                  <strong>{userItem.full_name}</strong>
                  <br />
                  <small className="dashboard-page__email">{userItem.email}</small>
                </td>
                <td className="dashboard-page__td-points">
                  <span className="dashboard-page__badge">
                    <i className="fas fa-gem" aria-hidden />{' '}
                    {userItem.profile?.dascoin_points ?? 0}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
};

export default TopUsers;
