import { useState } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import { changeUserPassword } from '../../../api/user_management_api';
import './UserPasswordChangePage.css';

const UserPasswordChangePage = () => {
  const navigate = useNavigate();
  const { userId } = useParams();
  const [formData, setFormData] = useState({
    new_password1: '',
    new_password2: '',
  });
  const [errors, setErrors] = useState({});
  const [submitError, setSubmitError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
    
    // Очищаем ошибки при изменении поля
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
    setSubmitting(true);
    setErrors({});
    setSubmitError(null);

    try {
      const result = await changeUserPassword(
        userId,
        formData.new_password1,
        formData.new_password2
      );

      if (result.success) {
        alert(result.message || 'Пароль успешно изменён');
        navigate(`/user_management/users/${userId}/edit`);
      } else {
        setSubmitError('Ошибка при смене пароля');
      }
    } catch (err) {
      if (err.errors) {
        setErrors(err.errors);
      } else {
        setSubmitError(err.message || 'Ошибка при смене пароля');
      }
    } finally {
      setSubmitting(false);
    }
  };

  const formatErrors = (fieldErrors) => {
    if (Array.isArray(fieldErrors)) {
      return fieldErrors.join(', ');
    }
    return String(fieldErrors);
  };

  return (
    <main className="user-password-change-page">
      <div className="user-form-wrapper">
        <div className="user-form-header">
          <Link 
            to={`/user_management/users/${userId}/edit`} 
            className="back-link"
          >
            &larr; Назад
          </Link>
          <h1 className="form-title">Смена пароля пользователя</h1>
        </div>

        <form onSubmit={handleSubmit} className="user-form">
          <div className="form-section">
            <div className="form-group">
              <label htmlFor="id_new_password1">
                Новый пароль <span className="required">*</span>
              </label>
              <input
                type="password"
                id="id_new_password1"
                name="new_password1"
                value={formData.new_password1}
                onChange={handleChange}
                className="form-control"
                required
                autoComplete="new-password"
              />
              <small className="form-text text-muted">
                Пароль должен содержать минимум 8 символов.
              </small>
              {errors.new_password1 && (
                <div className="um-user-warning">
                  {formatErrors(errors.new_password1)}
                </div>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="id_new_password2">
                Подтверждение пароля <span className="required">*</span>
              </label>
              <input
                type="password"
                id="id_new_password2"
                name="new_password2"
                value={formData.new_password2}
                onChange={handleChange}
                className="form-control"
                required
                autoComplete="new-password"
              />
              {errors.new_password2 && (
                <div className="um-user-warning">
                  {formatErrors(errors.new_password2)}
                </div>
              )}
            </div>

            {submitError && (
              <div className="um-user-warning">{submitError}</div>
            )}

            {errors.__all__ && (
              <div className="um-user-warning">
                {formatErrors(errors.__all__)}
              </div>
            )}
          </div>

          <div className="form-actions">
            <button
              type="submit"
              className="btn btn-primary"
              disabled={submitting}
            >
              {submitting ? 'Сохранение...' : 'Сохранить новый пароль'}
            </button>
            <Link
              to={`/user_management/users/${userId}/edit`}
              className="btn btn-outline-secondary"
            >
              Отмена
            </Link>
          </div>
        </form>
      </div>
    </main>
  );
};

export default UserPasswordChangePage;
