import './ChatHeader.css';

const ChatHeader = ({ room, notificationsEnabled, isCreator, onToggleNotifications, onShowParticipants, onBackToList }) => {
  return (
    <div className="chat-header">
      <div>
        <h2>{room?.name || 'Чат'}</h2>
        <div className="chat-header__room-id">Идентификатор комнаты: {room?.room_id}</div>
      </div>
      <div className="chat-header__actions">
        <button
          type="button"
          className={`chat-header__notification-toggle ${notificationsEnabled ? 'enabled' : 'disabled'}`}
          onClick={onToggleNotifications}
          title={notificationsEnabled ? 'Уведомления включены' : 'Уведомления выключены'}
          aria-label={notificationsEnabled ? 'Выключить уведомления' : 'Включить уведомления'}
        >
          <svg className="bell-icon bell-enabled" xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
          </svg>
          <svg className="bell-icon bell-disabled" xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
            <line x1="3" y1="3" x2="21" y2="21" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
          </svg>
        </button>
        <button type="button" className="btn btn-secondary" onClick={onShowParticipants}>
          Участники
        </button>
        <button type="button" className="btn btn-secondary" onClick={onBackToList}>
          Список комнат
        </button>
      </div>
    </div>
  );
};

export default ChatHeader;
