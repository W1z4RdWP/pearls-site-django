import { useState, useRef, useEffect } from 'react';
import { updateProfile } from '../../../../api/api';
import './ProfileEditForm.css';

// Преобразует дату из формата DD.MM.YYYY в YYYY-MM-DD для input type="date"
const convertDateForInput = (dateString) => {
  if (!dateString) return '';
  // Формат из API: DD.MM.YYYY
  const parts = dateString.split('.');
  if (parts.length === 3) {
    return `${parts[2]}-${parts[1]}-${parts[0]}`;
  }
  return dateString;
};

const ProfileEditForm = ({ user, profile, onSuccess, onCancel }) => {
  const [formData, setFormData] = useState({
    first_name: user?.first_name || '',
    last_name: user?.last_name || '',
    middle_name: profile?.middle_name || '',
    date_of_birth: convertDateForInput(profile?.date_of_birth),
    bio: profile?.bio || '',
  });
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(profile?.avatar_url || null);
  const [cameraPreview, setCameraPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const imageInputRef = useRef(null);
  const cameraInputRef = useRef(null);

  // Обновляем состояние формы при изменении пропсов
  useEffect(() => {
    setFormData({
      first_name: user?.first_name || '',
      last_name: user?.last_name || '',
      middle_name: profile?.middle_name || '',
      date_of_birth: convertDateForInput(profile?.date_of_birth),
      bio: profile?.bio || '',
    });
    if (profile?.avatar_url) {
      setImagePreview(profile.avatar_url);
    }
  }, [user, profile]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setImageFile(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleCameraClick = () => {
    cameraInputRef.current?.click();
  };

  const handleCameraChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setCameraPreview(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleUseCameraPhoto = () => {
    if (cameraInputRef.current?.files[0]) {
      const file = cameraInputRef.current.files[0];
      setImageFile(file);
      setImagePreview(cameraPreview);
      setCameraPreview(null);
      cameraInputRef.current.value = '';
    }
  };

  const handleRetakePhoto = () => {
    setCameraPreview(null);
    cameraInputRef.current.value = '';
    cameraInputRef.current?.click();
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const formDataToSend = new FormData();
      formDataToSend.append('first_name', formData.first_name);
      formDataToSend.append('last_name', formData.last_name);
      formDataToSend.append('middle_name', formData.middle_name || '');
      if (formData.date_of_birth) {
        formDataToSend.append('date_of_birth', formData.date_of_birth);
      } else {
        // Отправляем пустую строку для очистки даты
        formDataToSend.append('date_of_birth', '');
      }
      formDataToSend.append('bio', formData.bio || '');
      
      if (imageFile) {
        formDataToSend.append('image', imageFile);
      }

      const updatedData = await updateProfile(formDataToSend);
      onSuccess(updatedData);
    } catch (err) {
      setError(err.message || 'Ошибка при обновлении профиля');
      console.error('Error updating profile:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="profile-edit-form">
      <form onSubmit={handleSubmit} encType="multipart/form-data" autoComplete='off'>
        <fieldset className="profile-edit-form__fieldset">
          <legend className="profile-edit-form__legend">Информация профиля</legend>
          
          <div className="profile-edit-form__group">
            <label htmlFor="id_first_name" className="profile-edit-form__label">
              Имя <span className="profile-edit-form__required">*</span>
            </label>
            <input
              type="text"
              id="id_first_name"
              name="first_name"
              value={formData.first_name}
              onChange={handleChange}
              className="profile-edit-form__input"
              required
            />
          </div>

          <div className="profile-edit-form__group">
            <label htmlFor="id_last_name" className="profile-edit-form__label">
              Фамилия <span className="profile-edit-form__required">*</span>
            </label>
            <input
              type="text"
              id="id_last_name"
              name="last_name"
              value={formData.last_name}
              onChange={handleChange}
              className="profile-edit-form__input"
              required
            />
          </div>

          <div className="profile-edit-form__group">
            <label htmlFor="id_middle_name" className="profile-edit-form__label">
              Отчество
            </label>
            <input
              type="text"
              id="id_middle_name"
              name="middle_name"
              value={formData.middle_name}
              onChange={handleChange}
              className="profile-edit-form__input"
            />
          </div>

          <div className="profile-edit-form__group">
            <label htmlFor="id_image" className="profile-edit-form__label">
              Аватар
            </label>
            <div className="profile-edit-form__avatar-container">
              <input
                type="file"
                id="id_image"
                name="image"
                accept="image/*"
                onChange={handleImageChange}
                className="profile-edit-form__file-input"
                ref={imageInputRef}
              />
              <div className="profile-edit-form__avatar-controls">
                <button
                  type="button"
                  className="profile-edit-form__btn profile-edit-form__btn--secondary"
                  onClick={handleCameraClick}
                >
                  <i className="fa fa-camera" aria-hidden="true" /> Сделать фото
                </button>
                <input
                  type="file"
                  id="camera-input"
                  accept="image/*"
                  capture="user"
                  style={{ display: 'none' }}
                  onChange={handleCameraChange}
                  ref={cameraInputRef}
                />
              </div>

              {cameraPreview && (
                <div className="profile-edit-form__camera-preview">
                  <img
                    src={cameraPreview}
                    alt="Превью с камеры"
                    className="profile-edit-form__preview-img"
                  />
                  <div className="profile-edit-form__preview-controls">
                    <button
                      type="button"
                      className="profile-edit-form__btn profile-edit-form__btn--success"
                      onClick={handleUseCameraPhoto}
                    >
                      <i className="fa fa-check" aria-hidden="true" /> Использовать
                    </button>
                    <button
                      type="button"
                      className="profile-edit-form__btn profile-edit-form__btn--secondary"
                      onClick={handleRetakePhoto}
                    >
                      <i className="fa fa-camera" aria-hidden="true" /> Переснять
                    </button>
                  </div>
                </div>
              )}

              {imagePreview && !cameraPreview && (
                <div className="profile-edit-form__image-preview">
                  <img
                    src={imagePreview}
                    alt="Превью аватара"
                    className="profile-edit-form__preview-img"
                  />
                </div>
              )}
            </div>
          </div>

          <div className="profile-edit-form__group">
            <label htmlFor="id_date_of_birth" className="profile-edit-form__label">
              Дата рождения
            </label>
            <input
              type="date"
              id="id_date_of_birth"
              name="date_of_birth"
              value={formData.date_of_birth}
              onChange={handleChange}
              className="profile-edit-form__input"
            />
          </div>

          <div className="profile-edit-form__group">
            <label htmlFor="id_bio" className="profile-edit-form__label">
              О себе
            </label>
            <textarea
              id="id_bio"
              name="bio"
              value={formData.bio}
              onChange={handleChange}
              className="profile-edit-form__textarea"
              rows="4"
            />
          </div>
        </fieldset>

        {error && (
          <div className="profile-edit-form__error">
            {error}
          </div>
        )}

        <div className="profile-edit-form__actions">
          <button
            type="submit"
            className="profile-edit-form__btn profile-edit-form__btn--primary"
            disabled={loading}
          >
            {loading ? 'Обновление...' : 'Обновить'}
          </button>
          <button
            type="button"
            className="profile-edit-form__btn profile-edit-form__btn--secondary"
            onClick={onCancel}
            disabled={loading}
          >
            Отмена
          </button>
          <a
            href="/users/password_change/"
            className="profile-edit-form__btn profile-edit-form__btn--link"
          >
            <i className="fa fa-key" aria-hidden="true" /> Сменить пароль
          </a>
        </div>
      </form>
    </div>
  );
};

export default ProfileEditForm;
