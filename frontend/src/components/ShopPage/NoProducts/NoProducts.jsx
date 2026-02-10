import './NoProducts.css';

const NoProducts = () => {
  return (
    <div className="no-products">
      <i className="fas fa-shopping-bag" aria-hidden />
      <h3 className="no-products__title">Товары пока не добавлены</h3>
      <p className="no-products__text">
        Мы работаем над наполнением магазина. Скоро здесь появятся товары!
      </p>
    </div>
  );
};

export default NoProducts;
