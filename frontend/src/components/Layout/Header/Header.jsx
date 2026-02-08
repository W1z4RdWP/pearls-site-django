import { useState } from 'react';
import { Link } from 'react-router-dom';
import './Header.css';

const Header = ({ user, isAuthenticated, isExternal, navPublic, navStaff, navMentor }) => {
  const [menuOpen, setMenuOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);

  const toggleMenu = () => setMenuOpen((prev) => !prev);
  const toggleProfile = () => setProfileOpen((prev) => !prev);
  const closeAll = () => {
    setMenuOpen(false);
    setProfileOpen(false);
  };

  // const backendUrl = import.meta.env.VITE_BACKEND_URL
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
                    <ProfileDropdownItems user={user} isExternal={isExternal} onClose={closeAll} />
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

              {/* Кнопка входа */}
              {!isAuthenticated && (
                <li className="header__nav-item">
                  <a href="/users/login/" className="header__nav-link">
                    <i className="fa-solid fa-right-to-bracket" />
                    <span>Войти</span>
                  </a>
                </li>
              )}
            </ul>
          </div>

          {/* Desktop: профиль */}
          {isAuthenticated && (
            <div className="header__desktop-actions">
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
                    <ProfileDropdownItems user={user} isExternal={isExternal} onClose={closeAll} />
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </nav>
    </header>
  );
};

/**
 * Элементы выпадающего меню профиля.
 */
const ProfileDropdownItems = ({ user, isExternal, onClose }) => (
  <ul className="header__dropdown-list">
    <li>
      <a href="/users/profile/" className="header__dropdown-item" onClick={onClose}>
        Профиль
      </a>
    </li>
    {!isExternal && (
      <>
        <li>
          <a href="/users/transactions/" className="header__dropdown-item" onClick={onClose}>
            История транзакций
          </a>
        </li>
        <li>
          <a href="/courses/trajectory/" className="header__dropdown-item" onClick={onClose}>
            Ваши траектории и курсы
          </a>
        </li>
        <li>
          <a href="/courses/certificates/" className="header__dropdown-item" onClick={onClose}>
            Ваши сертификаты
          </a>
        </li>
        <li>
          <a href="/users/quiz-attempts/" className="header__dropdown-item" onClick={onClose}>
            Ваши попытки тестов
          </a>
        </li>
      </>
    )}
    <li className="header__dropdown-divider" />
    <li>
      <form action="/users/logout/" method="post">
        <button type="submit" className="header__dropdown-item header__dropdown-item--btn">
          Выйти
        </button>
      </form>
    </li>
  </ul>
);

export default Header;
