import './AdminUserTransactionsHeader.css';

const EXPORT_EXCEL_URL = (userId) => `/user_management/admin/user/${userId}/transactions/export/excel/`;
const EXPORT_PDF_URL = (userId) => `/user_management/admin/user/${userId}/transactions/export/pdf/`;

const AdminUserTransactionsHeader = ({ totalTransactions, userId, onBack }) => {
  return (
    <header className="admin-user-transactions-header">
      <div className="admin-user-transactions-header__title-row">
        <h3 className="admin-user-transactions-header__title">
          <i className="fa-solid fa-coins admin-user-transactions-header__icon" aria-hidden="true" />
          История транзакций DASCOIN
        </h3>
        <div className="admin-user-transactions-header__actions">
          <div className="admin-user-transactions-header__export">
            <a
              href={EXPORT_EXCEL_URL(userId)}
              className="admin-user-transactions-header__btn admin-user-transactions-header__btn--excel"
              aria-label="Экспорт в Excel"
            >
              <i className="fa-solid fa-file-excel" aria-hidden="true" />
              <span className="admin-user-transactions-header__btn-label">Excel</span>
            </a>
            <a
              href={EXPORT_PDF_URL(userId)}
              className="admin-user-transactions-header__btn admin-user-transactions-header__btn--pdf"
              aria-label="Экспорт в PDF"
            >
              <i className="fa-solid fa-file-pdf" aria-hidden="true" />
              <span className="admin-user-transactions-header__btn-label">PDF</span>
            </a>
          </div>
          <span className="admin-user-transactions-header__badge">{totalTransactions}</span>
          <button
            type="button"
            className="admin-user-transactions-header__btn admin-user-transactions-header__btn--back"
            onClick={onBack}
            aria-label="Вернуться к панели статистики"
          >
            <i className="fa-solid fa-arrow-left" aria-hidden="true" />
            <span className="admin-user-transactions-header__btn-label">Назад</span>
          </button>
        </div>
      </div>
    </header>
  );
};

export default AdminUserTransactionsHeader;
