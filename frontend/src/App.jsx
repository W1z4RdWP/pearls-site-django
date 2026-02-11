import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout/Layout';
import HomePage from './components/HomePage/HomePage';
import './App.css';
import LoginPage from './components/UsersApp/LoginPage/LoginPage';
import LogoutPage from './components/UsersApp/LogoutPage/LogoutPage';
import AboutPage from './components/AboutPage/AboutPage';
import ShopPage from './components/ShopPage/ShopPage';
import ProfilePage from './components/UsersApp/UserProfilePage/ProfilePage';

const App = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<HomePage />} />
          <Route path='/users/login' element={<LoginPage />}/>
          <Route path='/users/logout' element={<LogoutPage />}/>
          <Route path='/about' element={<AboutPage />}/>
          <Route path='/shop/catalog' element={<ShopPage />}/>
          <Route path='/users/profile' element={<ProfilePage />} /> 

          {/* Добавляйте новые маршруты здесь */}
        </Route>
      </Routes>
    </BrowserRouter>
  );
};

export default App;
