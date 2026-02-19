import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { createUserStep1 } from '../../../api/user_management_api';
import './UserCreateStep1Page.css';

const UserCreateStep1Page = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    email: '',
    password1: '',
    password2: '',
  });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [submitError, setSubmitError] = useState(null);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
    // Очищаем ошибку для этого поля при изменении
    if (errors[name]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }
    setSubmitError(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setErrors({});
    setSubmitError(null);

    try {
      const result = await createUserStep1(
        formData.email,
        formData.password1,
        formData.password2
      );

      if (result.success) {
        // Переходим на шаг 2
        navigate('/user_management/users/add/step2');
      } else {
        setErrors(result.errors || {});
        setSubmitError('Ошибка при создании пользователя');
      }
    } catch (err) {
      setSubmitError(err.message || 'Ошибка при создании пользователя');
    } finally {
      setLoading(false);
    }
  };

  const formatErrors = (fieldErrors) => {
    if (Array.isArray(fieldErrors)) {
      return fieldErrors.join(', ');
    }
    return String(fieldErrors);
  };

  return (
    <main className="user-create-step1-page">
      <div className="user-form-wrapper">
        <div className="user-form-header">
          <Link to="/user_management/users" className="back-link">
            &larr; Назад
          </Link>
          <h1 className="form-title">Новый пользователь — шаг 1</h1>
        </div>

        <form onSubmit={handleSubmit} className="user-form">
          <div className="form-section">
            <h2 className="section-title">Основные данные</h2>

            <label htmlFor="id_email">Email</label>
            <input
              type="email"
              id="id_email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              required
              autoComplete="email"
            />
            <div className="um-help-text">
              Email будет использоваться как логин для входа
            </div>
            {errors.email && (
              <div className="um-user-warning">{formatErrors(errors.email)}</div>
            )}

            <label htmlFor="id_password1">Пароль</label>
            <input
              type="password"
              id="id_password1"
              name="password1"
              value={formData.password1}
              onChange={handleChange}
              required
              autoComplete="new-password"
            />
            <div className="um-help-text">
              Минимум 8 символов, не слишком распространённый пароль
            </div>
            {errors.password1 && (
              <div className="um-user-warning">{formatErrors(errors.password1)}</div>
            )}

            <label htmlFor="id_password2">Подтверждение пароля</label>
            <input
              type="password"
              id="id_password2"
              name="password2"
              value={formData.password2}
              onChange={handleChange}
              required
              autoComplete="new-password"
            />
            {errors.password2 && (
              <div className="um-user-warning">{formatErrors(errors.password2)}</div>
            )}

            {submitError && (
              <div className="um-user-warning">{submitError}</div>
            )}

            {errors.__all__ && (
              <div className="um-user-warning">{formatErrors(errors.__all__)}</div>
            )}
          </div>

          <div className="form-actions">
            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading}
            >
              {loading ? 'Создание...' : 'Продолжить'}
            </button>
            <Link to="/user_management/users" className="btn btn-secondary">
              Отмена
            </Link>
          </div>
        </form>
      </div>
    </main>
  );
};

export default UserCreateStep1Page;
