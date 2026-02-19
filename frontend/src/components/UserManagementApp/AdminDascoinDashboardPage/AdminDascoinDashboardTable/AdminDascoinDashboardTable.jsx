import { useCallback } from 'react';
import './AdminDascoinDashboardTable.css';

const AdminDascoinDashboardTable = ({ users, onUserClick }) => {
  const handleRowDoubleClick = useCallback(
    (userId) => {
      onUserClick(userId);
    },
    [onUserClick]
  );

  const getUserStatusBadge = (user) => {
    if (!user.is_active) {
      return (
        <span className="admin-dascoin-dashboard-table__badge admin-dascoin-dashboard-table__badge--danger">
          <i className="fa-solid fa-ban" aria-hidden="true" />
          Неактивен
        </span>
      );
    }
    if (user.profile.is_approved) {
      return (
        <span className="admin-dascoin-dashboard-table__badge admin-dascoin-dashboard-table__badge--success">
          <i className="fa-solid fa-check" aria-hidden="true" />
          Активен
        </span>
      );
    }
    return (
      <span className="admin-dascoin-dashboard-table__badge admin-dascoin-dashboard-table__badge--warning">
        <i className="fa-solid fa-clock" aria-hidden="true" />
        Ожидает
      </span>
    );
  };

  return (
    <div className="admin-dascoin-dashboard-table">
      <div className="admin-dascoin-dashboard-table__wrapper">
        <table className="admin-dascoin-dashboard-table__table">
          <thead className="admin-dascoin-dashboard-table__thead">
            <tr>
              <th className="admin-dascoin-dashboard-table__th">Пользователь</th>
              <th className="admin-dascoin-dashboard-table__th">Группы</th>
              <th className="admin-dascoin-dashboard-table__th">Должность</th>
              <th className="admin-dascoin-dashboard-table__th">DASCOIN</th>
              <th className="admin-dascoin-dashboard-table__th">Статус</th>
              <th className="admin-dascoin-dashboard-table__th">Дата последнего начисления</th>
            </tr>
          </thead>
          <tbody className="admin-dascoin-dashboard-table__tbody">
            {users.map((user) => (
              <tr
                key={user.id}
                className="admin-dascoin-dashboard-table__row"
                onDoubleClick={() => handleRowDoubleClick(user.id)}
                style={{ cursor: 'pointer' }}
              >
                <td className="admin-dascoin-dashboard-table__td">
                  <div className="admin-dascoin-dashboard-table__user">
                    {user.profile.image ? (
                      <img
                        src={user.profile.image}
                        className="admin-dascoin-dashboard-table__avatar"
                        alt={user.full_name}
                        width="32"
                        height="32"
                      />
                    ) : (
                      <div className="admin-dascoin-dashboard-table__avatar admin-dascoin-dashboard-table__avatar--placeholder">
                        <i className="fa-solid fa-user" aria-hidden="true" />
                      </div>
                    )}
                    <div className="admin-dascoin-dashboard-table__user-info">
                      <div className="admin-dascoin-dashboard-table__user-name">{user.full_name}</div>
                      <div className="admin-dascoin-dashboard-table__user-email">{user.email}</div>
                    </div>
                  </div>
                </td>
                <td className="admin-dascoin-dashboard-table__td">
                  {user.groups && user.groups.length > 0 ? (
                    user.groups.map((group) => (
                      <span key={group.id} className="admin-dascoin-dashboard-table__badge admin-dascoin-dashboard-table__badge--secondary">
                        {group.name}
                      </span>
                    ))
                  ) : (
                    <span className="admin-dascoin-dashboard-table__empty">—</span>
                  )}
                </td>
                <td className="admin-dascoin-dashboard-table__td">
                  {user.profile.role ? (
                    <span className="admin-dascoin-dashboard-table__badge admin-dascoin-dashboard-table__badge--info">
                      {user.profile.role.name}
                    </span>
                  ) : (
                    <span className="admin-dascoin-dashboard-table__empty">—</span>
                  )}
                </td>
                <td className="admin-dascoin-dashboard-table__td">
                  <div className="admin-dascoin-dashboard-table__points">
                    <span className="admin-dascoin-dashboard-table__points-value">
                      {user.profile.dascoin_points}
                    </span>
                    {user.profile.dascoin_points > 0 && (
                      <i className="fa-solid fa-coins admin-dascoin-dashboard-table__points-icon" aria-hidden="true" />
                    )}
                  </div>
                </td>
                <td className="admin-dascoin-dashboard-table__td">{getUserStatusBadge(user)}</td>
                <td className="admin-dascoin-dashboard-table__td admin-dascoin-dashboard-table__td--center">
                  {user.last_award_date ? (
                    <div className="admin-dascoin-dashboard-table__date">
                      <div className="admin-dascoin-dashboard-table__date-day">
                        {user.last_award_date.split(' ')[0]}
                      </div>
                      <div className="admin-dascoin-dashboard-table__date-time">
                        {user.last_award_date.split(' ')[1]}
                      </div>
                    </div>
                  ) : (
                    <span className="admin-dascoin-dashboard-table__empty">—</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default AdminDascoinDashboardTable;
