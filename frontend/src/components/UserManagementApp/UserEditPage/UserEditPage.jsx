import { useState, useEffect } from 'react';
import { useNavigate, Link, useParams } from 'react-router-dom';
import {
  fetchUserEditData,
  updateUser,
  createRole,
  updateRole,
  deleteRole,
  setRoleResponsible,
  fetchRoleUsers,
} from '../../../api/user_management_api';
import './UserEditPage.css';

const UserEditPage = () => {
  const navigate = useNavigate();
  const { userId } = useParams();
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [submitError, setSubmitError] = useState(null);
  const [formErrors, setFormErrors] = useState({});
  
  const [readonly, setReadonly] = useState(false);
  const [roles, setRoles] = useState([]);
  const [groups, setGroups] = useState([]);
  const [userData, setUserData] = useState(null);
  const [isResponsible, setIsResponsible] = useState(false);
  
  // Модальные окна
  const [showRoleModal, setShowRoleModal] = useState(false);
  const [showResponsibleModal, setShowResponsibleModal] = useState(false);
  const [editingRoleId, setEditingRoleId] = useState(null);
  const [editingRoleName, setEditingRoleName] = useState('');
  const [newRoleName, setNewRoleName] = useState('');
  const [responsibleUsers, setResponsibleUsers] = useState([]);
  const [selectedResponsibleId, setSelectedResponsibleId] = useState('');
  
  const [formData, setFormData] = useState({
    email: '',
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
    is_active: true,
    is_approved: false,
    is_mentor: false,
  });

  // Загрузка данных для формы
  useEffect(() => {
    const loadData = async () => {
      try {
        const data = await fetchUserEditData(userId);
        setRoles(data.roles || []);
        setGroups(data.groups || []);
        setUserData(data.user);
        setReadonly(data.user.readonly || false);
        setIsResponsible(data.profile.is_responsible || false);
        
        // Заполняем форму данными
        setFormData({
          email: data.user.email || '',
          first_name: data.user.first_name || '',
          last_name: data.user.last_name || '',
          middle_name: data.profile.middle_name || '',
          role: data.profile.role_id || '',
          groups: data.user.groups || [],
          date_of_birth: data.profile.date_of_birth || '',
          phone_number: data.profile.phone_number || '',
          phone_arbitrary_format: data.profile.phone_arbitrary_format || false,
          bio: data.profile.bio || '',
          image: null,
          is_active: data.user.is_active !== undefined ? data.user.is_active : true,
          is_approved: data.profile.is_approved || false,
          is_mentor: data.profile.is_mentor || false,
        });
      } catch (err) {
        setError(err.message || 'Ошибка загрузки данных');
      } finally {
        setLoading(false);
      }
    };

    if (userId) {
      loadData();
    }
  }, [userId]);

  // Загрузка пользователей роли для модального окна ответственности
  useEffect(() => {
    if (showResponsibleModal && formData.role) {
      const loadRoleUsers = async () => {
        try {
          const data = await fetchRoleUsers(formData.role);
          setResponsibleUsers(data.users || []);
          // Находим текущего ответственного
          const currentResponsible = data.users.find(u => u.is_responsible);
          setSelectedResponsibleId(currentResponsible ? String(currentResponsible.id) : '');
        } catch (err) {
          console.error('Ошибка загрузки пользователей роли:', err);
        }
      };
      loadRoleUsers();
    }
  }, [showResponsibleModal, formData.role]);

  // Обновление состояния is_responsible при изменении роли
  useEffect(() => {
    if (formData.role) {
      const loadRoleUsers = async () => {
        try {
          const data = await fetchRoleUsers(formData.role);
          const currentUser = data.users.find(u => u.id === parseInt(userId));
          setIsResponsible(currentUser ? currentUser.is_responsible : false);
        } catch (err) {
          console.error('Ошибка проверки ответственности:', err);
        }
      };
      loadRoleUsers();
    } else {
      setIsResponsible(false);
    }
  }, [formData.role, userId]);

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
    
    if (checked) {
      setFormData(prev => ({
        ...prev,
        phone_number: prev.phone_number.replace(/\D/g, ''),
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        phone_number: formatPhone(prev.phone_number),
      }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (readonly) return;
    
    setSubmitting(true);
    setFormErrors({});
    setSubmitError(null);

    try {
      const result = await updateUser(userId, formData, formData.image);

      if (result.success) {
        navigate('/user_management/users');
      } else {
        setFormErrors(result.errors || {});
        setSubmitError('Ошибка при сохранении данных пользователя');
      }
    } catch (err) {
      setSubmitError(err.message || 'Ошибка при сохранении данных пользователя');
    } finally {
      setSubmitting(false);
    }
  };

  // Управление ролями
  const handleCreateRole = async (e) => {
    e.preventDefault();
    if (!newRoleName.trim()) return;
    
    try {
      const result = await createRole(newRoleName.trim());
      if (result.success) {
        setRoles(prev => [...prev, result.role]);
        setNewRoleName('');
      }
    } catch (err) {
      alert(err.message || 'Ошибка при создании должности');
    }
  };

  const handleStartEditRole = (roleId, roleName) => {
    setEditingRoleId(roleId);
    setEditingRoleName(roleName);
  };

  const handleCancelEditRole = () => {
    setEditingRoleId(null);
    setEditingRoleName('');
  };

  const handleSaveRole = async (roleId) => {
    if (!editingRoleName.trim()) {
      alert('Название не может быть пустым');
      return;
    }
    
    try {
      const result = await updateRole(roleId, editingRoleName.trim());
      if (result.success) {
        setRoles(prev => prev.map(r => r.id === roleId ? result.role : r));
        setEditingRoleId(null);
        setEditingRoleName('');
      }
    } catch (err) {
      alert(err.message || 'Ошибка при обновлении должности');
    }
  };

  const handleDeleteRole = async (roleId) => {
    if (!window.confirm('Удалить должность?')) return;
    
    try {
      const result = await deleteRole(roleId);
      if (result.success) {
        setRoles(prev => prev.filter(r => r.id !== roleId));
        if (formData.role === String(roleId)) {
          setFormData(prev => ({ ...prev, role: '' }));
        }
      }
    } catch (err) {
      alert(err.message || 'Ошибка при удалении должности');
    }
  };

  // Управление ответственными
  const handleSetResponsible = async () => {
    try {
      const responsibleId = selectedResponsibleId ? parseInt(selectedResponsibleId) : null;
      const result = await setRoleResponsible(formData.role, responsibleId);
      if (result.success) {
        setShowResponsibleModal(false);
        // Обновляем состояние is_responsible
        setIsResponsible(responsibleId === parseInt(userId));
        alert(result.message);
      }
    } catch (err) {
      alert(err.message || 'Ошибка при назначении ответственного');
    }
  };

  // Обработка чекбокса "Ответственный"
  const handleResponsibleCheckboxChange = async (e) => {
    const checked = e.target.checked;
    
    if (!formData.role) {
      alert('Сначала выберите должность для пользователя');
      e.target.checked = !checked;
      return;
    }
    
    try {
      const responsibleId = checked ? parseInt(userId) : null;
      const result = await setRoleResponsible(formData.role, responsibleId);
      if (result.success) {
        setIsResponsible(checked);
        alert(result.message);
      } else {
        e.target.checked = !checked;
      }
    } catch (err) {
      e.target.checked = !checked;
      alert(err.message || 'Ошибка при назначении ответственности');
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
      <main className="user-edit-page">
        <div className="user-form-wrapper">
          <p>Загрузка данных...</p>
        </div>
      </main>
    );
  }

  if (error) {
    return (
      <main className="user-edit-page">
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
    <main className="user-edit-page">
      <div className="user-form-wrapper">
        <div className="user-form-header">
          <Link to="/user_management/users" className="back-link">
            &larr; Назад
          </Link>
          <h1 className="form-title">Редактировать пользователя</h1>
        </div>

        {readonly && (
          <div className="um-user-warning">
            Вы не можете редактировать этого пользователя
          </div>
        )}

        <form onSubmit={handleSubmit} className="user-form" encType="multipart/form-data">
          <div className="form-section">
            <h2 className="section-title">Общая информация о пользователе</h2>

            <label htmlFor="id_first_name">Имя</label>
            <input
              type="text"
              id="id_first_name"
              name="first_name"
              value={formData.first_name}
              onChange={handleChange}
              required
              disabled={readonly}
              readOnly={readonly}
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
              disabled={readonly}
              readOnly={readonly}
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
              disabled={readonly}
              readOnly={readonly}
            />
            {formErrors.middle_name && (
              <div className="um-user-warning">{formatErrors(formErrors.middle_name)}</div>
            )}

            <label htmlFor="id_role">Должность</label>
            <div className="role-field-wrapper">
              <div style={{ flex: 1 }}>
                <select
                  id="id_role"
                  name="role"
                  value={formData.role}
                  onChange={handleChange}
                  disabled={readonly}
                >
                  <option value="">— выберите —</option>
                  {roles.map(role => (
                    <option key={role.id} value={role.id}>
                      {role.name}
                    </option>
                  ))}
                </select>
              </div>
              {!readonly && (
                <>
                  <button
                    type="button"
                    className="btn btn-link p-0"
                    onClick={() => setShowRoleModal(true)}
                    style={{ marginLeft: '8px' }}
                    title="Управление должностями"
                  >
                    <i className="fa fa-cog"></i>
                  </button>
                  <div className="form-check" title="Пользователь является ответственным за свою должность">
                    <input
                      type="checkbox"
                      className="form-check-input"
                      id="is_responsible"
                      checked={isResponsible}
                      onChange={handleResponsibleCheckboxChange}
                      disabled={!formData.role}
                    />
                    <label className="form-check-label" htmlFor="is_responsible">
                      Ответственный
                    </label>
                  </div>
                </>
              )}
            </div>
            {formErrors.role && (
              <div className="um-user-warning">{formatErrors(formErrors.role)}</div>
            )}

            <label htmlFor="id_email">Email</label>
            <input
              type="email"
              id="id_email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              required
              disabled={readonly}
              readOnly={readonly}
            />
            {formErrors.email && (
              <div className="um-user-warning">{formatErrors(formErrors.email)}</div>
            )}

            <label htmlFor="id_groups">Группы пользователя</label>
            {readonly ? (
              <div className="um-user-groups">
                {formData.groups.length === 1 ? (
                  <p>Пользователь состоит в группе: <b>{groups.find(g => g.id === formData.groups[0])?.name}</b></p>
                ) : formData.groups.length > 1 ? (
                  <>
                    <p>Группы пользователя:</p>
                    <ul className="um-user-groups-list">
                      {formData.groups.map(groupId => {
                        const group = groups.find(g => g.id === groupId);
                        return group ? <li key={groupId}><b>{group.name}</b></li> : null;
                      })}
                    </ul>
                  </>
                ) : (
                  <p>Пользователь не состоит в группах</p>
                )}
              </div>
            ) : (
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
            )}
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
              disabled={readonly}
              readOnly={readonly}
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
                disabled={readonly}
                readOnly={readonly}
              />
              {!readonly && (
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
              )}
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
              disabled={readonly}
              readOnly={readonly}
            />
            {formErrors.bio && (
              <div className="um-user-warning">{formatErrors(formErrors.bio)}</div>
            )}

            {!readonly && (
              <>
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
              </>
            )}

            <div className="form-check">
              <input
                className="form-check-input"
                type="checkbox"
                id="id_is_active"
                name="is_active"
                checked={formData.is_active}
                onChange={handleChange}
                disabled={readonly}
              />
              <label className="form-check-label" htmlFor="id_is_active">
                Активен
              </label>
            </div>
            {formErrors.is_active && (
              <div className="um-user-warning">{formatErrors(formErrors.is_active)}</div>
            )}

            <div className="form-check">
              <input
                className="form-check-input"
                type="checkbox"
                id="id_is_approved"
                name="is_approved"
                checked={formData.is_approved}
                onChange={handleChange}
                disabled={readonly}
              />
              <label className="form-check-label" htmlFor="id_is_approved">
                Одобрен
              </label>
            </div>
            {formErrors.is_approved && (
              <div className="um-user-warning">{formatErrors(formErrors.is_approved)}</div>
            )}

            <div className="form-check">
              <input
                className="form-check-input"
                type="checkbox"
                id="id_is_mentor"
                name="is_mentor"
                checked={formData.is_mentor}
                onChange={handleChange}
                disabled={readonly}
              />
              <label className="form-check-label" htmlFor="id_is_mentor">
                Наставник
              </label>
            </div>
            {formErrors.is_mentor && (
              <div className="um-user-warning">{formatErrors(formErrors.is_mentor)}</div>
            )}

            {submitError && (
              <div className="um-user-warning">{submitError}</div>
            )}

            {formErrors.__all__ && (
              <div className="um-user-warning">{formatErrors(formErrors.__all__)}</div>
            )}
          </div>

          <div className="form-actions">
            {!readonly && (
              <>
                <Link
                  to={`/user_management/user/${userId}/password`}
                  className="btn btn-outline-info"
                >
                  Сменить пароль
                </Link>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={submitting}
                >
                  {submitting ? 'Сохранение...' : 'Сохранить'}
                </button>
              </>
            )}
            <Link to="/user_management/users" className="btn btn-secondary">
              Отмена
            </Link>
          </div>
        </form>
      </div>

      {/* Модальное окно для управления ролями */}
      {showRoleModal && (
        <div className="modal-overlay" onClick={() => setShowRoleModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h5 className="modal-title">Управление должностями</h5>
              <button
                type="button"
                className="btn-close"
                onClick={() => setShowRoleModal(false)}
                aria-label="Закрыть"
              ></button>
            </div>
            <div className="modal-body">
              <form onSubmit={handleCreateRole}>
                <div className="mb-3">
                  <label htmlFor="id_new_role" className="form-label">
                    Добавить новую должность
                  </label>
                  <input
                    type="text"
                    className="form-control"
                    id="id_new_role"
                    value={newRoleName}
                    onChange={(e) => setNewRoleName(e.target.value)}
                    maxLength={200}
                  />
                </div>
                <button type="submit" className="btn btn-primary mb-3">
                  Добавить
                </button>
              </form>
              <hr />
              <h6>Существующие должности:</h6>
              <ul className="list-group">
                {roles.length === 0 ? (
                  <li className="list-group-item">Нет должностей</li>
                ) : (
                  roles.map(role => (
                    <li
                      key={role.id}
                      className="list-group-item d-flex justify-content-between align-items-center"
                    >
                      {editingRoleId === role.id ? (
                        <>
                          <input
                            type="text"
                            className="form-control form-control-sm d-inline"
                            style={{ width: '120px', display: 'inline-block' }}
                            value={editingRoleName}
                            onChange={(e) => setEditingRoleName(e.target.value)}
                          />
                          <div style={{ display: 'flex', gap: '6px', marginLeft: '10px' }}>
                            <button
                              type="button"
                              className="btn btn-sm btn-success"
                              onClick={() => handleSaveRole(role.id)}
                            >
                              <i className="fa fa-save"></i>
                            </button>
                            <button
                              type="button"
                              className="btn btn-sm btn-secondary"
                              onClick={handleCancelEditRole}
                            >
                              <i className="fa fa-times"></i>
                            </button>
                          </div>
                        </>
                      ) : (
                        <>
                          <span>{role.name}</span>
                          <div style={{ display: 'flex', gap: '6px', marginLeft: '10px' }}>
                            <button
                              type="button"
                              className="btn btn-sm btn-secondary"
                              onClick={() => handleStartEditRole(role.id, role.name)}
                            >
                              <i className="fa fa-pencil"></i>
                            </button>
                            <button
                              type="button"
                              className="btn btn-sm btn-danger"
                              onClick={() => handleDeleteRole(role.id)}
                            >
                              <i className="fa fa-trash"></i>
                            </button>
                          </div>
                        </>
                      )}
                    </li>
                  ))
                )}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Модальное окно для управления ответственными */}
      {showResponsibleModal && formData.role && (
        <div className="modal-overlay" onClick={() => setShowResponsibleModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h5 className="modal-title">Управление ответственным</h5>
              <button
                type="button"
                className="btn-close"
                onClick={() => setShowResponsibleModal(false)}
                aria-label="Закрыть"
              ></button>
            </div>
            <div className="modal-body">
              <div className="mb-3">
                <label htmlFor="responsible_user" className="form-label">
                  Ответственный для должности "{roles.find(r => r.id === parseInt(formData.role))?.name}"
                </label>
                <select
                  className="form-control"
                  id="responsible_user"
                  value={selectedResponsibleId}
                  onChange={(e) => setSelectedResponsibleId(e.target.value)}
                >
                  <option value="">— не назначен —</option>
                  {responsibleUsers.map(user => (
                    <option key={user.id} value={user.id}>
                      {user.full_name}
                    </option>
                  ))}
                </select>
                <div className="form-text">
                  Выберите пользователя, который будет ответственным за данную должность
                </div>
              </div>
              <button
                type="button"
                className="btn btn-primary"
                onClick={handleSetResponsible}
              >
                Сохранить
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
};

export default UserEditPage;
