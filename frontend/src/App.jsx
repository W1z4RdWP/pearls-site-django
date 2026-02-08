import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout/Layout';
import HomePage from './components/HomePage/HomePage';
import './App.css';
import LoginPage from './components/UsersApp/LoginPage/LoginPage';
import LogoutPage from './components/UsersApp/LogoutPage/LogoutPage';

const App = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<HomePage />} />
          <Route path='/users/login' element={<LoginPage />}/>
          <Route path='/users/logout' element={<LogoutPage />}/>
          {/* Добавляйте новые маршруты здесь */}
        </Route>
      </Routes>
    </BrowserRouter>
  );
};

export default App;
