import { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { logoutUser } from '../../../api/api';
import './Header.css';
import NotificationBellCluster from './NotificationBellCluster/NotificationBellCluster';
import {
  fetchNotificationCount,
  fetchNotificationsDropdown,
  markAllNotificationsRead,
} from '../../../api/notifications_api';

const Header = ({ user, isAuthenticated, isExternal, navPublic, navStaff, navMentor, refreshLayout }) => {
  const [menuOpen, setMenuOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [notificationCount, setNotificationCount] = useState(0);
  const [notificationItems, setNotificationItems] = useState([]);
  const [notificationsLoading, setNotificationsLoading] = useState(false);
  const [notificationsError, setNotificationsError] = useState(null);

  const navigate = useNavigate();

  const toggleMenu = () => setMenuOpen((prev) => !prev);
  const toggleProfile = () => {
    setNotificationsOpen(false);
    setProfileOpen((prev) => !prev);
  };
  const closeAll = () => {
    setMenuOpen(false);
    setProfileOpen(false);
    setNotificationsOpen(false);
  };

  const refreshNotificationCount = useCallback(() => {
    if (!isAuthenticated) return;
    fetchNotificationCount()
      .then((data) => setNotificationCount(data.count))
      .catch(() => {});
  }, [isAuthenticated]);

  useEffect(() => {
    refreshNotificationCount();
    if (!isAuthenticated) return undefined;
    const id = setInterval(refreshNotificationCount, 30000);
    return () => clearInterval(id);
  }, [isAuthenticated, refreshNotificationCount]);

  const handleNotificationToggle = async () => {
    setProfileOpen(false);
    if (notificationsOpen) {
      setNotificationsOpen(false);
      return;
    }
    setNotificationsOpen(true);
    setNotificationsLoading(true);
    setNotificationsError(null);
    try {
      await markAllNotificationsRead();
      const data = await fetchNotificationsDropdown();
      setNotificationItems(data.notifications || []);
      setNotificationCount(0);
    } catch (err) {
      console.error('Уведомления:', err);
      setNotificationsError('Ошибка загрузки');
      setNotificationItems([]);
    } finally {
      setNotificationsLoading(false);
    }
  };

  const handleLogout = async () => {
    closeAll();
    try {
      await logoutUser();
      await refreshLayout();
      navigate('/users/login', { replace: true });
    } catch (err) {
      console.error('Ошибка при выходе:', err);
    }
  };

  const avatarUrl = user?.avatar_url || '/media/profile_pics/default.jpg';


  return (
    <header className="header">
      <nav className="header__nav">
        <div className="header__container">
          {/* Логотип */}
          {!isExternal ? (
            <Link to="/" className="header__logo-link" onClick={closeAll}>
              <img
                src="/static/global/imgs/logo_light_theme.png"
                alt="Логотип"
                className="header__logo"
              />
            </Link>
          ) : (
            <img
              src="/static/global/imgs/logo_light_theme.png"
              alt="Логотип"
              className="header__logo"
            />
          )}

          {/* Мобильные кнопки */}
          <div className="header__mobile-actions">
            {isAuthenticated && (
              <NotificationBellCluster
                notificationCount={notificationCount}
                notificationsOpen={notificationsOpen}
                notificationItems={notificationItems}
                notificationsLoading={notificationsLoading}
                notificationsError={notificationsError}
                onToggle={handleNotificationToggle}
                onClose={closeAll}
              />
            )}
            {isAuthenticated && (
              <div className="header__mobile-profile">
                <button
                  className="header__avatar-btn"
                  onClick={toggleProfile}
                  aria-label="Профиль"
                >
                  <img src={avatarUrl} alt="Аватар" className="header__avatar" />
                </button>
                {profileOpen && (
                  <div className="header__dropdown header__dropdown--mobile">
                    <ProfileDropdownItems user={user} isExternal={isExternal} onClose={closeAll} onLogout={handleLogout} />
                  </div>
                )}
              </div>
            )}
            <button
              className="header__burger"
              onClick={toggleMenu}
              aria-label="Меню"
              aria-expanded={menuOpen}
            >
              <i className={menuOpen ? 'fas fa-times' : 'fas fa-bars'} />
            </button>
          </div>

          {/* Навигация */}
          <div className={`header__nav-collapse ${menuOpen ? 'header__nav-collapse--open' : ''}`}>
            <ul className="header__nav-list">
              {/* Публичные ссылки */}
              {isAuthenticated && !isExternal && navPublic?.map((item) => (
                <li key={item.url} className="header__nav-item">
                  <Link to={item.url} className="header__nav-link" onClick={closeAll}>
                    <i className={item.icon} />
                    <span>{item.label}</span>
                  </Link>
                </li>
              ))}

              {/* Ссылки для наставника */}
              {isAuthenticated && user?.is_mentor && !user?.is_superuser && !user?.is_staff && navMentor?.map((item) => (
                <li key={`mentor-${item.url}`} className="header__nav-item">
                  <Link to={item.url} className="header__nav-link" title={item.label} onClick={closeAll}>
                    <i className={item.icon} />
                  </Link>
                </li>
              ))}

              {/* Ссылки для персонала */}
              {isAuthenticated && user?.is_staff && navStaff?.map((item) => (
                <li key={`staff-${item.url}`} className="header__nav-item">
                  <Link to={item.url} className="header__nav-link" title={item.label} onClick={closeAll}>
                    <i className={item.icon} />
                  </Link>
                </li>
              ))}

              {/* Админ панель */}
              {isAuthenticated && user?.is_superuser && (
                <li className="header__nav-item">
                  <a href="/admin" className="header__nav-link" title="Админ панель">
                    <i className="fa-solid fa-screwdriver-wrench" />
                  </a>
                </li>
              )}

              {/* Войти — только в мобильном меню (на десктопе кнопка справа) */}
              {!isAuthenticated && (
                <li className="header__nav-item header__nav-item--login-only">
                  <Link to="/users/login" className="header__nav-link" onClick={closeAll}>
                    <i className="fa-solid fa-right-to-bracket" />
                    <span>Войти</span>
                  </Link>
                </li>
              )}
            </ul>
          </div>

          {/* Правый угол: уведомления, профиль или кнопка Войти */}
          <div className="header__desktop-actions">
            {isAuthenticated ? (
              <>
              <NotificationBellCluster
                notificationCount={notificationCount}
                notificationsOpen={notificationsOpen}
                notificationItems={notificationItems}
                notificationsLoading={notificationsLoading}
                notificationsError={notificationsError}
                onToggle={handleNotificationToggle}
                onClose={closeAll}
              />
              <div className="header__profile-wrapper">
                <button
                  className="header__avatar-btn"
                  onClick={toggleProfile}
                  aria-label="Профиль"
                >
                  <img src={avatarUrl} alt="Аватар" className="header__avatar" />
                </button>
                {profileOpen && (
                  <div className="header__dropdown">
                    <ProfileDropdownItems user={user} isExternal={isExternal} onClose={closeAll} onLogout={handleLogout} />
                  </div>
                )}
              </div>
              </>
            ) : (
              <Link to="/users/login" className="header__login-link">
                <i className="fa-solid fa-right-to-bracket" />
                <span>Войти</span>
              </Link>
            )}
          </div>
        </div>
      </nav>
    </header>
  );
};

/**
 * Элементы выпадающего меню профиля.
 */
const ProfileDropdownItems = ({ user, isExternal, onClose, onLogout }) => (
  <ul className="header__dropdown-list">
    <li>
      <a href="/users/profile/" className="header__dropdown-item" onClick={onClose}>
        Профиль
      </a>
    </li>
    {!isExternal && (
      <>
        <li>
          <a href="/users/profile/transactions/" className="header__dropdown-item" onClick={onClose}>
            История транзакций
          </a>
        </li>
        <li>
          <a href="/courses/trajectories/" className="header__dropdown-item" onClick={onClose}>
            Ваши траектории и курсы
          </a>
        </li>
        <li>
          <a href="/courses/user-certificates/" className="header__dropdown-item" onClick={onClose}>
            Ваши сертификаты
          </a>
        </li>
        <li>
          <a href="/users/profile/quiz-attempts-report/" className="header__dropdown-item" onClick={onClose}>
            Ваши попытки тестов
          </a>
        </li>
      </>
    )}
    <li className="header__dropdown-divider" />
    <li>
      <button
        type="button"
        className="header__dropdown-item header__dropdown-item--btn"
        onClick={onLogout}
      >
        Выйти
      </button>
    </li>
  </ul>
);

export default Header;
