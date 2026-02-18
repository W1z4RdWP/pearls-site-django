import { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate, useOutletContext } from 'react-router-dom';
import {
  fetchChatRoomData,
  uploadChatAttachment,
  sendChatMessage,
  fetchRoomParticipants,
  addRoomParticipant,
  searchUsersForRoom,
  toggleRoomNotifications,
} from '../../../api/messenger_api';
import { useWebSocket } from '../../../hooks/useWebSocket';
import { playReceiveSound, playSendSound } from '../../../utils/sounds';
import ChatHeader from './ChatHeader/ChatHeader';
import MessageList from './MessageList/MessageList';
import ChatInput from './ChatInput/ChatInput';
import ParticipantsModal from './ParticipantsModal/ParticipantsModal';
import ConnectionStatus from './ConnectionStatus/ConnectionStatus';
import './ChatRoomPage.css';

const ChatRoomPage = () => {
  const { roomId } = useParams();
  const navigate = useNavigate();
  const { user, isAuthenticated } = useOutletContext();
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [roomData, setRoomData] = useState(null);
  const [messages, setMessages] = useState([]);
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  const [showParticipantsModal, setShowParticipantsModal] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  
  const messagesEndRef = useRef(null);
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadRoomData = useCallback(async () => {
    if (!isAuthenticated) return;
    
    setLoading(true);
    setError(null);
    try {
      const data = await fetchChatRoomData(roomId);
      setRoomData(data);
      setMessages(data.messages || []);
      setNotificationsEnabled(data.notifications_enabled);
      setRoomData(data);
      // Прокручиваем вниз после загрузки
      setTimeout(scrollToBottom, 100);
    } catch (err) {
      setError(err.message || 'Ошибка загрузки данных чата');
      setRoomData(null);
      setMessages([]);
    } finally {
      setLoading(false);
    }
  }, [roomId, isAuthenticated]);

  // Обработчик новых сообщений из WebSocket
  const handleWebSocketMessage = useCallback((newMessage) => {
    setMessages(prev => [...prev, newMessage]);
    // Воспроизводим звук уведомления (если включены уведомления)
    if (notificationsEnabled) {
      playReceiveSound();
    }
  }, [notificationsEnabled]);

  // Обработчик ошибок WebSocket
  const handleWebSocketError = useCallback((error) => {
    console.error('WebSocket error:', error);
    // Можно показать уведомление пользователю
  }, []);

  // WebSocket подключение (подключается только после загрузки данных комнаты)
  const { connectionStatus, sendMessage, sendMessageWithAttachments, reconnect } = useWebSocket(
    roomId,
    roomData?.current_user_id,
    handleWebSocketMessage,
    handleWebSocketError
  );

  useEffect(() => {
    loadRoomData();
  }, [loadRoomData]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = useCallback(async (messageText, files) => {
    if (!messageText.trim() && (!files || files.length === 0)) {
      return;
    }

    if (files && files.length > 0) {
      // Загрузка файлов через HTTP
      setIsUploading(true);
      setUploadProgress(0);
      
      try {
        const response = await uploadChatAttachment(
          roomId,
          messageText,
          files,
          (progress) => setUploadProgress(progress)
        );
        
        if (response.success) {
          // Добавляем новое сообщение в список локально
          const newMessage = {
            id: response.message_id,
            sender_id: roomData?.current_user_id,
            sender_full_name: roomData?.current_user_name,
            content: response.message,
            created_at: response.timestamp,
            sender_avatar: roomData?.current_user_avatar,
            sender_initials: roomData?.current_user_initials,
            attachments: response.attachments || [],
          };
          
          setMessages(prev => [...prev, newMessage]);
          
          // Воспроизводим звук отправки
          playSendSound();
          
          // Уведомляем других участников через WebSocket
          sendMessageWithAttachments(
            response.message_id,
            response.message,
            response.attachments || []
          );
          
          if (response.warnings && response.warnings.length > 0) {
            alert('Предупреждения:\n' + response.warnings.join('\n'));
          }
        }
      } catch (err) {
        alert('Ошибка отправки сообщения: ' + err.message);
      } finally {
        setIsUploading(false);
        setUploadProgress(0);
      }
    } else {
      // Только текстовое сообщение - отправляем через WebSocket
      const sent = sendMessage(messageText);
      
      if (sent) {
        // Воспроизводим звук отправки
        playSendSound();
        
        // Оптимистичное обновление - добавляем сообщение сразу
        const newMessage = {
          id: Date.now(), // Временный ID
          sender_id: roomData?.current_user_id,
          sender_full_name: roomData?.current_user_name,
          content: messageText,
          created_at: new Date().toISOString(),
          sender_avatar: roomData?.current_user_avatar,
          sender_initials: roomData?.current_user_initials,
          attachments: [],
        };
        
        setMessages(prev => [...prev, newMessage]);
      } else {
        // Если WebSocket не подключен, пытаемся отправить через REST API
        try {
          const response = await sendChatMessage(roomId, messageText);
          
          if (response.success) {
            const newMessage = {
              id: response.message_id,
              sender_id: roomData?.current_user_id,
              sender_full_name: roomData?.current_user_name,
              content: response.message,
              created_at: response.timestamp,
              sender_avatar: roomData?.current_user_avatar,
              sender_initials: roomData?.current_user_initials,
              attachments: [],
            };
            
            setMessages(prev => [...prev, newMessage]);
          }
        } catch (err) {
          alert('Ошибка отправки сообщения: ' + err.message);
        }
      }
    }
  }, [roomId, roomData, sendMessage, sendMessageWithAttachments]);

  const handleToggleNotifications = useCallback(async () => {
    try {
      const response = await toggleRoomNotifications(roomId);
      setNotificationsEnabled(response.notifications_enabled);
    } catch (err) {
      alert('Ошибка переключения уведомлений: ' + err.message);
    }
  }, [roomId]);

  const handleShowParticipants = useCallback(() => {
    setShowParticipantsModal(true);
  }, []);

  const handleCloseParticipants = useCallback(() => {
    setShowParticipantsModal(false);
  }, []);

  if (loading) {
    return (
      <div className="chat-room-page">
        <div className="chat-room-page__loading">
          <p>Загрузка чата...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="chat-room-page">
        <div className="chat-room-page__error" role="alert">
          <p>{error}</p>
          <button onClick={() => navigate('/messenger/chat/rooms')} className="chat-room-page__back-btn">
            Вернуться к списку комнат
          </button>
        </div>
      </div>
    );
  }

  if (!roomData) {
    return null;
  }

  return (
    <div className="chat-room-page">
      <ChatHeader
        room={roomData.room}
        notificationsEnabled={notificationsEnabled}
        isCreator={roomData.is_creator}
        onToggleNotifications={handleToggleNotifications}
        onShowParticipants={handleShowParticipants}
        onBackToList={() => navigate('/messenger/chat/rooms')}
      />
      
      <ConnectionStatus
        status={connectionStatus}
        onReconnect={reconnect}
      />
      
      <MessageList
        messages={messages}
        currentUserId={roomData.current_user_id}
        messagesEndRef={messagesEndRef}
      />
      
      <ChatInput
        onSendMessage={handleSendMessage}
        isUploading={isUploading}
        uploadProgress={uploadProgress}
        isConnected={connectionStatus === 'connected'}
      />
      
      {showParticipantsModal && (
        <ParticipantsModal
          roomId={roomId}
          isCreator={roomData.is_creator}
          onClose={handleCloseParticipants}
        />
      )}
    </div>
  );
};

export default ChatRoomPage;
