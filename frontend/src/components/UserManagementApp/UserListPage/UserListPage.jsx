import { useState, useEffect, useCallback } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { fetchUserList } from '../../../api/user_management_api';
import UserListHeader from './UserListHeader/UserListHeader';
import UserListFilter from './UserListFilter/UserListFilter';
import UserListTable from './UserListTable/UserListTable';
import UserListPagination from './UserListPagination/UserListPagination';
import NoUsers from './NoUsers/NoUsers';
import './UserListPage.css';

const UserListPage = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  
  const pageParam = searchParams.get('page');
  const qParam = searchParams.get('q') || '';
  const filterParam = searchParams.get('filter') || 'approved';
  const groupParam = searchParams.get('group') || '';
  const excludeExternalParam = searchParams.get('exclude_external');
  const excludeExternal = excludeExternalParam !== '0';
  
  const page = Math.max(1, parseInt(pageParam || '1', 10) || 1);

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadData = useCallback(async (pageNum, q, filter, group, excludeExt) => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchUserList(pageNum, q, filter, group, excludeExt);
      setData(result);
    } catch (err) {
      setError(err.message || 'Ошибка загрузки списка пользователей');
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData(page, qParam, filterParam, groupParam, excludeExternal);
  }, [loadData, page, qParam, filterParam, groupParam, excludeExternal]);

  useEffect(() => {
    document.title = data?.is_mentor_only ? 'Моя группа' : 'Пользователи';
    return () => { document.title = 'Главная'; };
  }, [data?.is_mentor_only]);

  const handleFilterChange = useCallback((filters) => {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      
      if (filters.q !== undefined) {
        if (filters.q) {
          next.set('q', filters.q);
        } else {
          next.delete('q');
        }
      }
      
      if (filters.filter !== undefined) {
        if (filters.filter) {
          next.set('filter', filters.filter);
        } else {
          next.delete('filter');
        }
      }
      
      if (filters.group !== undefined) {
        if (filters.group) {
          next.set('group', filters.group);
        } else {
          next.delete('group');
        }
      }
      
      if (filters.exclude_external !== undefined) {
        next.set('exclude_external', filters.exclude_external ? '1' : '0');
      }
      
      next.set('page', '1');
      return next;
    });
  }, [setSearchParams]);

  const hasUsers = data && data.users && data.users.length > 0;

  return (
    <main className="user-list-page" aria-label={data?.is_mentor_only ? 'Моя группа' : 'Список пользователей'}>
      <div className="user-list-page__container">
        <Link to="/builder" className="btn btn-outline-primary mb-3">
          ← Вернуться в панель управления
        </Link>
        
        <div className="user-list-page__wrapper">
          {data && (
            <UserListHeader isMentorOnly={data.is_mentor_only} />
          )}

          {loading && (
            <p className="user-list-page__loading" aria-live="polite">
              Загрузка списка пользователей…
            </p>
          )}

          {error && (
            <p className="user-list-page__error" role="alert">
              {error}
            </p>
          )}

          {!loading && !error && data && (
            <>
              <UserListFilter
                groups={data.groups}
                isMentorOnly={data.is_mentor_only}
                currentFilters={{
                  q: qParam,
                  filter: filterParam,
                  group: groupParam,
                  exclude_external: excludeExternal,
                }}
                onFilterChange={handleFilterChange}
              />

              {hasUsers ? (
                <>
                  <UserListTable users={data.users} startIndex={data.pagination.start_index} />
                  {data.pagination && data.pagination.num_pages > 1 && (
                    <UserListPagination
                      pagination={data.pagination}
                      currentFilters={{
                        q: qParam,
                        filter: filterParam,
                        group: groupParam,
                        exclude_external: excludeExternal,
                      }}
                    />
                  )}
                </>
              ) : (
                <NoUsers />
              )}
            </>
          )}
        </div>
      </div>
    </main>
  );
};

export default UserListPage;
