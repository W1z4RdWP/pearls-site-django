import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout/Layout';
import HomePage from './components/HomePage/HomePage';
import './App.css';
import LoginPage from './components/UsersApp/LoginPage/LoginPage';
import LogoutPage from './components/UsersApp/LogoutPage/LogoutPage';
import AboutPage from './components/AboutPage/AboutPage';
import ShopPage from './components/ShopApp/ShopPage';
import OrderHistoryPage from './components/ShopApp/OrderHistoryPage/OrderHistoryPage';
import UsersWithOrdersPage from './components/ShopApp/UsersWithOrdersPage/UsersWithOrdersPage';
import UserOrdersAdminPage from './components/ShopApp/UserOrdersAdminPage/UserOrdersAdminPage';
import CreateProductPage from './components/ShopApp/CreateProductPage/CreateProductPage';
import ProfilePage from './components/UsersApp/UserProfilePage/ProfilePage';
import TransactionsPage from './components/UsersApp/TransactionsPage/TransactionsPage';
import DashboardPage from './components/DashboardPage/DashboardPage';
import ChangeLogPage from './components/ChangeLogPage/ChangeLogPage';
import MessengerPage from './components/MessengerApp/MessengerPage/MessengerPage';

const App = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<HomePage />} />
          <Route path='/about' element={<AboutPage />}/>
          <Route path='/changelog' element={<ChangeLogPage />}/>
          <Route path='/builder' element={<DashboardPage />}/>
          <Route path='/messenger/chat/rooms' element={<MessengerPage />}/>



          {/* shop */}
          <Route path='/shop/catalog' element={<ShopPage />}/>
          <Route path='/shop/history' element={<OrderHistoryPage />} />
          <Route path='/shop/admin/users' element={<UsersWithOrdersPage />} />
          <Route path='/shop/admin/user/:userId/orders' element={<UserOrdersAdminPage />} />
          <Route path='/shop/product/create' element={<CreateProductPage />} />

          {/* users */}
          <Route path='/users/login' element={<LoginPage />}/>
          <Route path='/users/logout' element={<LogoutPage />}/>
          <Route path='/users/profile' element={<ProfilePage />} />
          <Route path='/users/profile/transactions' element={<TransactionsPage />} />

          {/* Добавляйте новые маршруты здесь */}
        </Route>
      </Routes>
    </BrowserRouter>
  );
};

export default App;
