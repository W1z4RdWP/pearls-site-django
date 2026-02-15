import { useState, useEffect, useCallback } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import { fetchUserOrdersAdmin } from '../../../api/api';
import UserOrdersAdminHeader from './UserOrdersAdminHeader/UserOrdersAdminHeader';
import UserInfoBox from './UserInfoBox/UserInfoBox';
import StatsCards from '../OrderHistoryPage/StatsCards/StatsCards';
import OrderCard from '../OrderHistoryPage/OrderCard/OrderCard';
import OrderHistoryPagination from '../OrderHistoryPage/OrderHistoryPagination/OrderHistoryPagination';
import NoOrdersAdmin from './NoOrdersAdmin/NoOrdersAdmin';
import './UserOrdersAdminPage.css';

const UserOrdersAdminPage = () => {
  const { userId } = useParams();
  const [searchParams] = useSearchParams();
  const pageParam = searchParams.get('page');
  const page = Math.max(1, parseInt(pageParam || '1', 10) || 1);

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadData = useCallback(async (id, pageNum) => {
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      const result = await fetchUserOrdersAdmin(Number(id), pageNum);
      setData(result);
    } catch (err) {
      setError(err.message || 'Ошибка загрузки');
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData(userId, page);
  }, [loadData, userId, page]);

  const hasOrders = data && data.orders && data.orders.length > 0;

  return (
    <div className="user-orders-admin-page">
      <div className="user-orders-admin-page__container">
        <UserOrdersAdminHeader />

        {loading && (
          <p className="user-orders-admin-page__loading" aria-live="polite">
            Загрузка…
          </p>
        )}

        {error && (
          <p className="user-orders-admin-page__error" role="alert">
            {error}
          </p>
        )}

        {!loading && !error && data && (
          <>
            <UserInfoBox targetUser={data.target_user} />
            {hasOrders ? (
              <>
                <StatsCards
                  stats={data.stats}
                  totalPointsSpent={data.total_points_spent}
                  totalPointsRefunded={data.total_points_refunded}
                />
                <section className="user-orders-admin-page__list" aria-label="Список заказов">
                  {data.orders.map((order) => (
                    <OrderCard key={order.id} order={order} />
                  ))}
                </section>
                {data.pagination && data.pagination.num_pages > 1 && (
                  <OrderHistoryPagination
                    page={data.pagination.page}
                    numPages={data.pagination.num_pages}
                    hasPrevious={data.pagination.has_previous}
                    hasNext={data.pagination.has_next}
                  />
                )}
              </>
            ) : (
              <NoOrdersAdmin />
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default UserOrdersAdminPage;
