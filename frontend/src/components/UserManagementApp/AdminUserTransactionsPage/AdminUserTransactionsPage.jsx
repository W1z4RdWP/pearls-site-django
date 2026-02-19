import { useState, useEffect, useCallback } from 'react';
import { useSearchParams, useParams, useNavigate } from 'react-router-dom';
import { fetchAdminUserTransactions } from '../../../api/user_management_api';
import AdminUserTransactionsHeader from './AdminUserTransactionsHeader/AdminUserTransactionsHeader';
import AdminUserInfo from './AdminUserInfo/AdminUserInfo';
import AdminUserTransactionsFilter from './AdminUserTransactionsFilter/AdminUserTransactionsFilter';
import AdminUserTransactionsTable from './AdminUserTransactionsTable/AdminUserTransactionsTable';
import AdminUserTransactionsPagination from './AdminUserTransactionsPagination/AdminUserTransactionsPagination';
import NoTransactions from './NoTransactions/NoTransactions';
import './AdminUserTransactionsPage.css';

const AdminUserTransactionsPage = () => {
  const { userId } = useParams();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  
  const pageParam = searchParams.get('page');
  const typeParam = searchParams.get('type') || '';
  const page = Math.max(1, parseInt(pageParam || '1', 10) || 1);

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadData = useCallback(async (pageNum, type) => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchAdminUserTransactions(userId, pageNum, type);
      setData(result);
    } catch (err) {
      setError(err.message || 'Ошибка загрузки истории транзакций');
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    loadData(page, typeParam);
  }, [loadData, page, typeParam]);

  useEffect(() => {
    document.title = data?.user ? `История транзакций DASCOIN - ${data.user.full_name}` : 'История транзакций DASCOIN';
    return () => { document.title = 'Главная'; };
  }, [data?.user]);

  const handleBack = useCallback(() => {
    navigate('/user_management/admin/dascoin_dashboard/');
  }, [navigate]);

  const hasTransactions = data && data.transactions && data.transactions.length > 0;

  return (
    <main className="admin-user-transactions-page" aria-label="История транзакций DASCOIN">
      <div className="admin-user-transactions-page__container">
        <AdminUserTransactionsHeader
          totalTransactions={data?.total_transactions ?? 0}
          userId={userId}
          onBack={handleBack}
        />

        {loading && (
          <p className="admin-user-transactions-page__loading" aria-live="polite">
            Загрузка истории транзакций…
          </p>
        )}

        {error && (
          <p className="admin-user-transactions-page__error" role="alert">
            {error}
          </p>
        )}

        {!loading && !error && data && (
          <>
            <AdminUserInfo user={data.user} />

            <AdminUserTransactionsFilter
              stats={data.stats}
              totalTransactions={data.total_transactions}
              currentFilter={data.current_filter}
            />

            {hasTransactions ? (
              <>
                <AdminUserTransactionsTable transactions={data.transactions} />
                {data.pagination && data.pagination.num_pages > 1 && (
                  <AdminUserTransactionsPagination
                    pagination={data.pagination}
                    currentFilter={data.current_filter}
                    userId={userId}
                  />
                )}
              </>
            ) : (
              <NoTransactions currentFilter={data.current_filter} userId={userId} />
            )}
          </>
        )}
      </div>
    </main>
  );
};

export default AdminUserTransactionsPage;
