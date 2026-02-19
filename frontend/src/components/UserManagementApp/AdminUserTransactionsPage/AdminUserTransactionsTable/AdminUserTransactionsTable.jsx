import './AdminUserTransactionsTable.css';

const TYPE_BADGES = {
  award: { label: 'Начисление', icon: 'fa-solid fa-plus', variant: 'success' },
  deduct: { label: 'Списание', icon: 'fa-solid fa-minus', variant: 'danger' },
  set: { label: 'Установка', icon: 'fa-solid fa-equals', variant: 'info' },
  correction: { label: 'Корректировка', icon: 'fa-solid fa-tools', variant: 'warning' },
};

const truncate = (str, maxLen) => {
  if (!str) return null;
  return str.length > maxLen ? str.slice(0, maxLen) + '…' : str;
};

const AdminUserTransactionsTable = ({ transactions }) => {
  return (
    <div className="admin-user-transactions-table-wrap">
      <table className="admin-user-transactions-table" aria-label="Таблица транзакций">
        <thead className="admin-user-transactions-table__head">
          <tr>
            <th className="admin-user-transactions-table__th">Дата</th>
            <th className="admin-user-transactions-table__th">Тип</th>
            <th className="admin-user-transactions-table__th">Изменение</th>
            <th className="admin-user-transactions-table__th">До</th>
            <th className="admin-user-transactions-table__th">После</th>
            <th className="admin-user-transactions-table__th">Причина</th>
            <th className="admin-user-transactions-table__th">Админ</th>
          </tr>
        </thead>
        <tbody>
          {transactions.map((t) => {
            const badge = TYPE_BADGES[t.transaction_type] || TYPE_BADGES.award;
            const isPositive = t.points_change > 0;

            return (
              <tr key={t.id} className="admin-user-transactions-table__row">
                <td className="admin-user-transactions-table__td">
                  <div className="admin-user-transactions-table__date">{t.created_at}</div>
                  <div className="admin-user-transactions-table__time">{t.created_at_time}</div>
                </td>
                <td className="admin-user-transactions-table__td">
                  <span className={`admin-user-transactions-table__badge admin-user-transactions-table__badge--${badge.variant}`}>
                    <i className={badge.icon} aria-hidden="true" />
                    <span className="admin-user-transactions-table__badge-label">{badge.label}</span>
                  </span>
                </td>
                <td className="admin-user-transactions-table__td">
                  <span className={`admin-user-transactions-table__change admin-user-transactions-table__change--${isPositive ? 'positive' : 'negative'}`}>
                    {isPositive ? '+' : ''}{t.points_change}
                  </span>
                </td>
                <td className="admin-user-transactions-table__td">
                  <span className="admin-user-transactions-table__muted">{t.points_before}</span>
                </td>
                <td className="admin-user-transactions-table__td">
                  <span className="admin-user-transactions-table__bold">{t.points_after}</span>
                </td>
                <td className="admin-user-transactions-table__td">
                  {t.reason ? (
                    <span className="admin-user-transactions-table__reason" title={t.reason}>
                      {truncate(t.reason, 50)}
                    </span>
                  ) : (
                    <span className="admin-user-transactions-table__muted">&mdash;</span>
                  )}
                </td>
                <td className="admin-user-transactions-table__td">
                  <span className="admin-user-transactions-table__admin">
                    {t.admin_user || 'Система'}
                  </span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};

export default AdminUserTransactionsTable;
