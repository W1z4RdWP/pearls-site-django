import { useState, useEffect } from 'react';
import { useNavigate, useOutletContext } from 'react-router-dom';
import { loginUser } from '../../../api/api';
import './LoginPage.css';

const LoginPage = () => {
  const navigate = useNavigate();
  const { isAuthenticated, refreshLayout } = useOutletContext();

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    document.title = 'Вход в учетную запись';
    return () => {
      document.title = 'Главная';
    };
  }, []);

  // Если уже авторизован — перенаправляем на главную
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/', { replace: true });
    }
  }, [isAuthenticated, navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!username.trim() || !password) {
      setError('Введите логин и пароль');
      return;
    }

    setLoading(true);

    try {
      await loginUser(username.trim(), password);
      // Обновляем данные Layout (user, nav и т.д.)
      await refreshLayout();
      navigate('/', { replace: true });
    } catch (err) {
      setError(err.message || 'Ошибка при входе');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-page__card">
        <h1 className="login-page__title">Вход</h1>

        {error && (
          <div className="login-page__error">{error}</div>
        )}

        <form className="login-page__form" onSubmit={handleSubmit}>
          <label className="login-page__field">
            <span className="login-page__label">Логин</span>
            <input
              className="login-page__input"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Введите логин"
              autoComplete="username"
              disabled={loading}
            />
          </label>
          <label className="login-page__field">
            <span className="login-page__label">Пароль</span>
            <input
              className="login-page__input"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Введите пароль"
              autoComplete="current-password"
              disabled={loading}
            />
          </label>
          <button
            className="login-page__btn"
            type="submit"
            disabled={loading}
          >
            {loading ? 'Вход...' : 'Войти'}
          </button>
        </form>

        <p className="login-page__hint">Нужен аккаунт? Обратитесь к администратору.</p>
      </div>
    </div>
  );
};

export default LoginPage;
