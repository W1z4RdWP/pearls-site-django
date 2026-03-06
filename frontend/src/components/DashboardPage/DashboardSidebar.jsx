import { Link } from 'react-router-dom';

const DASHBOARD_LINKS_ADMIN = [
  { to: '/user_management/admin/dascoin_dashboard/', label: 'Статистика DASCOIN', icon: 'fas fa-chart-line' },
  { to: '/quizzes/', label: 'Панель управления тестам', icon: 'fa-solid fa-clipboard-question' },
  { to: '/delegation/', label: 'Делегирование', icon: 'fas fa-user-shield' },
  { to: '/builder/ipr/', label: 'ИПР', icon: 'fas fa-user-graduate' },
  { to: '/builder/trajectory-management', label: 'Управление траекториями', icon: 'fas fa-route', isReactRoute: true },
  { to: '/courses/metrics/admin/', label: 'Заполненные метрики', icon: 'fas fa-chart-bar' },
];

const DashboardSidebar = ({ usersLabel, showAdminLinks, currentPage = 'dashboard' }) => (
  <div className="dashboard-page__sidebar">
    <nav className="dashboard-page__nav" aria-label="Навигация панели управления">
      <Link
        to="/builder"
        className={`dashboard-page__nav-link ${currentPage === 'dashboard' ? 'dashboard-page__nav-link--active' : ''}`}
        aria-current={currentPage === 'dashboard' ? 'page' : undefined}
      >
        <i className="fas fa-tachometer-alt" aria-hidden />
        Панель управления
      </Link>
      <a href="/user_management/users/" className="dashboard-page__nav-link">
        <i className="fas fa-users" aria-hidden />
        {usersLabel}
      </a>
      <Link to="/reports/homework-check-dashboard" className="dashboard-page__nav-link">
        <i className="fas fa-clipboard-check" aria-hidden />
        Проверка заданий
      </Link>
      <a href="/builder/lesson/draft/history/" className="dashboard-page__nav-link">
        <i className="fas fa-history" aria-hidden />
        История правок
      </a>
      <Link
        to="/builder/incidents"
        className={`dashboard-page__nav-link ${currentPage === 'incidents' ? 'dashboard-page__nav-link--active' : ''}`}
        aria-current={currentPage === 'incidents' ? 'page' : undefined}
      >
        <i className="fas fa-exclamation-triangle" aria-hidden />
        Инциденты
      </Link>
      {showAdminLinks &&
        DASHBOARD_LINKS_ADMIN.map((item) =>
          item.isReactRoute ? (
            <Link key={item.to} to={item.to} className="dashboard-page__nav-link">
              <i className={item.icon} aria-hidden />
              {item.label}
            </Link>
          ) : (
            <a key={item.to} href={item.to} className="dashboard-page__nav-link">
              <i className={item.icon} aria-hidden />
              {item.label}
            </a>
          )
        )}
    </nav>
  </div>
);

export default DashboardSidebar;
