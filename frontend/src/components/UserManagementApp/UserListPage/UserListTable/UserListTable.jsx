import { useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import './UserListTable.css';

const UserListTable = ({ users, startIndex }) => {
  const navigate = useNavigate();

  const handleRowClick = useCallback((editUrl) => {
    if (editUrl) {
      navigate(editUrl);
    }
  }, [navigate]);

  return (
    <div className="user-list-table-wrap">
      <table className="user-list-table" aria-label="Таблица пользователей">
        <thead className="user-list-table__head">
          <tr>
            <th className="user-list-table__th">#</th>
            <th className="user-list-table__th">Имя пользователя</th>
            <th className="user-list-table__th">Дата рождения</th>
            <th className="user-list-table__th">Группы</th>
            <th className="user-list-table__th">Статус</th>
          </tr>
        </thead>
        <tbody>
          {users.map((user, index) => (
            <tr
              key={user.id}
              className="user-list-table__row user-list-table__row--clickable"
              onClick={() => handleRowClick(user.edit_url)}
            >
              <td className="user-list-table__td">{startIndex + index}</td>
              <td className="user-list-table__td">
                <div className="user-list-table__user-info">
                  {user.avatar_url && (
                    <img
                      src={user.avatar_url}
                      alt="avatar"
                      className="user-list-table__avatar"
                    />
                  )}
                  <div className="user-list-table__user-details">
                    <div className="user-list-table__user-name">
                      {user.full_name}
                    </div>
                    <span className="user-list-table__user-email">
                      {user.email}
                    </span>
                  </div>
                </div>
              </td>
              <td className="user-list-table__td">
                {user.date_of_birth || '—'}
              </td>
              <td className="user-list-table__td">
                {user.groups_display || '—'}
              </td>
              <td className="user-list-table__td">
                {user.is_approved ? (
                  <span className="user-list-table__status user-list-table__status--approved" title="Подтверждён">
                    ✔️ Подтверждён
                  </span>
                ) : (
                  <span className="user-list-table__status user-list-table__status--unapproved" title="Не подтверждён">
                    ⏳ Не подтверждён
                  </span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default UserListTable;
