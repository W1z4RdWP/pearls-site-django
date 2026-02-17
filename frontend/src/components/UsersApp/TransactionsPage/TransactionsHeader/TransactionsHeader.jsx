import { useNavigate } from 'react-router-dom';
import './TransactionsHeader.css';

const EXPORT_EXCEL_URL = '/users/profile/transactions/export/excel/';
const EXPORT_PDF_URL = '/users/profile/transactions/export/pdf/';

const TransactionsHeader = ({ totalTransactions }) => {
  const navigate = useNavigate();

  const handleBack = () => {
    navigate('/users/profile');
  };

  return (
    <header className="transactions-header">
      <div className="transactions-header__title-row">
        <h3 className="transactions-header__title">
          <i className="fa-solid fa-coins transactions-header__icon" aria-hidden="true" />
          История транзакций DASCOIN
        </h3>
        <div className="transactions-header__actions">
          <div className="transactions-header__export">
            <a
              href={EXPORT_EXCEL_URL}
              className="transactions-header__btn transactions-header__btn--excel"
              aria-label="Экспорт в Excel"
            >
              <i className="fa-solid fa-file-excel" aria-hidden="true" />
              <span className="transactions-header__btn-label">Excel</span>
            </a>
            <a
              href={EXPORT_PDF_URL}
              className="transactions-header__btn transactions-header__btn--pdf"
              aria-label="Экспорт в PDF"
            >
              <i className="fa-solid fa-file-pdf" aria-hidden="true" />
              <span className="transactions-header__btn-label">PDF</span>
            </a>
          </div>
          <span className="transactions-header__badge">{totalTransactions}</span>
          <button
            type="button"
            className="transactions-header__btn transactions-header__btn--back"
            onClick={handleBack}
            aria-label="Вернуться в профиль"
          >
            <i className="fa-solid fa-arrow-left" aria-hidden="true" />
            <span className="transactions-header__btn-label">Назад</span>
          </button>
        </div>
      </div>
    </header>
  );
};

export default TransactionsHeader;
