import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { fetchUserCreateStep2Data, createUserStep2 } from '../../../api/user_management_api';
import './UserCreateStep2Page.css';

const UserCreateStep2Page = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [submitError, setSubmitError] = useState(null);
  const [formErrors, setFormErrors] = useState({});
  
  const [roles, setRoles] = useState([]);
  const [groups, setGroups] = useState([]);
  const [user, setUser] = useState(null);
  
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    middle_name: '',
    role: '',
    groups: [],
    date_of_birth: '',
    phone_number: '',
    phone_arbitrary_format: false,
    bio: '',
    image: null,
    is_approved: false,
    is_mentor: false,
  });

  // Загрузка данных для формы
  useEffect(() => {
    const loadData = async () => {
      try {
        const data = await fetchUserCreateStep2Data();
        setRoles(data.roles || []);
        setGroups(data.groups || []);
        setUser(data.user);
        
        // Заполняем форму данными профиля, если они есть
        if (data.profile) {
          setFormData(prev => ({
            ...prev,
            first_name: data.profile.first_name || '',
            last_name: data.profile.last_name || '',
            middle_name: data.profile.middle_name || '',
            role: data.profile.role_id || '',
            groups: data.profile.groups || [],
            date_of_birth: data.profile.date_of_birth || '',
            phone_number: data.profile.phone_number || '',
            phone_arbitrary_format: data.profile.phone_arbitrary_format || false,
            bio: data.profile.bio || '',
            is_approved: data.profile.is_approved || false,
            is_mentor: data.profile.is_mentor || false,
          }));
        }
      } catch (err) {
        setError(err.message || 'Ошибка загрузки данных');
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  // Маска для телефона
  const formatPhone = (value) => {
    let digits = value.replace(/\D/g, '');
    if (digits.startsWith('7')) digits = digits.slice(1);
    if (digits.startsWith('8')) digits = digits.slice(1);
    digits = digits.slice(0, 10);
    if (digits.length === 0) return '';
    let result = '+7';
    if (digits.length > 0) result += ' (' + digits.slice(0, 3);
    if (digits.length >= 4) result += ') ' + digits.slice(3, 6);
    if (digits.length >= 7) result += '-' + digits.slice(6, 8);
    if (digits.length >= 9) result += '-' + digits.slice(8, 10);
    return result;
  };

  const handleChange = (e) => {
    const { name, value, type, checked, files } = e.target;
    
    if (type === 'checkbox') {
      if (name === 'groups') {
        // Обработка чекбоксов групп
        const groupId = parseInt(value);
        setFormData(prev => ({
          ...prev,
          groups: checked
            ? [...prev.groups, groupId]
            : prev.groups.filter(id => id !== groupId),
        }));
      } else {
        setFormData(prev => ({
          ...prev,
          [name]: checked,
        }));
      }
    } else if (type === 'file') {
      setFormData(prev => ({
        ...prev,
        [name]: files[0] || null,
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        [name]: value,
      }));
    }
    
    // Очищаем ошибку для этого поля
    if (formErrors[name]) {
      setFormErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }
    setSubmitError(null);
  };

  const handlePhoneChange = (e) => {
    const { value } = e.target;
    if (!formData.phone_arbitrary_format) {
      const formatted = formatPhone(value);
      setFormData(prev => ({
        ...prev,
        phone_number: formatted,
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        phone_number: value,
      }));
    }
  };

  const handlePhoneArbitraryChange = (e) => {
    const checked = e.target.checked;
    setFormData(prev => ({
      ...prev,
      phone_arbitrary_format: checked,
    }));
    
    // Если переключаемся на произвольный формат, очищаем маску
    if (checked) {
      setFormData(prev => ({
        ...prev,
        phone_number: prev.phone_number.replace(/\D/g, ''),
      }));
    } else {
      // Применяем маску обратно
      setFormData(prev => ({
        ...prev,
        phone_number: formatPhone(prev.phone_number),
      }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setFormErrors({});
    setSubmitError(null);

    try {
      const result = await createUserStep2(formData, formData.image);

      if (result.success) {
        // Переходим на страницу списка пользователей
        navigate('/user_management/users');
      } else {
        setFormErrors(result.errors || {});
        setSubmitError('Ошибка при сохранении профиля пользователя');
      }
    } catch (err) {
      setSubmitError(err.message || 'Ошибка при сохранении профиля пользователя');
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

  if (loading) {
    return (
      <main className="user-create-step2-page">
        <div className="user-form-wrapper">
          <p>Загрузка данных...</p>
        </div>
      </main>
    );
  }

  if (error) {
    return (
      <main className="user-create-step2-page">
        <div className="user-form-wrapper">
          <div className="um-user-warning">{error}</div>
          <Link to="/user_management/users" className="btn btn-secondary">
            Вернуться к списку пользователей
          </Link>
        </div>
      </main>
    );
  }

  return (
    <main className="user-create-step2-page">
      <div className="user-form-wrapper">
        <div className="user-form-header">
          <Link to="/user_management/users" className="back-link">
            &larr; Назад
          </Link>
          <h1 className="form-title">Новый пользователь — шаг 2</h1>
        </div>

        <form onSubmit={handleSubmit} className="user-form" encType="multipart/form-data">
          <div className="form-section">
            <h2 className="section-title">Профиль пользователя</h2>

            <label htmlFor="id_first_name">Имя</label>
            <input
              type="text"
              id="id_first_name"
              name="first_name"
              value={formData.first_name}
              onChange={handleChange}
              required
            />
            {formErrors.first_name && (
              <div className="um-user-warning">{formatErrors(formErrors.first_name)}</div>
            )}

            <label htmlFor="id_last_name">Фамилия</label>
            <input
              type="text"
              id="id_last_name"
              name="last_name"
              value={formData.last_name}
              onChange={handleChange}
              required
            />
            {formErrors.last_name && (
              <div className="um-user-warning">{formatErrors(formErrors.last_name)}</div>
            )}

            <label htmlFor="id_middle_name">Отчество</label>
            <input
              type="text"
              id="id_middle_name"
              name="middle_name"
              value={formData.middle_name}
              onChange={handleChange}
            />
            {formErrors.middle_name && (
              <div className="um-user-warning">{formatErrors(formErrors.middle_name)}</div>
            )}

            <label htmlFor="id_role">Должность</label>
            <select
              id="id_role"
              name="role"
              value={formData.role}
              onChange={handleChange}
            >
              <option value="">— выберите —</option>
              {roles.map(role => (
                <option key={role.id} value={role.id}>
                  {role.name}
                </option>
              ))}
            </select>
            {formErrors.role && (
              <div className="um-user-warning">{formatErrors(formErrors.role)}</div>
            )}

            <label htmlFor="id_groups">Группы пользователя</label>
            <div className="um-user-groups-checkboxes">
              {groups.map(group => (
                <div key={group.id} className="form-check">
                  <input
                    className="form-check-input"
                    type="checkbox"
                    name="groups"
                    id={`group_${group.id}`}
                    value={group.id}
                    checked={formData.groups.includes(group.id)}
                    onChange={handleChange}
                  />
                  <label className="form-check-label" htmlFor={`group_${group.id}`}>
                    {group.name}
                  </label>
                </div>
              ))}
            </div>
            {formErrors.groups && (
              <div className="um-user-warning">{formatErrors(formErrors.groups)}</div>
            )}

            <label htmlFor="id_date_of_birth">Дата рождения</label>
            <input
              type="date"
              id="id_date_of_birth"
              name="date_of_birth"
              value={formData.date_of_birth}
              onChange={handleChange}
            />
            {formErrors.date_of_birth && (
              <div className="um-user-warning">{formatErrors(formErrors.date_of_birth)}</div>
            )}

            <div className="phone-field-wrapper">
              <label htmlFor="id_phone_number">Номер телефона</label>
              <input
                type="text"
                id="id_phone_number"
                name="phone_number"
                className="form-control"
                maxLength={formData.phone_arbitrary_format ? undefined : 18}
                autoComplete="off"
                value={formData.phone_number}
                onChange={handlePhoneChange}
                onKeyDown={(e) => {
                  if (!formData.phone_arbitrary_format) {
                    if (e.key === '+' && formData.phone_number === '') {
                      e.preventDefault();
                      setFormData(prev => ({
                        ...prev,
                        phone_number: '+7',
                      }));
                    }
                  }
                }}
              />
              <div className="form-check">
                <input
                  className="form-check-input"
                  type="checkbox"
                  id="id_phone_arbitrary_format"
                  name="phone_arbitrary_format"
                  checked={formData.phone_arbitrary_format}
                  onChange={handlePhoneArbitraryChange}
                />
                <label className="form-check-label" htmlFor="id_phone_arbitrary_format">
                  Произвольный формат
                </label>
              </div>
            </div>
            {formErrors.phone_number && (
              <div className="um-user-warning">{formatErrors(formErrors.phone_number)}</div>
            )}

            <label htmlFor="id_bio">Биография</label>
            <textarea
              id="id_bio"
              name="bio"
              value={formData.bio}
              onChange={handleChange}
              rows={4}
            />
            {formErrors.bio && (
              <div className="um-user-warning">{formatErrors(formErrors.bio)}</div>
            )}

            <label htmlFor="id_image">Изображение</label>
            <input
              type="file"
              id="id_image"
              name="image"
              accept="image/*"
              onChange={handleChange}
            />
            {formData.image && (
              <div className="image-preview">
                <p>Выбран файл: {formData.image.name}</p>
              </div>
            )}
            {formErrors.image && (
              <div className="um-user-warning">{formatErrors(formErrors.image)}</div>
            )}

            <div className="form-check">
              <input
                className="form-check-input"
                type="checkbox"
                id="id_is_approved"
                name="is_approved"
                checked={formData.is_approved}
                onChange={handleChange}
              />
              <label className="form-check-label" htmlFor="id_is_approved">
                Одобрен
              </label>
            </div>
            {formErrors.is_approved && (
              <div className="um-user-warning">{formatErrors(formErrors.is_approved)}</div>
            )}

            {submitError && (
              <div className="um-user-warning">{submitError}</div>
            )}

            {formErrors.__all__ && (
              <div className="um-user-warning">{formatErrors(formErrors.__all__)}</div>
            )}
          </div>

          <div className="form-actions">
            <button
              type="submit"
              className="btn btn-primary"
              disabled={submitting}
            >
              {submitting ? 'Сохранение...' : 'Сохранить'}
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

export default UserCreateStep2Page;
