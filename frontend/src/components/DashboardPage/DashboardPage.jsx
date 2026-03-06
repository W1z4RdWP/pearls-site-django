import { useState, useEffect, useCallback } from 'react';
import { useOutletContext } from 'react-router-dom';
import { fetchDashboardData } from '../../api/api';
import DashboardSidebar from './DashboardSidebar';
import TopUsers from './TopUsers';
import UnratedAnswers from './UnratedAnswers';
import './DashboardPage.css';

const DashboardPage = () => {
  const { user, isAuthenticated } = useOutletContext();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const isMentorOnly = user?.is_mentor && !user?.is_staff && !user?.is_superuser;
  const showAdminLinks = !isMentorOnly;

  const loadDashboard = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchDashboardData();
      setData(res);
    } catch (err) {
      setError(err.message || 'Ошибка загрузки дашборда');
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (isAuthenticated) {
      loadDashboard();
    }
  }, [isAuthenticated, loadDashboard]);

  const usersLabel = isMentorOnly ? 'Моя группа' : 'Пользователи';

  return (
    <div className="dashboard-page">
      <DashboardSidebar usersLabel={usersLabel} showAdminLinks={showAdminLinks} currentPage="dashboard" />

      <div className="dashboard-page__main">
        <div className="dashboard-page__card">
          {loading && (
            <div className="dashboard-page__loading">
              <p>Загрузка...</p>
            </div>
          )}
          {error && (
            <div className="dashboard-page__error" role="alert">
              <p>{error}</p>
            </div>
          )}
          {!loading && !error && data && (
            <>
              {isMentorOnly ? (
                <TopUsers topUsers={data.top_users_dascoin} />
              ) : (
                <UnratedAnswers
                  totalUnratedCount={data.total_unrated_count}
                  unratedTextAnswers={data.unrated_text_answers ?? []}
                />
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
