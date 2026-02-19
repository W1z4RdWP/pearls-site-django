import { useState } from 'react';
import { changePassword } from '../../../../api/users_api';
import './ProfilePasswordChangeForm.css';

const ProfilePasswordChangeForm = ({ onSuccess, onCancel }) => {
  const [formData, setFormData] = useState({
    old_password: '',
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
      const result = await changePassword(
        formData.old_password,
        formData.new_password1,
        formData.new_password2
      );

      if (result.success) {
        if (onSuccess) {
          onSuccess(result.message || 'Пароль успешно изменён');
        } else {
          alert(result.message || 'Пароль успешно изменён');
        }
        // Очищаем форму
        setFormData({
          old_password: '',
          new_password1: '',
          new_password2: '',
        });
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
    <div className="profile-password-change-form">
      <form onSubmit={handleSubmit} encType="multipart/form-data" autoComplete="off">
        <fieldset className="profile-password-change-form__fieldset">
          <legend className="profile-password-change-form__legend">Смена пароля</legend>
          
          <div className="profile-password-change-form__group">
            <label htmlFor="id_old_password" className="profile-password-change-form__label">
              Текущий пароль <span className="profile-password-change-form__required">*</span>
            </label>
            <input
              type="password"
              id="id_old_password"
              name="old_password"
              value={formData.old_password}
              onChange={handleChange}
              className="profile-password-change-form__input"
              required
              autoComplete="current-password"
            />
            {errors.old_password && (
              <div className="profile-password-change-form__error">
                {formatErrors(errors.old_password)}
              </div>
            )}
          </div>

          <div className="profile-password-change-form__group">
            <label htmlFor="id_new_password1" className="profile-password-change-form__label">
              Новый пароль <span className="profile-password-change-form__required">*</span>
            </label>
            <input
              type="password"
              id="id_new_password1"
              name="new_password1"
              value={formData.new_password1}
              onChange={handleChange}
              className="profile-password-change-form__input"
              required
              autoComplete="new-password"
            />
            <small className="profile-password-change-form__help">
              Пароль должен содержать минимум 8 символов.
            </small>
            {errors.new_password1 && (
              <div className="profile-password-change-form__error">
                {formatErrors(errors.new_password1)}
              </div>
            )}
          </div>

          <div className="profile-password-change-form__group">
            <label htmlFor="id_new_password2" className="profile-password-change-form__label">
              Подтверждение пароля <span className="profile-password-change-form__required">*</span>
            </label>
            <input
              type="password"
              id="id_new_password2"
              name="new_password2"
              value={formData.new_password2}
              onChange={handleChange}
              className="profile-password-change-form__input"
              required
              autoComplete="new-password"
            />
            {errors.new_password2 && (
              <div className="profile-password-change-form__error">
                {formatErrors(errors.new_password2)}
              </div>
            )}
          </div>

          {submitError && (
            <div className="profile-password-change-form__error">
              {submitError}
            </div>
          )}

          {errors.__all__ && (
            <div className="profile-password-change-form__error">
              {formatErrors(errors.__all__)}
            </div>
          )}
        </fieldset>

        <div className="profile-password-change-form__actions">
          <button
            type="submit"
            className="profile-password-change-form__btn profile-password-change-form__btn--primary"
            disabled={submitting}
          >
            {submitting ? 'Смена пароля...' : 'Сменить пароль'}
          </button>
          {onCancel && (
            <button
              type="button"
              className="profile-password-change-form__btn profile-password-change-form__btn--secondary"
              onClick={onCancel}
              disabled={submitting}
            >
              Отмена
            </button>
          )}
        </div>
      </form>
    </div>
  );
};

export default ProfilePasswordChangeForm;
