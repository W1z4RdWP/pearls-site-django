import './Modal.css';

const Modal = ({ isOpen, onClose, title, children }) => {
  if (!isOpen) return null;

  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div className="gamification-modal-overlay" onClick={handleOverlayClick}>
      <div className="gamification-modal-content">
        <div className="gamification-modal-header">
          <h3>{title}</h3>
          <button className="gamification-modal-close" onClick={onClose}>
            &times;
          </button>
        </div>
        <div className="gamification-modal-body">
          {children}
        </div>
      </div>
    </div>
  );
};

export default Modal;
