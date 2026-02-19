import './AdminDascoinDashboardHeader.css';

const EXPORT_EXCEL_URL = '/user_management/admin/stats/export/excel/';
const EXPORT_PDF_URL = '/user_management/admin/stats/export/pdf/';

const AdminDascoinDashboardHeader = ({ isMentorOnly }) => {
  const title = isMentorOnly
    ? 'Статистика моей группы по баллам DASCOIN'
    : 'Статистика пользователей по баллам DASCOIN';

  return (
    <header className="admin-dascoin-dashboard-header">
      <div className="admin-dascoin-dashboard-header__title-row">
        <h3 className="admin-dascoin-dashboard-header__title">
          <i className="fa-solid fa-chart-line admin-dascoin-dashboard-header__icon" aria-hidden="true" />
          {title}
        </h3>
        {!isMentorOnly && (
          <div className="admin-dascoin-dashboard-header__actions">
            <a
              href={EXPORT_EXCEL_URL}
              className="admin-dascoin-dashboard-header__btn admin-dascoin-dashboard-header__btn--excel"
              aria-label="Экспорт в Excel"
            >
              <i className="fa-solid fa-file-excel" aria-hidden="true" />
              <span className="admin-dascoin-dashboard-header__btn-label">Экспорт Excel</span>
            </a>
            <a
              href={EXPORT_PDF_URL}
              className="admin-dascoin-dashboard-header__btn admin-dascoin-dashboard-header__btn--pdf"
              aria-label="Экспорт в PDF"
            >
              <i className="fa-solid fa-file-pdf" aria-hidden="true" />
              <span className="admin-dascoin-dashboard-header__btn-label">Экспорт PDF</span>
            </a>
          </div>
        )}
      </div>
    </header>
  );
};

export default AdminDascoinDashboardHeader;
