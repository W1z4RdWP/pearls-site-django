import { Link } from 'react-router-dom';
import './CreateProductHeader.css';

const CreateProductHeader = () => {
  return (
    <header className="create-product-header">
      <Link
        to="/shop/catalog"
        className="create-product-header__back-link"
        aria-label="Вернуться в магазин"
      >
        <i className="fas fa-arrow-left" aria-hidden />
        <span className="create-product-header__back-text">Вернуться в магазин</span>
      </Link>
      <h1 className="create-product-header__title">
        <i className="fas fa-plus-circle create-product-header__icon" aria-hidden />
        Создание нового товара
      </h1>
    </header>
  );
};

export default CreateProductHeader;
