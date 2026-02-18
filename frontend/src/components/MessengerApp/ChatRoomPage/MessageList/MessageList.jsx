import { useEffect } from 'react';
import Message from '../Message/Message';
import DateSeparator from '../DateSeparator/DateSeparator';
import './MessageList.css';

const MessageList = ({ messages, currentUserId, messagesEndRef }) => {
  // Группируем сообщения по датам
  const groupedMessages = [];
  let currentDate = null;
  
  messages.forEach((message) => {
    const messageDate = new Date(message.created_at);
    const dateStr = messageDate.toISOString().split('T')[0]; // YYYY-MM-DD
    
    if (dateStr !== currentDate) {
      currentDate = dateStr;
      groupedMessages.push({
        type: 'date',
        date: dateStr,
        dateObj: messageDate,
      });
    }
    
    groupedMessages.push({
      type: 'message',
      message: message,
    });
  });

  return (
    <div className="chat-messages">
      {groupedMessages.length === 0 ? (
        <div className="chat-messages__empty">
          <p>Пока нет сообщений. Начните общение!</p>
        </div>
      ) : (
        groupedMessages.map((item, index) => {
          if (item.type === 'date') {
            return <DateSeparator key={`date-${item.date}`} date={item.dateObj} />;
          } else {
            return (
              <Message
                key={item.message.id}
                message={item.message}
                isOwn={item.message.sender_id === currentUserId}
              />
            );
          }
        })
      )}
      <div ref={messagesEndRef} />
    </div>
  );
};

export default MessageList;
