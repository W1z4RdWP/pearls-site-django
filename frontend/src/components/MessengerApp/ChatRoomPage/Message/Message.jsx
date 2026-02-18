import './Message.css';

const Message = ({ message, isOwn }) => {
  const formatTime = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString('ru-RU', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getFileIcon = (filename) => {
    const ext = filename.toLowerCase().split('.').pop();
    const icons = {
      pdf: '📕', doc: '📘', docx: '📘',
      xls: '📗', xlsx: '📗',
      ppt: '📙', pptx: '📙',
      txt: '📄', rtf: '📄', odt: '📄',
      zip: '📦', rar: '📦',
      mp4: '🎬', avi: '🎬', mov: '🎬', mkv: '🎬', webm: '🎬',
    };
    return icons[ext] || '📄';
  };

  return (
    <div className={`message ${isOwn ? 'own' : 'other'}`}>
      <div className="message__avatar">
        {message.sender_avatar ? (
          <img src={message.sender_avatar} alt={message.sender_full_name} />
        ) : (
          <div className="message__avatar-initials">
            {message.sender_initials || message.sender_full_name.substring(0, 2).toUpperCase()}
          </div>
        )}
      </div>
      <div className="message__body">
        <div className="message__header">{message.sender_full_name}</div>
        {message.content && (
          <div className="message__content">{message.content}</div>
        )}
        {message.attachments && message.attachments.length > 0 && (
          <div className="message__attachments">
            {message.attachments.map((att) => {
              if (att.is_image) {
                return (
                  <div key={att.id} className="attachment-item image-attachment">
                    <a href={att.file_url} target="_blank" rel="noopener noreferrer">
                      <img src={att.file_url} alt={att.filename} loading="lazy" />
                    </a>
                  </div>
                );
              } else if (att.is_video) {
                return (
                  <div key={att.id} className="attachment-item video-attachment">
                    <video controls preload="metadata">
                      <source src={att.file_url} type="video/mp4" />
                      Ваш браузер не поддерживает видео
                    </video>
                  </div>
                );
              } else {
                return (
                  <div key={att.id} className="attachment-item document-attachment">
                    <a href={att.file_url} target="_blank" rel="noopener noreferrer" download>
                      <span className="doc-icon">{getFileIcon(att.filename)}</span>
                      <div className="doc-info">
                        <div className="doc-name">{att.filename}</div>
                        <div className="doc-size">{att.file_size_display}</div>
                      </div>
                    </a>
                  </div>
                );
              }
            })}
          </div>
        )}
        <div className="message__time">{formatTime(message.created_at)}</div>
      </div>
    </div>
  );
};

export default Message;
