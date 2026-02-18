import { useCallback, useEffect, useState } from "react";
import { useOutletContext } from 'react-router-dom';
import { fetchChatRooms, createChatRoom } from "../../../api/messenger_api";
import './MessengerPage.css';

const MessengerPage = () => {
    const { user, isAuthenticated, refreshLayout } = useOutletContext();
    const [dataLoading, setDataLoading] = useState(true);
    const [dataError, setDataError] = useState(null);
    const [chatRooms, setChatRooms] = useState([]);
    const [roomName, setRoomName] = useState('');
    const [isCreating, setIsCreating] = useState(false);
    const [createError, setCreateError] = useState(null);

    const loadMessengerData = useCallback(async () => {
        setDataLoading(true);
        setDataError(null);
        try {
            const response = await fetchChatRooms();
            setChatRooms(response?.chat_rooms || []);
        } catch (err) {
            setDataError(err.message || 'Ошибка загрузки данных мессенджера');
            setChatRooms([]);
        } finally {
            setDataLoading(false);
        }
    }, []);

    useEffect(() => {
        loadMessengerData();
    }, [loadMessengerData]);

    const handleCreateRoom = useCallback(async (e) => {
        e.preventDefault();
        setCreateError(null);
        
        if (isCreating) return;

        setIsCreating(true);
        try {
            const response = await createChatRoom(roomName.trim());
            if (response.success) {
                setRoomName('');
                // Перезагружаем список комнат
                await loadMessengerData();
                // Перенаправляем на созданную комнату (пока используем Django URL)
                if (response.chat_room?.room_id) {
                    window.location.href = `/messenger/chat/room/${response.chat_room.room_id}/`;
                }
            } else {
                setCreateError(response.error || 'Ошибка при создании комнаты');
            }
        } catch (err) {
            setCreateError(err.message || 'Ошибка при создании комнаты');
        } finally {
            setIsCreating(false);
        }
    }, [roomName, isCreating, loadMessengerData]);

    const formatDate = (dateString) => {
        if (!dateString) return '';
        const date = new Date(dateString);
        return date.toLocaleString('ru-RU', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    const getCreatorName = (room) => {
        if (room.created_by) {
            // Если created_by это объект с полями
            if (typeof room.created_by === 'object') {
                return room.created_by.first_name && room.created_by.last_name
                    ? `${room.created_by.first_name} ${room.created_by.last_name}`.trim()
                    : room.created_by.username || 'Неизвестный';
            }
            // Если это просто ID
            return 'Неизвестный';
        }
        return 'Неизвестный';
    };

    return (
        <div className="rooms-container">
            <div className="rooms-header">
                <h1>Комнаты чата</h1>
            </div>
            
            <div className="create-room-form">
                <h2>Создать новую комнату</h2>
                <form onSubmit={handleCreateRoom}>
                    <div className="form-group">
                        <label htmlFor="room-name">Название комнаты (необязательно)</label>
                        <input
                            type="text"
                            id="room-name"
                            name="name"
                            value={roomName}
                            onChange={(e) => setRoomName(e.target.value)}
                            placeholder="Введите название комнаты"
                            autoComplete="off"
                            disabled={isCreating}
                        />
                    </div>
                    {createError && (
                        <p className="create-room-form__error" role="alert">{createError}</p>
                    )}
                    <button 
                        type="submit" 
                        className="btn btn-primary"
                        disabled={isCreating}
                    >
                        {isCreating ? 'Создание...' : 'Создать комнату'}
                    </button>
                </form>
            </div>
            
            {dataLoading && (
                <p className="rooms-loading" aria-live="polite">
                    Загрузка комнат чата…
                </p>
            )}
            
            {dataError && (
                <p className="rooms-error" role="alert">
                    {dataError}
                </p>
            )}
            
            {!dataLoading && !dataError && (
                <div className="rooms-list">
                    {chatRooms.length === 0 ? (
                        <div className="room-card">
                            <p>Пока нет созданных комнат. Создайте первую комнату выше.</p>
                        </div>
                    ) : (
                        chatRooms.map((room) => (
                            <div key={room.id} className="room-card">
                                <div className="room-card-header">
                                    <div>
                                        <h3 className="room-card-title">
                                            {room.name || 'Комната без названия'}
                                        </h3>
                                        <div className="room-card-id">ID: {room.room_id}</div>
                                    </div>
                                </div>
                                <div className="room-card-meta">
                                    <span>Создатель: {getCreatorName(room)}</span>
                                    <span>Создана: {formatDate(room.created_at)}</span>
                                </div>
                                <div className="room-card-footer">
                                    <a 
                                        href={`/messenger/chat/room/${room.room_id}/`}
                                        className="btn-join"
                                    >
                                        Присоединиться
                                    </a>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            )}
        </div>
    );
};

export default MessengerPage;