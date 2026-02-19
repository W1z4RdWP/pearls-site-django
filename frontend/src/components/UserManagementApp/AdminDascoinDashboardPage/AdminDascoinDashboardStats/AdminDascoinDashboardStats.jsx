import './AdminDascoinDashboardStats.css';

const AdminDascoinDashboardStats = ({ totalSpentPoints, totalDascoinPoints, lastAwardDate }) => {
  const formatDate = (dateStr) => {
    if (!dateStr) return null;
    const [date, time] = dateStr.split(' ');
    return { date, time };
  };

  const lastAward = formatDate(lastAwardDate);

  return (
    <div className="admin-dascoin-dashboard-stats">
      <div className="admin-dascoin-dashboard-stats__grid">
        <div className="admin-dascoin-dashboard-stats__card admin-dascoin-dashboard-stats__card--spent">
          <div className="admin-dascoin-dashboard-stats__content">
            <div className="admin-dascoin-dashboard-stats__icon">
              <i className="fa-solid fa-minus-circle" aria-hidden="true" />
            </div>
            <div className="admin-dascoin-dashboard-stats__info">
              <div className="admin-dascoin-dashboard-stats__value">{totalSpentPoints}</div>
              <div className="admin-dascoin-dashboard-stats__label">Потрачено баллов</div>
            </div>
          </div>
        </div>
        <div className="admin-dascoin-dashboard-stats__card admin-dascoin-dashboard-stats__card--total">
          <div className="admin-dascoin-dashboard-stats__content">
            <div className="admin-dascoin-dashboard-stats__icon">
              <i className="fa-solid fa-coins" aria-hidden="true" />
            </div>
            <div className="admin-dascoin-dashboard-stats__info">
              <div className="admin-dascoin-dashboard-stats__value">{totalDascoinPoints}</div>
              <div className="admin-dascoin-dashboard-stats__label">Общее количество DASCOIN</div>
            </div>
          </div>
        </div>
        <div className="admin-dascoin-dashboard-stats__card admin-dascoin-dashboard-stats__card--last">
          <div className="admin-dascoin-dashboard-stats__content">
            <div className="admin-dascoin-dashboard-stats__icon">
              <i className="fa-solid fa-clock" aria-hidden="true" />
            </div>
            <div className="admin-dascoin-dashboard-stats__info">
              {lastAward ? (
                <>
                  <div className="admin-dascoin-dashboard-stats__value">{lastAward.date}</div>
                  <div className="admin-dascoin-dashboard-stats__label">
                    {lastAward.time} - Последнее начисление
                  </div>
                </>
              ) : (
                <>
                  <div className="admin-dascoin-dashboard-stats__value">—</div>
                  <div className="admin-dascoin-dashboard-stats__label">Нет данных</div>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminDascoinDashboardStats;
