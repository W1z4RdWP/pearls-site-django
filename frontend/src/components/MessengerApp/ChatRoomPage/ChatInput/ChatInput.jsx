import { useState, useRef, useCallback } from 'react';
import './ChatInput.css';

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10 МБ

const ChatInput = ({ onSendMessage, isUploading, uploadProgress, isConnected = true }) => {
  const [message, setMessage] = useState('');
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef(null);
  const textareaRef = useRef(null);

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Б';
    const k = 1024;
    const sizes = ['Б', 'КБ', 'МБ', 'ГБ'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
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

  const isImageFile = (file) => {
    return file.type.startsWith('image/');
  };

  const handleFileSelect = useCallback((files) => {
    const fileArray = Array.from(files);
    const validFiles = [];
    
    fileArray.forEach(file => {
      if (file.size > MAX_FILE_SIZE) {
        alert(`Файл "${file.name}" превышает максимальный размер 10 МБ`);
        return;
      }
      // Избегаем дубликатов
      if (!selectedFiles.some(f => f.name === file.name && f.size === file.size)) {
        validFiles.push(file);
      }
    });
    
    if (validFiles.length > 0) {
      setSelectedFiles(prev => [...prev, ...validFiles]);
    }
  }, [selectedFiles]);

  const handleFileInputChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFileSelect(e.target.files);
    }
    // Сбрасываем значение input для возможности повторного выбора того же файла
    e.target.value = '';
  };

  const removeFile = (index) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const clearAllFiles = () => {
    setSelectedFiles([]);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (!message.trim() && selectedFiles.length === 0) {
      return;
    }
    
    onSendMessage(message.trim(), selectedFiles);
    setMessage('');
    setSelectedFiles([]);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
    // Сбрасываем высоту textarea
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const autoResizeTextarea = () => {
    if (!textareaRef.current) return;
    
    const maxRows = 10;
    textareaRef.current.style.height = 'auto';
    
    const styles = getComputedStyle(textareaRef.current);
    const lineHeight = parseFloat(styles.lineHeight) || 20;
    const paddingTop = parseFloat(styles.paddingTop) || 10;
    const paddingBottom = parseFloat(styles.paddingBottom) || 10;
    const borderTop = parseFloat(styles.borderTopWidth) || 1;
    const borderBottom = parseFloat(styles.borderBottomWidth) || 1;
    
    const maxHeight = (lineHeight * maxRows) + paddingTop + paddingBottom + borderTop + borderBottom;
    const scrollHeight = textareaRef.current.scrollHeight;
    
    if (scrollHeight <= maxHeight) {
      textareaRef.current.style.height = scrollHeight + 'px';
      textareaRef.current.style.overflowY = 'hidden';
    } else {
      textareaRef.current.style.height = maxHeight + 'px';
      textareaRef.current.style.overflowY = 'auto';
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelect(e.dataTransfer.files);
    }
  };

  return (
    <div 
      className={`chat-input-container ${isDragging ? 'dragging' : ''}`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      {selectedFiles.length > 0 && (
        <div className="file-preview-container show">
          <div className="file-preview-header">
            <h4>Выбранные файлы ({selectedFiles.length})</h4>
            <button type="button" className="file-preview-clear" onClick={clearAllFiles}>
              Очистить всё
            </button>
          </div>
          <div className="file-preview-list">
            {selectedFiles.map((file, index) => (
              <div key={index} className="file-preview-item">
                {isImageFile(file) ? (
                  <img src={URL.createObjectURL(file)} alt={file.name} />
                ) : (
                  <div className="file-icon">{getFileIcon(file.name)}</div>
                )}
                <div className="file-preview-info">
                  <div className="file-preview-name" title={file.name}>{file.name}</div>
                  <div className="file-preview-size">{formatFileSize(file.size)}</div>
                </div>
                <button
                  type="button"
                  className="file-preview-remove"
                  onClick={() => removeFile(index)}
                  title="Удалить"
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {isUploading && (
        <div className="upload-progress show">
          <div className="upload-progress-bar">
            <div className="upload-progress-fill" style={{ width: `${uploadProgress}%` }}></div>
          </div>
          <div className="upload-progress-text">Загрузка файлов: {uploadProgress}%</div>
        </div>
      )}
      
      <form className="chat-input-form" onSubmit={handleSubmit}>
        <div className="chat-input-wrapper">
          <input
            type="file"
            ref={fileInputRef}
            id="file-input"
            multiple
            accept="image/*,video/*,.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.rtf,.odt,.zip,.rar"
            style={{ display: 'none' }}
            onChange={handleFileInputChange}
          />
          <button
            type="button"
            className={`attachment-btn ${selectedFiles.length > 0 ? 'has-files' : ''}`}
            onClick={() => fileInputRef.current?.click()}
            title="Прикрепить файл"
            aria-label="Прикрепить файл"
          >
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M18.375 12.739l-7.693 7.693a4.5 4.5 0 01-6.364-6.364l10.94-10.94A3 3 0 1119.5 7.372L8.552 18.32m.009-.01l-.01.01m5.699-9.941l-7.81 7.81a1.5 1.5 0 002.112 2.13" />
            </svg>
          </button>
          <textarea
            ref={textareaRef}
            className="chat-input"
            rows="1"
            placeholder="Введите сообщение..."
            value={message}
            onChange={(e) => {
              setMessage(e.target.value);
              autoResizeTextarea();
            }}
            onKeyDown={handleKeyDown}
            onPaste={() => setTimeout(autoResizeTextarea, 0)}
            disabled={isUploading}
          />
        </div>
        <button
          type="submit"
          className="chat-send-btn"
          title={!isConnected ? 'Нет подключения к чату' : 'Отправить'}
          disabled={isUploading || !isConnected || (!message.trim() && selectedFiles.length === 0)}
          aria-label="Отправить сообщение"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="none" viewBox="0 0 24 24">
            <path fill="currentColor" fillRule="evenodd" d="M21.4716 4.41683C21.6818 4.58678 21.7843 4.85669 21.7398 5.12331L19.2398 20.1233C19.1977 20.3759 19.0296 20.5896 18.794 20.69C18.5584 20.7904 18.2879 20.7636 18.0765 20.619L12.3413 16.6949L9.53266 19.528C9.31867 19.7439 8.99558 19.8092 8.71452 19.6935C8.43347 19.5778 8.25003 19.3039 8.25003 19V14.1505L1.89397 13.2425C1.55713 13.1944 1.29489 12.9255 1.25516 12.5876C1.21543 12.2497 1.40817 11.9273 1.72466 11.8024L20.7247 4.30239C20.9761 4.20315 21.2614 4.24687 21.4716 4.41683ZM9.75003 14.9219L11.0828 15.8338L9.75003 17.1782V14.9219ZM12.6832 15.1113C12.6756 15.1059 12.6679 15.1006 12.6601 15.0955L10.3126 13.4893L19.9642 6.6528L17.9535 18.7173L12.6832 15.1113ZM15.498 7.97817L4.90916 12.158L8.81033 12.7153L15.498 7.97817Z" clipRule="evenodd"></path>
          </svg>
        </button>
      </form>
    </div>
  );
};

export default ChatInput;
