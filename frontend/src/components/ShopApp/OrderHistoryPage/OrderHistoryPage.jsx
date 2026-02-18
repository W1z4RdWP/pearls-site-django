import { useState, useEffect, useCallback } from 'react';
import { useOutletContext, useSearchParams } from 'react-router-dom';
import { fetchOrderHistory } from '../../../api/api';
import OrderHistoryHeader from './OrderHistoryHeader/OrderHistoryHeader';
import StatsCards from './StatsCards/StatsCards';
import OrderCard from './OrderCard/OrderCard';
import OrderHistoryPagination from './OrderHistoryPagination/OrderHistoryPagination';
import NoOrders from './NoOrders/NoOrders';
import './OrderHistoryPage.css';

const OrderHistoryPage = () => {
  const { user } = useOutletContext();
  const [searchParams] = useSearchParams();
  const pageParam = searchParams.get('page');
  const page = Math.max(1, parseInt(pageParam || '1', 10) || 1);

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadHistory = useCallback(async (pageNum) => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchOrderHistory(pageNum);
      setData(result);
    } catch (err) {
      setError(err.message || 'Ошибка загрузки истории заказов');
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadHistory(page);
  }, [loadHistory, page]);

  const isStaff = user?.is_staff ?? false;
  const isSuperuser = user?.is_superuser ?? false;
  const hasOrders = data && data.stats && data.stats.total > 0;

  return (
    <div className="order-history-page">
      <div className="order-history-page__container">
        <OrderHistoryHeader isStaff={isStaff} isSuperuser={isSuperuser} />

        {loading && (
          <p className="order-history-page__loading" aria-live="polite">
            Загрузка истории заказов…
          </p>
        )}

        {error && (
          <p className="order-history-page__error" role="alert">
            {error}
          </p>
        )}

        {!loading && !error && data && (
          <>
            {hasOrders ? (
              <>
                <StatsCards
                  stats={data.stats}
                  totalPointsSpent={data.total_points_spent}
                  totalPointsRefunded={data.total_points_refunded}
                />
                <section className="order-history-page__list" aria-label="Список заказов">
                  {data.orders.map((order) => (
                    <OrderCard key={order.id} order={order} />
                  ))}
                </section>
                {data.pagination && (
                  <OrderHistoryPagination
                    page={data.pagination.page}
                    numPages={data.pagination.num_pages}
                    hasPrevious={data.pagination.has_previous}
                    hasNext={data.pagination.has_next}
                  />
                )}
              </>
            ) : (
              <NoOrders />
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default OrderHistoryPage;
