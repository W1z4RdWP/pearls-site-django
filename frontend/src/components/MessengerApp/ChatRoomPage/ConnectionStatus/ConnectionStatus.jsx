import './ConnectionStatus.css';

const ConnectionStatus = ({ status, onReconnect }) => {
  const getStatusText = () => {
    switch (status) {
      case 'connecting':
        return 'Подключение...';
      case 'connected':
        return 'Подключено';
      case 'disconnected':
        return 'Отключено';
      default:
        return 'Неизвестное состояние';
    }
  };

  if (status === 'connected') {
    return null; // Не показываем статус когда подключено
  }

  return (
    <div className={`connection-status connection-status--${status}`}>
      <span>{getStatusText()}</span>
      {status === 'disconnected' && onReconnect && (
        <button
          type="button"
          className="connection-status__reconnect-btn"
          onClick={onReconnect}
        >
          Переподключиться
        </button>
      )}
    </div>
  );
};

export default ConnectionStatus;
