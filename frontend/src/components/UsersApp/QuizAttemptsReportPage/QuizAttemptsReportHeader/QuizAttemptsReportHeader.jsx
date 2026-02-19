import './QuizAttemptsReportHeader.css';

const QuizAttemptsReportHeader = ({ totalCount, onBack }) => {
  return (
    <div className="quiz-attempts-report-header">
      <div className="quiz-attempts-report-header__top">
        <h2 className="quiz-attempts-report-header__title">
          <i className="fas fa-clipboard-list quiz-attempts-report-header__icon" aria-hidden="true" />
          Ваши попытки тестов и заданий
        </h2>
        <div className="quiz-attempts-report-header__actions">
          <span className="quiz-attempts-report-header__badge">
            {totalCount}
          </span>
          <button
            type="button"
            className="quiz-attempts-report-header__back-btn"
            onClick={onBack}
          >
            <i className="fas fa-arrow-left quiz-attempts-report-header__back-icon" aria-hidden="true" />
            Назад
          </button>
        </div>
      </div>
    </div>
  );
};

export default QuizAttemptsReportHeader;
