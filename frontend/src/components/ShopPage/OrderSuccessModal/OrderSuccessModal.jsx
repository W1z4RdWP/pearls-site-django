import { useEffect } from 'react';
import './OrderSuccessModal.css';

const OrderSuccessModal = ({ isOpen, message, onClose }) => {
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape') onClose();
    };
    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    }
    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = '';
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      className="order-success-modal order-success-modal--backdrop"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="orderSuccessModalLabel"
    >
      <div
        className="order-success-modal__dialog"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="order-success-modal__content">
          <div className="order-success-modal__header">
            <h5 className="order-success-modal__title" id="orderSuccessModalLabel">
              <i className="fas fa-check-circle" aria-hidden /> Заказ оформлен
            </h5>
            <button
              type="button"
              className="order-success-modal__close"
              onClick={onClose}
              aria-label="Закрыть"
            >
              <span aria-hidden>×</span>
            </button>
          </div>
          <div className="order-success-modal__body">
            <p>{message}</p>
          </div>
          <div className="order-success-modal__footer">
            <button type="button" className="order-success-modal__btn" onClick={onClose}>
              Понятно
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OrderSuccessModal;
