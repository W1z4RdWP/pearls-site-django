import { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { fetchTransactions } from '../../../api/users_api';
import TransactionsHeader from './TransactionsHeader/TransactionsHeader';
import TransactionsFilter from './TransactionsFilter/TransactionsFilter';
import TransactionsTable from './TransactionsTable/TransactionsTable';
import TransactionsPagination from './TransactionsPagination/TransactionsPagination';
import NoTransactions from './NoTransactions/NoTransactions';
import './TransactionsPage.css';

const TransactionsPage = () => {
  const [searchParams] = useSearchParams();
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
      const result = await fetchTransactions(pageNum, type);
      setData(result);
    } catch (err) {
      setError(err.message || 'Ошибка загрузки истории транзакций');
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData(page, typeParam);
  }, [loadData, page, typeParam]);

  useEffect(() => {
    document.title = 'История транзакций DASCOIN';
    return () => { document.title = 'Главная'; };
  }, []);

  const hasTransactions = data && data.transactions && data.transactions.length > 0;

  return (
    <main className="transactions-page" aria-label="История транзакций DASCOIN">
      <div className="transactions-page__container">
        <TransactionsHeader totalTransactions={data?.total_transactions ?? 0} />

        {loading && (
          <p className="transactions-page__loading" aria-live="polite">
            Загрузка истории транзакций…
          </p>
        )}

        {error && (
          <p className="transactions-page__error" role="alert">
            {error}
          </p>
        )}

        {!loading && !error && data && (
          <>
            <TransactionsFilter
              stats={data.stats}
              totalTransactions={data.total_transactions}
              currentFilter={data.current_filter}
            />

            {hasTransactions ? (
              <>
                <TransactionsTable transactions={data.transactions} />
                {data.pagination && data.pagination.num_pages > 1 && (
                  <TransactionsPagination
                    pagination={data.pagination}
                    currentFilter={data.current_filter}
                  />
                )}
              </>
            ) : (
              <NoTransactions currentFilter={data.current_filter} />
            )}
          </>
        )}
      </div>
    </main>
  );
};

export default TransactionsPage;
