import { useEffect } from 'react';
import './ProductModal.css';

const ProductModal = ({ isOpen, product, isLoading, isOrdering, onClose, onOrder }) => {
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

  const restrictionsText = product
    ? (product.restrictions_text || product.constraints_display || '')
    : '';

  return (
    <div
      className="product-modal product-modal--backdrop"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="productModalLabel"
    >
      <div
        className="product-modal__dialog"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="product-modal__content">
          <div className="product-modal__header">
            <h5 className="product-modal__title" id="productModalLabel">
              Информация о товаре
            </h5>
            <button
              type="button"
              className="product-modal__close"
              onClick={onClose}
              aria-label="Закрыть"
            >
              <span aria-hidden>×</span>
            </button>
          </div>
          <div className="product-modal__body">
            {isLoading ? (
              <p className="product-modal__loading">Загрузка…</p>
            ) : product ? (
              <>
                <img
                  src={product.image_url}
                  alt={product.name}
                  className="product-modal__image"
                />
                <h4 className="product-modal__product-title">{product.name}</h4>
                <div className="product-modal__price">
                  {product.points_price} <span>баллов</span>
                </div>
                {product.description && (
                  <div className="product-modal__description">{product.description}</div>
                )}
                {restrictionsText && (
                  <div className="product-modal__restrictions">
                    <h6><i className="fas fa-info-circle" aria-hidden /> Ограничения:</h6>
                    <p>{restrictionsText}</p>
                  </div>
                )}
              </>
            ) : null}
          </div>
          <div className="product-modal__footer">
            <button type="button" className="product-modal__btn product-modal__btn--secondary" onClick={onClose}>
              Закрыть
            </button>
            <button
              type="button"
              className="product-modal__btn product-modal__btn--order"
              onClick={() => product && onOrder(product.id)}
              disabled={!product || isOrdering}
            >
              {isOrdering ? (
                <>
                  <i className="fas fa-spinner fa-spin" aria-hidden /> Оформление...
                </>
              ) : (
                <>
                  <i className="fas fa-shopping-cart" aria-hidden /> Заказать
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProductModal;
