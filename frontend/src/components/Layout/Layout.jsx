import { useState, useEffect, useCallback } from 'react';
import { Outlet } from 'react-router-dom';
import Header from './Header/Header';
import Footer from './Footer/Footer';
import { fetchLayoutData } from '../../api/api';
import { fetchNewTicketsCount } from '../../api/tech_support_api';
import './Layout.css';

const Layout = () => {
  const [layoutData, setLayoutData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [hasNewTickets, setHasNewTickets] = useState(false);

  const loadLayout = useCallback(async () => {
    try {
      const data = await fetchLayoutData();
      setLayoutData(data);
    } catch (err) {
      console.error('Ошибка загрузки данных layout:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadLayout();
  }, [loadLayout]);

  useEffect(() => {
    if (!layoutData?.is_authenticated || !(layoutData?.user?.is_staff || layoutData?.user?.is_superuser)) {
      setHasNewTickets(false);
      return undefined;
    }

    let isCancelled = false;

    const updateNewTicketsIndicator = async () => {
      try {
        const data = await fetchNewTicketsCount();
        if (!isCancelled) {
          setHasNewTickets(Boolean(data?.has_new));
        }
      } catch (err) {
        if (!isCancelled) {
          setHasNewTickets(false);
        }
      }
    };

    updateNewTicketsIndicator();
    const intervalId = window.setInterval(updateNewTicketsIndicator, 30000);

    return () => {
      isCancelled = true;
      window.clearInterval(intervalId);
    };
  }, [layoutData]);

  if (loading) {
    return (
      <div className="layout__loading">
        <div className="layout__spinner" />
        <p>Загрузка...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="layout__error">
        <p>Ошибка загрузки: {error}</p>
      </div>
    );
  }

  const {
    user,
    is_authenticated: isAuthenticated,
    is_external: isExternal,
    nav_public: navPublic,
    nav_staff: navStaff,
    nav_mentor: navMentor,
    site_version: siteVersion,
  } = layoutData;
  const isStaffUser = Boolean(user?.is_staff || user?.is_superuser);

  return (
    <>
      <Header
        user={user}
        isAuthenticated={isAuthenticated}
        isExternal={isExternal}
        navPublic={navPublic}
        navStaff={navStaff}
        navMentor={navMentor}
        refreshLayout={loadLayout}
      />

      <main className="layout__main">
        <Outlet context={{ user, isAuthenticated, isExternal, refreshLayout: loadLayout }} />
      </main>

      {/* Кнопка поддержки */}
      {isAuthenticated && (
        <a href="/tech_support/chat/" className="layout__support-btn" title="Служба поддержки">
          {!isStaffUser && <div className="layout__support-pulse" />}
          <i className="fas fa-question" />
          {isStaffUser && hasNewTickets && (
            <span className="layout__new-tickets-indicator" title="Новые тикеты" />
          )}
        </a>
      )}

      <Footer
        isAuthenticated={isAuthenticated}
        isExternal={isExternal}
        isStaff={user?.is_staff}
        siteVersion={siteVersion}
      />
    </>
  );
};

export default Layout;
