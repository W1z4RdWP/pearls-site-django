import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchQuizAttemptsReport } from '../../../api/users_api';
import QuizAttemptsReportHeader from './QuizAttemptsReportHeader/QuizAttemptsReportHeader';
import QuizAttemptsReportTable from './QuizAttemptsReportTable/QuizAttemptsReportTable';
import NoQuizAttempts from './NoQuizAttempts/NoQuizAttempts';
import './QuizAttemptsReportPage.css';

const QuizAttemptsReportPage = () => {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedRowIndex, setSelectedRowIndex] = useState(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchQuizAttemptsReport();
      setData(result);
    } catch (err) {
      setError(err.message || 'Ошибка загрузки отчёта по попыткам тестов и заданий');
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  useEffect(() => {
    document.title = 'Ваши попытки тестов и заданий';
    return () => { document.title = 'Главная'; };
  }, []);

  const handleRowClick = (index) => {
    setSelectedRowIndex(index);
  };

  const handleRowDoubleClick = (item) => {
    if (item.quiz_url) {
      window.location.href = item.quiz_url;
    }
  };

  const handleClickOutside = (e) => {
    if (!e.target.closest('.quiz-attempts-report-table__row')) {
      setSelectedRowIndex(null);
    }
  };

  useEffect(() => {
    document.addEventListener('click', handleClickOutside);
    return () => {
      document.removeEventListener('click', handleClickOutside);
    };
  }, []);

  const hasAttempts = data && data.report_data && data.report_data.length > 0;

  return (
    <main className="quiz-attempts-report-page" aria-label="Ваши попытки тестов и заданий">
      <div className="quiz-attempts-report-page__container">
        <QuizAttemptsReportHeader 
          totalCount={data?.total_count ?? 0}
          onBack={() => navigate('/users/profile')}
        />

        {loading && (
          <p className="quiz-attempts-report-page__loading" aria-live="polite">
            Загрузка отчёта по попыткам тестов и заданий…
          </p>
        )}

        {error && (
          <p className="quiz-attempts-report-page__error" role="alert">
            {error}
          </p>
        )}

        {!loading && !error && data && (
          <>
            {hasAttempts ? (
              <QuizAttemptsReportTable
                reportData={data.report_data}
                selectedRowIndex={selectedRowIndex}
                onRowClick={handleRowClick}
                onRowDoubleClick={handleRowDoubleClick}
              />
            ) : (
              <NoQuizAttempts />
            )}
          </>
        )}
      </div>
    </main>
  );
};

export default QuizAttemptsReportPage;
