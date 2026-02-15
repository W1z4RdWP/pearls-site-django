import { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { fetchUsersWithOrders } from '../../../api/api';
import UsersWithOrdersHeader from './UsersWithOrdersHeader/UsersWithOrdersHeader';
import UsersWithOrdersStats from './UsersWithOrdersStats/UsersWithOrdersStats';
import SearchBox from './SearchBox/SearchBox';
import UserCard from './UserCard/UserCard';
import UsersWithOrdersPagination from './UsersWithOrdersPagination/UsersWithOrdersPagination';
import NoUsers from './NoUsers/NoUsers';
import './UsersWithOrdersPage.css';

const UsersWithOrdersPage = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const pageParam = searchParams.get('page');
  const searchQuery = searchParams.get('q') || '';
  const page = Math.max(1, parseInt(pageParam || '1', 10) || 1);

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadData = useCallback(async (pageNum, q) => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchUsersWithOrders(pageNum, q);
      setData(result);
    } catch (err) {
      setError(err.message || 'Ошибка загрузки');
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData(page, searchQuery);
  }, [loadData, page, searchQuery]);

  const handleSearch = useCallback(
    (q) => {
      setSearchParams((prev) => {
        const next = new URLSearchParams(prev);
        next.set('q', q);
        next.set('page', '1');
        return next;
      });
    },
    [setSearchParams]
  );

  const handleResetSearch = useCallback(() => {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      next.delete('q');
      next.set('page', '1');
      return next;
    });
  }, [setSearchParams]);

  const hasUsers = data && data.users && data.users.length > 0;

  return (
    <div className="users-with-orders-page">
      <div className="users-with-orders-page__container">
        <UsersWithOrdersHeader />

        {loading && (
          <p className="users-with-orders-page__loading" aria-live="polite">
            Загрузка…
          </p>
        )}

        {error && (
          <p className="users-with-orders-page__error" role="alert">
            {error}
          </p>
        )}

        {!loading && !error && data && (
          <>
            <UsersWithOrdersStats
              totalUsers={data.total_users}
              totalOrders={data.total_orders}
              totalPointsSpent={data.total_points_spent}
            />
            <SearchBox
              initialQuery={data.search_query}
              onSearch={handleSearch}
              onReset={handleResetSearch}
            />
            {hasUsers ? (
              <>
                <section className="users-with-orders-page__list" aria-label="Список пользователей">
                  {data.users.map((user) => (
                    <UserCard key={user.id} user={user} />
                  ))}
                </section>
                {data.pagination && (
                  <UsersWithOrdersPagination
                    page={data.pagination.page}
                    numPages={data.pagination.num_pages}
                    hasPrevious={data.pagination.has_previous}
                    hasNext={data.pagination.has_next}
                    searchQuery={data.search_query}
                  />
                )}
              </>
            ) : (
              <NoUsers hasSearchQuery={Boolean(data.search_query)} />
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default UsersWithOrdersPage;
