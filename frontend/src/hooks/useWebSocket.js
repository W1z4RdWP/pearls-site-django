import { useEffect, useRef, useState, useCallback } from 'react';

/**
 * Хук для работы с WebSocket соединением
 * @param {string} roomId - ID комнаты чата
 * @param {number} currentUserId - ID текущего пользователя
 * @param {Function} onMessage - Callback для обработки новых сообщений
 * @param {Function} onError - Callback для обработки ошибок
 * @returns {Object} { socket, connectionStatus, sendMessage, reconnect }
 */
export const useWebSocket = (roomId, currentUserId, onMessage, onError) => {
  const [connectionStatus, setConnectionStatus] = useState('disconnected'); // 'connecting', 'connected', 'disconnected'
  const socketRef = useRef(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 5;
  const reconnectTimeoutRef = useRef(null);
  const isManualCloseRef = useRef(false);

  const connect = useCallback(() => {
    if (!roomId) return;

    // Закрываем существующее соединение если есть
    if (socketRef.current) {
      socketRef.current.close();
    }

    setConnectionStatus('connecting');

    // Определяем WebSocket URL
    // В dev режиме Vite проксирует /ws на порт 8006
    // В production нужно использовать правильный хост и порт
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    
    // Проверяем, находимся ли мы в dev режиме (порт 3000 - это Vite)
    const isDev = window.location.port === '3000' || import.meta.env?.DEV;
    
    let wsUrl;
    if (isDev) {
      // В dev режиме сначала пробуем прокси Vite
      // Если прокси не работает, можно использовать прямой порт 8006
      // Для этого нужно раскомментировать строку ниже и закомментировать текущую
      // wsUrl = `${protocol}//${window.location.hostname}:8006/ws/chat/${roomId}/`;
      wsUrl = `${protocol}//${window.location.host}/ws/chat/${roomId}/`;
    } else {
      // В production используем тот же хост, но порт 8006
      const host = window.location.hostname;
      wsUrl = `${protocol}//${host}:8006/ws/chat/${roomId}/`;
    }

    console.log('Connecting to WebSocket:', wsUrl);
    console.log('Is dev mode:', isDev);
    console.log('Window location:', window.location.href);
    console.log('WebSocket server should be running on port 8006');

    try {
      const socket = new WebSocket(wsUrl);
      socketRef.current = socket;

      socket.onopen = () => {
        console.log('WebSocket connected');
        setConnectionStatus('connected');
        reconnectAttemptsRef.current = 0;
      };

      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          if (data.type === 'connection_established') {
            setConnectionStatus('connected');
          } else if (data.type === 'chat_message') {
            // Обрабатываем только сообщения от других пользователей
            if (data.sender_id !== currentUserId && onMessage) {
              onMessage({
                id: Date.now(), // Временный ID, так как сервер не возвращает ID для новых сообщений
                sender_id: data.sender_id,
                sender_full_name: data.sender_full_name,
                content: data.message,
                created_at: data.timestamp,
                sender_avatar: data.sender_avatar || '',
                sender_initials: data.sender_initials || '',
                attachments: [],
              });
            }
          } else if (data.type === 'chat_message_with_attachments') {
            // Обрабатываем только сообщения от других пользователей
            if (data.sender_id !== currentUserId && onMessage) {
              onMessage({
                id: data.message_id || Date.now(),
                sender_id: data.sender_id,
                sender_full_name: data.sender_full_name,
                content: data.message || '',
                created_at: data.timestamp || new Date().toISOString(),
                sender_avatar: data.sender_avatar || '',
                sender_initials: data.sender_initials || '',
                attachments: data.attachments || [],
              });
            }
          } else if (data.type === 'error') {
            if (onError) {
              onError(new Error(data.message || 'Ошибка WebSocket'));
            }
          }
        } catch (err) {
          console.error('Ошибка парсинга WebSocket сообщения:', err);
          if (onError) {
            onError(err);
          }
        }
      };

      socket.onclose = (event) => {
        console.log('WebSocket closed', event.code, event.reason);
        setConnectionStatus('disconnected');

        // Переподключаемся только если закрытие не было ручным
        if (!isManualCloseRef.current && reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current++;
          const delay = Math.min(2000 * reconnectAttemptsRef.current, 10000); // Максимум 10 секунд
          console.log(`Reconnecting in ${delay}ms (attempt ${reconnectAttemptsRef.current}/${maxReconnectAttempts})`);

          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, delay);
        } else if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
          console.error('Max reconnection attempts reached');
          if (onError) {
            onError(new Error('Не удалось подключиться к чату. Обновите страницу.'));
          }
        }
      };

      socket.onerror = (error) => {
        console.error('WebSocket error:', error);
        console.error('WebSocket URL was:', wsUrl);
        console.error('WebSocket readyState:', socket.readyState);
        setConnectionStatus('disconnected');
        if (onError) {
          onError(new Error('Ошибка подключения к чату. Проверьте, что WebSocket сервер запущен на порту 8006.'));
        }
      };
    } catch (err) {
      console.error('Ошибка создания WebSocket:', err);
      setConnectionStatus('disconnected');
      if (onError) {
        onError(err);
      }
    }
  }, [roomId, currentUserId, onMessage, onError]);

  const sendMessage = useCallback((message) => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({ message }));
      return true;
    }
    return false;
  }, []);

  const sendMessageWithAttachments = useCallback((messageId, message, attachments) => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({
        type: 'message_with_attachments',
        message_id: messageId,
        message: message,
        attachments: attachments,
      }));
      return true;
    }
    return false;
  }, []);

  const disconnect = useCallback(() => {
    isManualCloseRef.current = true;
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (socketRef.current) {
      socketRef.current.close();
      socketRef.current = null;
    }
    setConnectionStatus('disconnected');
  }, []);

  const reconnect = useCallback(() => {
    isManualCloseRef.current = false;
    reconnectAttemptsRef.current = 0;
    connect();
  }, [connect]);

  useEffect(() => {
    if (roomId && currentUserId) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [roomId, currentUserId, connect, disconnect]);

  return {
    connectionStatus,
    sendMessage,
    sendMessageWithAttachments,
    reconnect,
    disconnect,
  };
};
