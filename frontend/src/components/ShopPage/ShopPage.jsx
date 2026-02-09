import { useOutletContext } from "react-router-dom";

const ShopPage = () => {
    const { user, isAuthenticated } = useOutletContext();


    return (
        <div className="shop-page">
            <div className="shop-header">
                <div>
                    <h1>Магазин</h1>
                    <p>Потратьте свои баллы DASCOIN на товары и услуги</p>
                </div>
            <div class="d-flex align-items-center gap-2">
                {(user?.isAuthenticated) && (
                    <a href="/shop/history/" class="cart-icon-link" title="История покупок">
                        <i class="fas fa-shopping-cart"></i>
                        <span class="cart-badge" id="cart-badge" style="display: none;">0</span>
                    </a>
                )}
                {(user?.is_staff || user?.is_superuser) && (
                <a href="/shop/product/create/" className="add-product-icon-link" title="Добавить товар">
                    <i className="fas fa-plus"></i>
                </a>
                )}
            </div>
            </div>
        </div>
    )
}

export default ShopPage;