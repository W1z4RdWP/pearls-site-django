import { useState, useEffect, useCallback } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { fetchAdminDascoinDashboard } from '../../../api/user_management_api';
import AdminDascoinDashboardHeader from './AdminDascoinDashboardHeader/AdminDascoinDashboardHeader';
import AdminDascoinDashboardStats from './AdminDascoinDashboardStats/AdminDascoinDashboardStats';
import AdminDascoinDashboardFilters from './AdminDascoinDashboardFilters/AdminDascoinDashboardFilters';
import AdminDascoinDashboardTable from './AdminDascoinDashboardTable/AdminDascoinDashboardTable';
import AdminDascoinDashboardPagination from './AdminDascoinDashboardPagination/AdminDascoinDashboardPagination';
import NoUsers from './NoUsers/NoUsers';
import './AdminDascoinDashboardPage.css';

const AdminDascoinDashboardPage = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  
  const pageParam = searchParams.get('page');
  const groupParam = searchParams.get('group') || '';
  const roleParam = searchParams.get('role') || '';
  const pointsMinParam = searchParams.get('points_min') || '';
  const pointsMaxParam = searchParams.get('points_max') || '';
  const zeroPointsParam = searchParams.get('zero_points');
  const approvedParam = searchParams.get('approved');
  const showAllParam = searchParams.get('show_all');
  const topParam = searchParams.get('top');
  
  const page = Math.max(1, parseInt(pageParam || '1', 10) || 1);

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadData = useCallback(async (pageNum, filters) => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchAdminDascoinDashboard(pageNum, filters);
      setData(result);
    } catch (err) {
      setError(err.message || 'Ошибка загрузки статистики DASCOIN');
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const filters = {
      group: groupParam,
      role: roleParam,
      points_min: pointsMinParam,
      points_max: pointsMaxParam,
      zero_points: !!zeroPointsParam,
      approved_only: approvedParam === '1',
      show_all: !!showAllParam,
      top: topParam ? parseInt(topParam, 10) : null,
    };
    loadData(page, filters);
  }, [loadData, page, groupParam, roleParam, pointsMinParam, pointsMaxParam, zeroPointsParam, approvedParam, showAllParam, topParam]);

  useEffect(() => {
    document.title = data?.is_mentor_only ? 'Статистика моей группы по баллам DASCOIN' : 'Статистика пользователей по баллам DASCOIN';
    return () => { document.title = 'Главная'; };
  }, [data?.is_mentor_only]);

  const handleFilterChange = useCallback((newFilters) => {
    const params = new URLSearchParams();
    if (newFilters.group) params.set('group', newFilters.group);
    if (newFilters.role) params.set('role', newFilters.role);
    if (newFilters.points_min) params.set('points_min', newFilters.points_min);
    if (newFilters.points_max) params.set('points_max', newFilters.points_max);
    if (newFilters.zero_points) params.set('zero_points', '1');
    if (newFilters.approved_only) params.set('approved', '1');
    if (newFilters.show_all) params.set('show_all', '1');
    if (newFilters.top) params.set('top', String(newFilters.top));
    setSearchParams(params);
  }, [setSearchParams]);

  const handleQuickFilter = useCallback((filterType) => {
    const params = new URLSearchParams();
    switch (filterType) {
      case 'all':
        params.set('show_all', '1');
        break;
      case 'top10':
        params.set('top', '10');
        break;
      case 'zero':
        params.set('zero_points', '1');
        break;
      case 'approved':
        params.set('approved', '1');
        break;
      default:
        break;
    }
    setSearchParams(params);
  }, [setSearchParams]);

  const handleUserClick = useCallback((userId) => {
    navigate(`/user_management/admin/user/${userId}/transactions/`);
  }, [navigate]);

  const hasUsers = data && data.users && data.users.length > 0;

  return (
    <main className="admin-dascoin-dashboard-page" aria-label="Панель администратора - Статистика DASCOIN">
      <div className="admin-dascoin-dashboard-page__container">
        <AdminDascoinDashboardHeader isMentorOnly={data?.is_mentor_only} />

        {loading && (
          <p className="admin-dascoin-dashboard-page__loading" aria-live="polite">
            Загрузка статистики DASCOIN…
          </p>
        )}

        {error && (
          <p className="admin-dascoin-dashboard-page__error" role="alert">
            {error}
          </p>
        )}

        {!loading && !error && data && (
          <>
            <AdminDascoinDashboardStats
              totalSpentPoints={data.total_spent_points}
              totalDascoinPoints={data.total_dascoin_points}
              lastAwardDate={data.last_award_date}
            />

            <AdminDascoinDashboardFilters
              groups={data.groups}
              roles={data.roles}
              selectedGroup={data.selected_group}
              selectedRole={data.selected_role}
              pointsMin={data.points_min}
              pointsMax={data.points_max}
              topUsers={data.top_users}
              zeroPoints={data.zero_points}
              approvedOnly={data.approved_only}
              showAll={data.show_all}
              isMentorOnly={data.is_mentor_only}
              onFilterChange={handleFilterChange}
              onQuickFilter={handleQuickFilter}
            />

            {hasUsers ? (
              <>
                <AdminDascoinDashboardTable
                  users={data.users}
                  onUserClick={handleUserClick}
                />
                {data.pagination && data.pagination.num_pages > 1 && (
                  <AdminDascoinDashboardPagination
                    pagination={data.pagination}
                    queryParams={data.query_params}
                  />
                )}
              </>
            ) : (
              <NoUsers />
            )}
          </>
        )}
      </div>
    </main>
  );
};

export default AdminDascoinDashboardPage;
