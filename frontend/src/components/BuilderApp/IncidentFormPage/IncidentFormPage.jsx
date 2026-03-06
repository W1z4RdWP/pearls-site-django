import { useState, useEffect, useCallback, useRef } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import {
  fetchIncidentFormData,
  createIncident,
  updateIncident,
  createIncidentCourse,
  searchUsers,
  getUsersByIds,
  getGroups,
  getGroupUsers,
} from '../../../api/builder_api';
import './IncidentFormPage.css';

const TOOLTIP_MENTOR =
  'В списке отображаются сотрудники со статусом «Наставник».\nЭтот человек отвечает за проверку и подтверждение корректности выполнения теста обучающегося.\nПоле обязательное для заполнения, даже если тест не требует проверки — наставник должен быть назначен в любом случае.';
const TOOLTIP_MENTORS_TIME =
  'Укажите период, в течение которого наставник должен проверить тест после завершения урока.\nПо умолчанию — 2 дня после окончания урока, но срок можно увеличить или уменьшить при необходимости.';
const TOOLTIP_ASSIGNED_TIME =
  'Кол-во дней для прохождения курса, начинается отсчет, после прохождения курса ответственным руководителем за актуальность курса';
const TOOLTIP_EXPERT_TIME =
  'Укажите период, в течение которого руководитель должен проверить уроки курса.\nПо умолчанию — 3 дня, но срок можно увеличить или уменьшить при необходимости.';
const TOOLTIP_DESCRIPTION =
  'Здесь нужно зафиксировать саму суть ситуации, без общих фраз.\n\n💡 Отвечай на 4 коротких вопроса:\n1. Что произошло? (описать событие, факт — например: "пациент ждал 40 минут", "в DENT не внесли оплату").\n2. Где произошло? (филиал, кабинет, отдел).\n3. С кем / с какой ролью? (администратор, врач, ассистент, техник).\n4. Почему или из-за чего? (ошибка, недопонимание, отсутствие стандарта, неисправное оборудование и т.д.).\n\n❗️Не нужно писать: "виноват админ" или "пациент грубый" — важно зафиксировать факт и контекст, не эмоцию.\n\nПример хорошего описания:\n"Пациент ожидал приём 35 минут из-за того, что администратор не уведомил врача о прибытии. В расписании была путаница, не было отметки о переносе."\n\nПример плохого описания:\n"Админ опять всё перепутал. Пациент злой."';

const DEFAULT_MENTORS_TIME = 2;
const DEFAULT_ASSIGNED_TIME = 3;
const DEFAULT_EXPERT_TIME = 3;

function HelpIcon({ tooltip, label = 'Подсказка' }) {
  const [visible, setVisible] = useState(false);
  return (
    <span
      className="incident-form-page__help-icon"
      role="button"
      tabIndex={0}
      aria-label={label}
      title={tooltip}
      onMouseEnter={() => setVisible(true)}
      onMouseLeave={() => setVisible(false)}
      onFocus={() => setVisible(true)}
      onBlur={() => setVisible(false)}
    >
      ?
      {visible && (
        <span className="incident-form-page__tooltip" role="tooltip">
          {tooltip}
        </span>
      )}
    </span>
  );
}

function UserSelectModal({ isOpen, title, onClose, onSelect, mentorOnly = false, excludeStaff = false }) {
  const [query, setQuery] = useState('');
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const debounceRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    if (!isOpen) return;
    setQuery('');
    setUsers([]);
    setLoading(true);
    searchUsers('', { mentor_only: mentorOnly, exclude_staff: excludeStaff })
      .then((res) => setUsers(res.users || []))
      .catch(() => setUsers([]))
      .finally(() => setLoading(false));
    setTimeout(() => inputRef.current?.focus(), 100);
  }, [isOpen, mentorOnly, excludeStaff]);

  useEffect(() => {
    if (!isOpen) return;
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      setLoading(true);
      searchUsers(query, { mentor_only: mentorOnly, exclude_staff: excludeStaff })
        .then((res) => setUsers(res.users || []))
        .catch(() => setUsers([]))
        .finally(() => setLoading(false));
    }, 300);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [query, isOpen, mentorOnly, excludeStaff]);

  if (!isOpen) return null;

  const handleSelect = (user) => {
    onSelect(user.id, user.full_name);
    onClose();
  };

  return (
    <div className="incident-form-page__user-modal" role="dialog" aria-modal="true" aria-label={title}>
      <div className="incident-form-page__user-modal-backdrop" onClick={onClose} />
      <div className="incident-form-page__user-modal-content">
        <div className="incident-form-page__user-modal-header">
          <h3>{title}</h3>
          <span className="incident-form-page__user-modal-close" onClick={onClose} role="button" aria-label="Закрыть">
            &times;
          </span>
        </div>
        <div className="incident-form-page__user-modal-body">
          <div className="incident-form-page__user-search-box">
            <input
              ref={inputRef}
              type="text"
              className="incident-form-page__input"
              placeholder="Поиск по имени или фамилии..."
              autoComplete="off"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </div>
          <div className="incident-form-page__user-list-container">
            {loading ? (
              <div className="incident-form-page__user-list-loading">Загрузка...</div>
            ) : users.length === 0 ? (
              <div className="incident-form-page__user-list-empty">Пользователи не найдены</div>
            ) : (
              <ul className="incident-form-page__user-list">
                {users.map((user) => (
                  <li
                    key={user.id}
                    className="incident-form-page__user-list-item"
                    onClick={() => handleSelect(user)}
                    role="button"
                    tabIndex={0}
                    onKeyDown={(e) => e.key === 'Enter' && handleSelect(user)}
                  >
                    <span className="incident-form-page__user-list-item-name">
                      {user.full_name}
                      {user.role ? ` (${user.role})` : ''}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function AssignedModal({ isOpen, onClose, selectedUsers, violators, onConfirm, onLoadGroups, onAddGroupUsers, onSearchUsers, onAddUser, onRemoveUser, onToggleViolator }) {
  const [groups, setGroups] = useState([]);
  const [groupsLoading, setGroupsLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [dropdownVisible, setDropdownVisible] = useState(false);
  const debounceRef = useRef(null);

  useEffect(() => {
    if (!isOpen) return;
    setGroupsLoading(true);
    onLoadGroups()
      .then((res) => setGroups(res.groups || []))
      .catch(() => setGroups([]))
      .finally(() => setGroupsLoading(false));
    setSearchQuery('');
    setSearchResults([]);
    setDropdownVisible(false);
  }, [isOpen, onLoadGroups]);

  useEffect(() => {
    if (!isOpen) return;
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (searchQuery.trim() === '') {
      setSearchResults([]);
      setDropdownVisible(false);
      return;
    }
    debounceRef.current = setTimeout(() => {
      setSearchLoading(true);
      onSearchUsers(searchQuery)
        .then((res) => setSearchResults(res.users || []))
        .then(() => setDropdownVisible(true))
        .catch(() => setSearchResults([]))
        .finally(() => setSearchLoading(false));
    }, 300);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [searchQuery, isOpen, onSearchUsers]);

  if (!isOpen) return null;

  const selectedList = Array.from(selectedUsers.values());

  return (
    <div className="incident-form-page__assigned-modal" role="dialog" aria-modal="true" aria-label="Выберите назначенных">
      <div className="incident-form-page__assigned-modal-backdrop" onClick={onClose} />
      <div className="incident-form-page__assigned-modal-content">
        <div className="incident-form-page__assigned-modal-header">
          <h3>Выберите назначенных</h3>
          <span className="incident-form-page__assigned-modal-close" onClick={onClose} role="button" aria-label="Закрыть">
            &times;
          </span>
        </div>
        <div className="incident-form-page__assigned-modal-body">
          <div className="incident-form-page__assigned-columns">
            <div className="incident-form-page__assigned-left-column">
              <h4>Группы</h4>
              <div className="incident-form-page__group-list">
                {groupsLoading ? (
                  <div className="incident-form-page__group-list-loading">Загрузка групп...</div>
                ) : groups.length === 0 ? (
                  <div className="incident-form-page__group-list-empty">Группы не найдены</div>
                ) : (
                  groups.map((group) => (
                    <div
                      key={group.id}
                      className="incident-form-page__group-item"
                      onClick={() => onAddGroupUsers(group.id)}
                      role="button"
                      tabIndex={0}
                      onKeyDown={(e) => e.key === 'Enter' && onAddGroupUsers(group.id)}
                    >
                      <div className="incident-form-page__group-item-name">{group.name}</div>
                      <div className="incident-form-page__group-item-count">{group.user_count} пользователей</div>
                    </div>
                  ))
                )}
              </div>
            </div>
            <div className="incident-form-page__assigned-divider" />
            <div className="incident-form-page__assigned-right-column">
              <h4>Выбранные пользователи</h4>
              <div className="incident-form-page__assigned-search-box">
                <input
                  type="text"
                  className="incident-form-page__input"
                  placeholder="Поиск пользователя для добавления..."
                  autoComplete="off"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
                {dropdownVisible && (
                  <div className="incident-form-page__search-results-dropdown">
                    {searchLoading ? (
                      <div className="incident-form-page__search-results-loading">Поиск...</div>
                    ) : searchResults.length === 0 ? (
                      <div className="incident-form-page__search-results-empty">Пользователи не найдены</div>
                    ) : (
                      searchResults
                        .filter((u) => !selectedUsers.has(u.id))
                        .map((user) => (
                          <div
                            key={user.id}
                            className="incident-form-page__search-result-item"
                            onClick={() => {
                              onAddUser(user);
                              setSearchQuery('');
                              setDropdownVisible(false);
                            }}
                            role="button"
                            tabIndex={0}
                          >
                            <span className="incident-form-page__search-result-name">
                              {user.full_name}
                              {user.role ? ` (${user.role})` : ''}
                            </span>
                          </div>
                        ))
                    )}
                    {searchResults.length > 0 && searchResults.every((u) => selectedUsers.has(u.id)) && (
                      <div className="incident-form-page__search-results-empty">Все найденные пользователи уже выбраны</div>
                    )}
                  </div>
                )}
              </div>
              <div className="incident-form-page__selected-users-list">
                {selectedList.length === 0 ? (
                  <div className="incident-form-page__selected-users-empty">Пользователи не выбраны</div>
                ) : (
                  selectedList.map((user) => (
                    <div key={user.id} className="incident-form-page__selected-user-item">
                      <div className="incident-form-page__selected-user-info">
                        <div className="incident-form-page__selected-user-name">{user.full_name}</div>
                      </div>
                      <div className="incident-form-page__selected-user-actions">
                        <label className="incident-form-page__selected-user-checkbox" title="Нарушитель">
                          <input
                            type="checkbox"
                            checked={violators.has(user.id)}
                            onChange={() => onToggleViolator(user.id)}
                          />
                          <span className="incident-form-page__checkbox-label">Нарушитель</span>
                        </label>
                        <span
                          className="incident-form-page__selected-user-remove"
                          onClick={() => onRemoveUser(user.id)}
                          role="button"
                          tabIndex={0}
                          aria-label="Удалить"
                        >
                          &times;
                        </span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
          <div className="incident-form-page__assigned-modal-footer">
            <button type="button" className="incident-form-page__btn incident-form-page__btn--primary" onClick={() => { onConfirm(); onClose(); }}>
              Применить
            </button>
            <button type="button" className="incident-form-page__btn incident-form-page__btn--secondary" onClick={onClose}>
              Отмена
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

const IncidentFormPage = () => {
  const { pk } = useParams();
  const navigate = useNavigate();
  const isEdit = pk != null;

  const [loading, setLoading] = useState(true);
  const [submitLoading, setSubmitLoading] = useState(false);
  const [createCourseLoading, setCreateCourseLoading] = useState(false);
  const [error, setError] = useState(null);
  const [formPayload, setFormPayload] = useState(null);

  const [title, setTitle] = useState('');
  const [incidentType, setIncidentType] = useState('');
  const [userId, setUserId] = useState(null);
  const [userDisplayName, setUserDisplayName] = useState('Выберите пользователя...');
  const [responsibleMentorId, setResponsibleMentorId] = useState(null);
  const [mentorDisplayName, setMentorDisplayName] = useState('Выберите пользователя...');
  const [mentorsTimeToCheck, setMentorsTimeToCheck] = useState(DEFAULT_MENTORS_TIME);
  const [assignedTo, setAssignedTo] = useState(new Map());
  const [violators, setViolators] = useState(new Set());
  const [assignedToTimeToComplete, setAssignedToTimeToComplete] = useState(DEFAULT_ASSIGNED_TIME);
  const [expertId, setExpertId] = useState(null);
  const [expertDisplayName, setExpertDisplayName] = useState('Выберите пользователя...');
  const [expertTimeToComplete, setExpertTimeToComplete] = useState(DEFAULT_EXPERT_TIME);
  const [status, setStatus] = useState('accepted');
  const [description, setDescription] = useState('');
  const [courseSlug, setCourseSlug] = useState(null);
  const [hasCourse, setHasCourse] = useState(false);

  const [userModalMode, setUserModalMode] = useState(null);
  const [assignedModalOpen, setAssignedModalOpen] = useState(false);
  const [fieldErrors, setFieldErrors] = useState({});

  const loadFormData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchIncidentFormData(isEdit ? Number(pk) : null);
      setFormPayload(data);
      const firstType = data.incident_type_choices?.[0]?.[0];
      setIncidentType(firstType ?? '');
      setStatus(data.defaults?.status || 'accepted');
      setMentorsTimeToCheck(data.defaults?.mentors_time_to_check ?? DEFAULT_MENTORS_TIME);
      setAssignedToTimeToComplete(data.defaults?.assigned_to_time_to_complete ?? DEFAULT_ASSIGNED_TIME);
      setExpertTimeToComplete(data.defaults?.expert_time_to_complete ?? DEFAULT_EXPERT_TIME);

      if (data.incident) {
        const inc = data.incident;
        setTitle(inc.title || '');
        setIncidentType(inc.incident_type || '');
        setUserId(inc.user_id || null);
        setResponsibleMentorId(inc.responsible_mentor_id || null);
        setMentorsTimeToCheck(inc.mentors_time_to_check ?? DEFAULT_MENTORS_TIME);
        setAssignedToTimeToComplete(inc.assigned_to_time_to_complete ?? DEFAULT_ASSIGNED_TIME);
        setExpertId(inc.expert_id || null);
        setExpertTimeToComplete(inc.expert_time_to_complete ?? DEFAULT_EXPERT_TIME);
        setStatus(inc.status || 'accepted');
        setDescription(inc.description || '');
        setCourseSlug(inc.course_slug || null);
        setHasCourse(inc.has_course || false);

        if (inc.user_id) {
          getUsersByIds([inc.user_id]).then((r) => {
            const u = r.users?.[0];
            if (u) setUserDisplayName(u.full_name);
          });
        } else setUserDisplayName('Выберите пользователя...');

        if (inc.responsible_mentor_id) {
          getUsersByIds([inc.responsible_mentor_id]).then((r) => {
            const u = r.users?.[0];
            if (u) setMentorDisplayName(u.full_name);
          });
        } else setMentorDisplayName('Выберите пользователя...');

        if (inc.expert_id) {
          getUsersByIds([inc.expert_id]).then((r) => {
            const u = r.users?.[0];
            if (u) setExpertDisplayName(u.full_name);
          });
        } else setExpertDisplayName('Выберите пользователя...');

        if (inc.assigned_to_ids?.length) {
          getUsersByIds(inc.assigned_to_ids).then((r) => {
            const map = new Map();
            (r.users || []).forEach((u) => map.set(u.id, u));
            setAssignedTo(map);
          });
          const violSet = new Set(inc.violators_ids || []);
          setViolators(violSet);
        }
      }
    } catch (err) {
      setError(err.message || 'Ошибка загрузки формы');
    } finally {
      setLoading(false);
    }
  }, [pk, isEdit]);

  useEffect(() => {
    loadFormData();
  }, [loadFormData]);

  const handleUserSelect = (mode, id, displayName) => {
    if (mode === 'user') {
      setUserId(id);
      setUserDisplayName(displayName);
    } else if (mode === 'mentor') {
      setResponsibleMentorId(id);
      setMentorDisplayName(displayName);
    } else if (mode === 'expert') {
      setExpertId(id);
      setExpertDisplayName(displayName);
    }
    setUserModalMode(null);
  };

  const handleTimeChange = (field, delta) => {
    const min = 1;
    const setters = {
      mentors: [mentorsTimeToCheck, setMentorsTimeToCheck],
      assigned: [assignedToTimeToComplete, setAssignedToTimeToComplete],
      expert: [expertTimeToComplete, setExpertTimeToComplete],
    };
    const [val, setVal] = setters[field];
    const next = val + delta;
    if (delta < 0 && next < min) return;
    setVal(next);
  };

  const handleAssignedConfirm = () => {
    setAssignedModalOpen(false);
  };

  const handleLoadGroups = useCallback(() => getGroups({ exclude_staff: true }), []);
  const handleAddGroupUsers = useCallback((groupId) => {
    getGroupUsers(groupId, { exclude_staff: true }).then((res) => {
      setAssignedTo((prev) => {
        const next = new Map(prev);
        (res.users || []).forEach((u) => next.set(u.id, u));
        return next;
      });
    });
  }, []);
  const handleSearchUsersAssigned = useCallback((q) => searchUsers(q, { exclude_staff: true }), []);
  const handleAddUser = useCallback((user) => {
    setAssignedTo((prev) => new Map(prev).set(user.id, user));
  }, []);
  const handleRemoveUser = useCallback((id) => {
    setAssignedTo((prev) => {
      const next = new Map(prev);
      next.delete(id);
      return next;
    });
    setViolators((prev) => {
      const next = new Set(prev);
      next.delete(id);
      return next;
    });
  }, []);
  const handleToggleViolator = useCallback((id) => {
    setViolators((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }, []);

  const buildSubmitPayload = () => ({
    title: title.trim(),
    incident_type: incidentType,
    user_id: userId,
    responsible_mentor_id: responsibleMentorId || undefined,
    mentors_time_to_check: mentorsTimeToCheck,
    assigned_to_ids: Array.from(assignedTo.keys()),
    violators_ids: Array.from(violators).filter((id) => assignedTo.has(id)),
    expert_id: expertId || undefined,
    assigned_to_time_to_complete: assignedToTimeToComplete,
    expert_time_to_complete: expertTimeToComplete,
    status: isEdit ? status : 'accepted',
    description: description.trim() || '',
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setFieldErrors({});
    setSubmitLoading(true);
    try {
      const payload = buildSubmitPayload();
      if (isEdit) {
        await updateIncident(Number(pk), payload);
        navigate('/builder/incidents');
      } else {
        const res = await createIncident(payload);
        navigate(res.redirect_url || `/builder/incidents/${res.id}/edit`);
      }
    } catch (err) {
      if (err.errors) setFieldErrors(err.errors);
      else setError(err.message || 'Ошибка сохранения');
    } finally {
      setSubmitLoading(false);
    }
  };

  const handleCreateCourse = async () => {
    if (!pk || hasCourse) return;
    setCreateCourseLoading(true);
    try {
      const res = await createIncidentCourse(Number(pk));
      if (res.redirect_url) navigate(res.redirect_url);
    } catch (err) {
      setError(err.message || 'Ошибка создания курса');
    } finally {
      setCreateCourseLoading(false);
    }
  };

  if (loading && !formPayload) {
    return (
      <main className="incident-form-page">
        <div className="incident-form-card">
          <p className="incident-form-page__loading">Загрузка…</p>
        </div>
      </main>
    );
  }

  if (error && !formPayload) {
    return (
      <main className="incident-form-page">
        <div className="incident-form-card">
          <p className="incident-form-page__error" role="alert">{error}</p>
          <Link to="/builder/incidents" className="incident-form-page__btn incident-form-page__btn--secondary">Инциденты</Link>
        </div>
      </main>
    );
  }

  const incidentTypeChoices = formPayload?.incident_type_choices || [];
  const statusChoices = formPayload?.status_choices || [];
  const assignedCount = assignedTo.size;

  return (
    <main className="incident-form-page">
      <div className="incident-form-card">
        <h2 className="incident-form-page__title">{isEdit ? 'Редактирование инцидента' : 'Новый инцидент'}</h2>

        <form onSubmit={handleSubmit} autoComplete="off" className="incident-form-page__form">
          {error && <div className="incident-form-page__form-error text-danger">{error}</div>}

          <div className="form-group">
            <label htmlFor="incident-title">Название инцидента</label>
            <input
              id="incident-title"
              type="text"
              className="incident-form-page__input form-control"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Введение в Dent"
            />
            {fieldErrors.title && <div className="text-danger mt-1">{fieldErrors.title}</div>}
          </div>

          <div className="form-group">
            <label htmlFor="incident-type">Тип инцидента</label>
            <select
              id="incident-type"
              className="incident-form-page__input form-control"
              value={incidentType}
              onChange={(e) => setIncidentType(e.target.value)}
            >
              {incidentTypeChoices.map(([val, label]) => (
                <option key={val} value={val}>{label}</option>
              ))}
            </select>
            {fieldErrors.incident_type && <div className="text-danger mt-1">{fieldErrors.incident_type}</div>}
          </div>

          <div className="form-group">
            <label htmlFor="user-display">Кто зафиксировал</label>
            <div
              className="incident-form-page__user-select-field user-select-field"
              id="userSelectField"
              onClick={() => setUserModalMode('user')}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => e.key === 'Enter' && setUserModalMode('user')}
            >
              <span className={`user-display-name ${!userId ? 'user-display-placeholder' : ''}`}>{userDisplayName}</span>
              <span className="user-select-icon">&#9660;</span>
            </div>
            {fieldErrors.user && <div className="text-danger mt-1">{fieldErrors.user}</div>}
          </div>

          <div className="form-group incident-form-page__form-group--mentor">
            <div className="incident-form-page__label-row">
              <label htmlFor="mentor-display">Проверяющий наставник</label>
              <HelpIcon tooltip={TOOLTIP_MENTOR} />
            </div>
            <div className="incident-form-page__row-with-time">
              <div
                className="incident-form-page__user-select-field user-select-field"
                onClick={() => setUserModalMode('mentor')}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => e.key === 'Enter' && setUserModalMode('mentor')}
              >
                <span className={`user-display-name ${!responsibleMentorId ? 'user-display-placeholder' : ''}`}>{mentorDisplayName}</span>
                <span className="user-select-icon">&#9660;</span>
              </div>
              <div className="incident-form-page__time-counter-wrapper time-counter-wrapper">
                <button type="button" className="time-counter-btn" onClick={() => handleTimeChange('mentors', -1)} aria-label="Уменьшить">−</button>
                <input type="number" readOnly min={1} className="time-counter-input" value={mentorsTimeToCheck} aria-label="Дней на проверку наставником" />
                <button type="button" className="time-counter-btn" onClick={() => handleTimeChange('mentors', 1)} aria-label="Увеличить">+</button>
                <HelpIcon tooltip={TOOLTIP_MENTORS_TIME} />
              </div>
            </div>
            {fieldErrors.responsible_mentor && <div className="text-danger mt-1">{fieldErrors.responsible_mentor}</div>}
            {fieldErrors.mentors_time_to_check && <div className="text-danger mt-1">{fieldErrors.mentors_time_to_check}</div>}
          </div>

          <div className="form-group">
            <label htmlFor="assigned-display">Кому назначен</label>
            <div className="incident-form-page__row-with-time">
              <div
                className="incident-form-page__assigned-select-field assigned-select-field"
                id="assignedSelectField"
                onClick={() => setAssignedModalOpen(true)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => e.key === 'Enter' && setAssignedModalOpen(true)}
              >
                <span className="assigned-display-text">
                  <span className="assigned-count">{assignedCount}</span> пользователей выбрано
                </span>
                <span className="assigned-select-icon">&#9660;</span>
              </div>
              <div className="incident-form-page__time-counter-wrapper time-counter-wrapper">
                <button type="button" className="time-counter-btn" onClick={() => handleTimeChange('assigned', -1)} aria-label="Уменьшить">−</button>
                <input type="number" readOnly min={1} className="time-counter-input" value={assignedToTimeToComplete} aria-label="Дней на завершение обучения" />
                <button type="button" className="time-counter-btn" onClick={() => handleTimeChange('assigned', 1)} aria-label="Увеличить">+</button>
                <HelpIcon tooltip={TOOLTIP_ASSIGNED_TIME} />
              </div>
            </div>
            {(fieldErrors.assigned_to || fieldErrors.assigned_to_time_to_complete) && (
              <div className="text-danger mt-1">{fieldErrors.assigned_to || fieldErrors.assigned_to_time_to_complete}</div>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="expert-display">Ответственный за актуальность курса</label>
            <div className="incident-form-page__row-with-time">
              <div
                className="incident-form-page__user-select-field user-select-field"
                onClick={() => setUserModalMode('expert')}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => e.key === 'Enter' && setUserModalMode('expert')}
              >
                <span className={`user-display-name ${!expertId ? 'user-display-placeholder' : ''}`}>{expertDisplayName}</span>
                <span className="user-select-icon">&#9660;</span>
              </div>
              <div className="incident-form-page__time-counter-wrapper time-counter-wrapper">
                <button type="button" className="time-counter-btn" onClick={() => handleTimeChange('expert', -1)} aria-label="Уменьшить">−</button>
                <input type="number" readOnly min={1} className="time-counter-input" value={expertTimeToComplete} aria-label="Дней на проверку экспертом" />
                <button type="button" className="time-counter-btn" onClick={() => handleTimeChange('expert', 1)} aria-label="Увеличить">+</button>
                <HelpIcon tooltip={TOOLTIP_EXPERT_TIME} />
              </div>
            </div>
            {fieldErrors.expert && <div className="text-danger mt-1">{fieldErrors.expert}</div>}
          </div>

          <div className="form-group">
            <label htmlFor="incident-status">Статус</label>
            <select id="incident-status" className="incident-form-page__input form-control" value={status} disabled aria-readonly>
              {statusChoices.map(([val, label]) => (
                <option key={val} value={val}>{label}</option>
              ))}
            </select>
            {fieldErrors.status && <div className="text-danger mt-1">{fieldErrors.status}</div>}
          </div>

          <div className="form-group">
            <div className="incident-form-page__label-row">
              <label htmlFor="incident-description">Описание проблемы</label>
              <HelpIcon tooltip={TOOLTIP_DESCRIPTION} />
            </div>
            <textarea
              id="incident-description"
              className="incident-form-page__input form-control"
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Дополнительные комментарии..."
            />
            {fieldErrors.description && <div className="text-danger mt-1">{fieldErrors.description}</div>}
          </div>

          <div className="incident-form-page__form-actions form-actions mt-4">
            <div>
              <button type="submit" className="incident-form-page__btn incident-form-page__btn--primary btn btn-primary" disabled={submitLoading}>
                {submitLoading ? 'Сохранение…' : 'Сохранить'}
              </button>
              <Link to="/builder/incidents" className="incident-form-page__btn incident-form-page__btn--secondary btn btn-secondary">Инциденты</Link>
            </div>
            {isEdit && pk && (
              hasCourse && courseSlug ? (
                <Link to={`/courses/course/${courseSlug}`} className="incident-form-page__btn incident-form-page__btn--success btn btn-success">
                  <i className="fa fa-graduation-cap" aria-hidden /> Перейти к курсу
                </Link>
              ) : (
                <button
                  type="button"
                  className="incident-form-page__btn incident-form-page__btn--success btn btn-success"
                  onClick={handleCreateCourse}
                  disabled={createCourseLoading}
                >
                  <i className="fa fa-graduation-cap" aria-hidden /> {createCourseLoading ? 'Создание…' : 'Сформировать курс'}
                </button>
              )
            )}
            {!isEdit && (
              <button type="button" className="incident-form-page__btn btn btn-success" disabled>
                <i className="fa fa-graduation-cap" aria-hidden /> Сформировать курс
              </button>
            )}
          </div>
        </form>
      </div>

      <UserSelectModal
        isOpen={userModalMode === 'user'}
        title="Выберите сотрудника"
        onClose={() => setUserModalMode(null)}
        onSelect={(id, name) => handleUserSelect('user', id, name)}
        mentorOnly={false}
        excludeStaff={true}
      />
      <UserSelectModal
        isOpen={userModalMode === 'mentor'}
        title="Выберите сотрудника"
        onClose={() => setUserModalMode(null)}
        onSelect={(id, name) => handleUserSelect('mentor', id, name)}
        mentorOnly={true}
        excludeStaff={false}
      />
      <UserSelectModal
        isOpen={userModalMode === 'expert'}
        title="Выберите сотрудника"
        onClose={() => setUserModalMode(null)}
        onSelect={(id, name) => handleUserSelect('expert', id, name)}
        mentorOnly={false}
        excludeStaff={true}
      />

      <AssignedModal
        isOpen={assignedModalOpen}
        onClose={() => setAssignedModalOpen(false)}
        selectedUsers={assignedTo}
        violators={violators}
        onConfirm={handleAssignedConfirm}
        onLoadGroups={handleLoadGroups}
        onAddGroupUsers={handleAddGroupUsers}
        onSearchUsers={handleSearchUsersAssigned}
        onAddUser={handleAddUser}
        onRemoveUser={handleRemoveUser}
        onToggleViolator={handleToggleViolator}
      />
    </main>
  );
};

export default IncidentFormPage;
