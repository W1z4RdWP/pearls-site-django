import './ProductCard.css';

const ProductCard = ({ product, onClick }) => {
  const restrictionsDisplay = product.restrictions_text
    || product.constraints_display
    || '';

  return (
    <button
      type="button"
      className="product-card"
      onClick={() => onClick(product.id)}
      data-product-id={product.id}
      aria-label={`Товар: ${product.name}, цена ${product.points_price} баллов`}
    >
      <div className="product-card__image-wrapper">
        <img
          src={product.image_url}
          alt={product.name}
          className="product-card__image"
        />
      </div>
      <div className="product-card__body">
        <h5 className="product-card__title">{product.name}</h5>
        <div className="product-card__price">
          {product.points_price} <span>баллов</span>
        </div>
        {restrictionsDisplay && (
          <div className="product-card__restrictions">
            <i className="fas fa-info-circle" aria-hidden />
            <small>{restrictionsDisplay.length > 60 ? `${restrictionsDisplay.slice(0, 60)}…` : restrictionsDisplay}</small>
          </div>
        )}
      </div>
    </button>
  );
};

export default ProductCard;
