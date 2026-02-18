import CreateProductHeader from './CreateProductHeader/CreateProductHeader';
import CreateProductForm from './CreateProductForm/CreateProductForm';
import './CreateProductPage.css';

const CreateProductPage = () => {
  return (
    <div className="create-product-page">
      <div className="create-product-page__container">
        <CreateProductHeader />
        <CreateProductForm />
      </div>
    </div>
  );
};

export default CreateProductPage;
