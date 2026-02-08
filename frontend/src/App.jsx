import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout/Layout';
import HomePage from './components/HomePage/HomePage';
import './App.css';
import LoginPage from './components/LoginPage/LoginPage';

const App = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<HomePage />} />
          <Route path='/users/login' element={<LoginPage />}/>
          {/* Добавляйте новые маршруты здесь */}
        </Route>
      </Routes>
    </BrowserRouter>
  );
};

export default App;
