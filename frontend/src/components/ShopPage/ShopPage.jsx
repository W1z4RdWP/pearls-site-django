import { useState, useEffect, useCallback } from 'react';
import { useOutletContext } from 'react-router-dom';
import {
  fetchShopProducts,
  fetchProductDetails,
  orderProduct,
  fetchOrdersCount,
} from '../../api/api';
import ShopHeader from './ShopHeader/ShopHeader';
import ProductsGrid from './ProductsGrid/ProductsGrid';
import NoProducts from './NoProducts/NoProducts';
import ProductModal from './ProductModal/ProductModal';
import OrderSuccessModal from './OrderSuccessModal/OrderSuccessModal';
import './ShopPage.css';

const ORDER_SUCCESS_MESSAGE = (points) =>
  `Списано ${points} баллов. HR проверяет соответствие политике в течение 2 рабочих дней, затем Вы сможете получить свой товар или Вам вернутся баллы обратно.`;

const ShopPage = () => {
  const { user, isAuthenticated, refreshLayout } = useOutletContext();
  const [products, setProducts] = useState([]);
  const [productsLoading, setProductsLoading] = useState(true);
  const [productsError, setProductsError] = useState(null);
  const [ordersCount, setOrdersCount] = useState(0);
  const [modalProductId, setModalProductId] = useState(null);
  const [modalProduct, setModalProduct] = useState(null);
  const [modalProductLoading, setModalProductLoading] = useState(false);
  const [isOrdering, setIsOrdering] = useState(false);
  const [successModalOpen, setSuccessModalOpen] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');

  const loadProducts = useCallback(async () => {
    setProductsLoading(true);
    setProductsError(null);
    try {
      const data = await fetchShopProducts();
      setProducts(data.products || []);
    } catch (err) {
      setProductsError(err.message || 'Ошибка загрузки товаров');
      setProducts([]);
    } finally {
      setProductsLoading(false);
    }
  }, []);

  const loadOrdersCount = useCallback(async () => {
    if (!isAuthenticated) return;
    try {
      const data = await fetchOrdersCount();
      setOrdersCount(data.count ?? 0);
    } catch {
      setOrdersCount(0);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    loadProducts();
  }, [loadProducts]);

  useEffect(() => {
    loadOrdersCount();
  }, [loadOrdersCount]);

  useEffect(() => {
    if (!modalProductId) {
      setModalProduct(null);
      return;
    }
    let cancelled = false;
    setModalProductLoading(true);
    setModalProduct(null);
    fetchProductDetails(modalProductId)
      .then((data) => {
        if (!cancelled && data.product) setModalProduct(data.product);
      })
      .catch(() => {
        if (!cancelled) setModalProduct(null);
      })
      .finally(() => {
        if (!cancelled) setModalProductLoading(false);
      });
    return () => { cancelled = true; };
  }, [modalProductId]);

  const handleProductClick = useCallback((productId) => {
    setModalProductId(productId);
  }, []);

  const handleCloseProductModal = useCallback(() => {
    setModalProductId(null);
  }, []);

  const handleOrder = useCallback(async () => {
    if (!modalProductId || !modalProduct) return;
    setIsOrdering(true);
    try {
      const res = await orderProduct(modalProductId);
      setSuccessMessage(ORDER_SUCCESS_MESSAGE(res.points_spent ?? modalProduct.points_price));
      setSuccessModalOpen(true);
      setModalProductId(null);
      refreshLayout?.();
      loadOrdersCount();
    } catch (err) {
      alert(err.message || 'Произошла ошибка при оформлении заказа.');
    } finally {
      setIsOrdering(false);
    }
  }, [modalProductId, modalProduct, refreshLayout, loadOrdersCount]);

  const handleCloseSuccessModal = useCallback(() => {
    setSuccessModalOpen(false);
  }, []);

  return (
    <div className="shop-page">
      <div className="shop-page__container">
        <ShopHeader
          isAuthenticated={isAuthenticated}
          isStaff={user?.is_staff}
          isSuperuser={user?.is_superuser}
          ordersCount={ordersCount}
        />

        {productsLoading && (
          <p className="shop-page__loading" aria-live="polite">Загрузка товаров…</p>
        )}
        {productsError && (
          <p className="shop-page__error" role="alert">{productsError}</p>
        )}
        {!productsLoading && !productsError && products.length > 0 && (
          <ProductsGrid products={products} onProductClick={handleProductClick} />
        )}
        {!productsLoading && !productsError && products.length === 0 && (
          <NoProducts />
        )}
      </div>

      <ProductModal
        isOpen={Boolean(modalProductId)}
        product={modalProduct}
        isLoading={modalProductLoading}
        isOrdering={isOrdering}
        onClose={handleCloseProductModal}
        onOrder={handleOrder}
      />

      <OrderSuccessModal
        isOpen={successModalOpen}
        message={successMessage}
        onClose={handleCloseSuccessModal}
      />
    </div>
  );
};

export default ShopPage;
