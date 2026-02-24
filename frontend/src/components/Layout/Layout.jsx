import { useState, useEffect, useCallback } from 'react';
import { Outlet } from 'react-router-dom';
import Header from './Header/Header';
import Footer from './Footer/Footer';
import { fetchLayoutData } from '../../api/api';
import './Layout.css';

const Layout = () => {
  const [layoutData, setLayoutData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

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
          <div className="layout__support-pulse" />
          <i className="fas fa-question" />
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
