import { useState, useEffect, useCallback, useRef } from 'react';
import {
  fetchRoomParticipants,
  addRoomParticipant,
  searchUsersForRoom,
} from '../../../../api/messenger_api';
import './ParticipantsModal.css';

const ParticipantsModal = ({ roomId, isCreator, onClose }) => {
  const [participants, setParticipants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const searchTimeoutRef = useRef(null);

  const loadParticipants = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchRoomParticipants(roomId);
      setParticipants(data.participants || []);
    } catch (err) {
      setError(err.message || 'Ошибка загрузки участников');
    } finally {
      setLoading(false);
    }
  }, [roomId]);

  useEffect(() => {
    loadParticipants();
  }, [loadParticipants]);

  useEffect(() => {
    if (searchQuery.trim().length < 2) {
      setSearchResults([]);
      return;
    }

    searchTimeoutRef.current = setTimeout(async () => {
      setSearchLoading(true);
      try {
        const data = await searchUsersForRoom(roomId, searchQuery.trim());
        setSearchResults(data.users || []);
      } catch (err) {
        setSearchResults([]);
      } finally {
        setSearchLoading(false);
      }
    }, 300);

    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }
    };
  }, [searchQuery, roomId]);

  const handleAddParticipant = useCallback(async (userId) => {
    try {
      await addRoomParticipant(roomId, userId);
      // Обновляем список участников
      await loadParticipants();
      // Удаляем пользователя из результатов поиска
      setSearchResults(prev => prev.filter(u => u.id !== userId));
      // Очищаем поле поиска
      setSearchQuery('');
    } catch (err) {
      alert('Ошибка добавления участника: ' + err.message);
    }
  }, [roomId, loadParticipants]);

  const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div className="participants-modal" onClick={handleBackdropClick}>
      <div className="participants-modal__content">
        <div className="participants-modal__header">
          <h3>Участники комнаты</h3>
          <button
            type="button"
            className="participants-modal__close"
            onClick={onClose}
            aria-label="Закрыть"
          >
            ×
          </button>
        </div>
        <div className="participants-modal__body">
          <div className="participants-list">
            {loading ? (
              <p>Загрузка...</p>
            ) : error ? (
              <p className="participants-list__error">{error}</p>
            ) : participants.length === 0 ? (
              <p>Нет участников</p>
            ) : (
              participants.map((participant) => (
                <div key={participant.id} className="participant-item">
                  <div className="participant-avatar">
                    {participant.avatar_url ? (
                      <img src={participant.avatar_url} alt={participant.full_name} />
                    ) : (
                      <div className="participant-initials">{participant.initials}</div>
                    )}
                  </div>
                  <div className="participant-info">
                    <div className="participant-name">{participant.full_name}</div>
                    {participant.is_creator && (
                      <span className="participant-badge">Создатель</span>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
          
          {isCreator && (
            <div className="add-participant-section">
              <h4>Добавить участника</h4>
              <div className="search-users-container">
                <input
                  type="text"
                  className="search-users-input"
                  placeholder="Поиск пользователей..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  autoComplete="off"
                />
                {searchLoading && <p>Поиск...</p>}
                {searchResults.length > 0 && (
                  <div className="search-users-results">
                    {searchResults.map((user) => (
                      <div key={user.id} className="search-user-item">
                        <div className="search-user-avatar">
                          {user.avatar_url ? (
                            <img src={user.avatar_url} alt={user.full_name} />
                          ) : (
                            <div className="search-user-initials">{user.initials}</div>
                          )}
                        </div>
                        <div className="search-user-info">
                          <div className="search-user-name">{user.full_name}</div>
                          <div className="search-user-username">{user.username}</div>
                        </div>
                        <button
                          type="button"
                          className="btn-add-user"
                          onClick={() => handleAddParticipant(user.id)}
                        >
                          Добавить
                        </button>
                      </div>
                    ))}
                  </div>
                )}
                {searchQuery.trim().length >= 2 && !searchLoading && searchResults.length === 0 && (
                  <div className="search-no-results">Пользователи не найдены</div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ParticipantsModal;
