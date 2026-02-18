import ProductCard from '../ProductCard/ProductCard';
import './ProductsGrid.css';

const ProductsGrid = ({ products, onProductClick }) => {
  return (
    <div className="products-grid" role="list">
      {products.map((product) => (
        <div key={product.id} className="products-grid__item" role="listitem">
          <ProductCard product={product} onClick={onProductClick} />
        </div>
      ))}
    </div>
  );
};

export default ProductsGrid;
