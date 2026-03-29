import { getNotificationIconClass } from '../../../../utils/notificationIcons';

/**
 * Колокольчик и панель уведомлений (дублируется в мобильной и десктопной зонах; видна одна).
 */
const NotificationBellCluster = ({
    notificationCount,
    notificationsOpen,
    notificationItems,
    notificationsLoading,
    notificationsError,
    onToggle,
    onClose,
  }) => {
    const badgeText = notificationCount > 99 ? '99+' : String(notificationCount);
  
    return (
      <div className="header__notification-wrap">
        <button
          type="button"
          className="header__notification-btn"
          onClick={() => { void onToggle(); }}
          aria-label="Уведомления"
          aria-expanded={notificationsOpen}
        >
          <i className="fas fa-bell" />
          {notificationCount > 0 ? (
            <span className="header__notification-badge">{badgeText}</span>
          ) : null}
        </button>
        {notificationsOpen ? (
          <div className="header__dropdown header__notification-dropdown">
            {notificationsLoading ? (
              <div className="header__notification-center">
                <i className="fas fa-spinner fa-spin" aria-hidden />
                <span> Загрузка...</span>
              </div>
            ) : notificationsError ? (
              <div className="header__notification-center header__notification-center--error">
                {notificationsError}
              </div>
            ) : notificationItems.length === 0 ? (
              <>
                <div className="header__notification-header">
                  <span className="header__notification-title">Уведомления</span>
                  <span className="header__notification-meta">Нет непрочитанных</span>
                </div>
                <div className="header__notification-divider" />
                <div className="header__notification-empty">
                  <i className="fas fa-bell-slash" aria-hidden />
                  <p>Нет новых уведомлений</p>
                </div>
                <div className="header__notification-divider" />
                <div className="header__notification-footer">
                  <a href="/notifications/" className="header__notification-all-btn" onClick={onClose}>
                    Посмотреть все уведомления
                  </a>
                </div>
              </>
            ) : (
              <>
                <div className="header__notification-header header__notification-header--gradient">
                  <span className="header__notification-title">
                    <i className="fas fa-bell header__notification-title-icon" aria-hidden />
                    Уведомления
                  </span>
                  {notificationItems.some((n) => !n.is_read) ? (
                    <span className="header__notification-pill">
                      {notificationItems.filter((n) => !n.is_read).length}
                    </span>
                  ) : null}
                </div>
                <div className="header__notification-divider" />
                <ul className="header__notification-list">
                  {notificationItems.map((n) => (
                    <li
                      key={n.id}
                      className={`header__notification-item${n.is_read ? '' : ' header__notification-item--unread'}`}
                    >
                      {n.url && n.url !== '#' ? (
                        <a href={n.url} className="header__notification-item-link" onClick={onClose}>
                          <NotificationRowContent n={n} />
                        </a>
                      ) : (
                        <div className="header__notification-item-link header__notification-item-link--static">
                          <NotificationRowContent n={n} />
                        </div>
                      )}
                    </li>
                  ))}
                </ul>
                <div className="header__notification-divider" />
                <div className="header__notification-footer">
                  <a href="/notifications/" className="header__notification-all-btn header__notification-all-btn--outline" onClick={onClose}>
                    <i className="fas fa-list" aria-hidden />
                    Посмотреть все уведомления
                  </a>
                </div>
              </>
            )}
          </div>
        ) : null}
      </div>
    );
  };
  
  const NotificationRowContent = ({ n }) => (
    <>
      <div className="header__notification-icon-cell">
        {n.avatar_url ? (
          <img src={n.avatar_url} alt="" className="header__notification-avatar" />
        ) : (
          <span className="header__notification-icon-ring">
            <i className={getNotificationIconClass(n.notification_type)} aria-hidden />
          </span>
        )}
      </div>
      <div className="header__notification-text-cell">
        <div className="header__notification-item-title">{n.title}</div>
        <div className="header__notification-item-msg">{n.message_preview}</div>
        <div className="header__notification-item-time">
          <i className="fas fa-clock" aria-hidden />
          {n.time_ago}
        </div>
      </div>
      {!n.is_read ? (
        <span className="header__notification-dot" aria-hidden />
      ) : null}
    </>
  );

export default NotificationBellCluster;