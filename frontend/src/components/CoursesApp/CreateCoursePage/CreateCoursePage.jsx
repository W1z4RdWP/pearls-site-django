import { useState, useEffect, useCallback } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  fetchCreateCoursePageData,
  createCourse,
  searchMentors,
  searchQuizzes,
} from '../../../api/courses_api';
import './CreateCoursePage.css';

const MENTORS_TIME_DEFAULT = 2;
const DEFAULT_DEADLINE_DAYS = 7;

const CreateCoursePage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const isIncidentFromUrl = searchParams.get('is_incident') === '1';

  const [pageData, setPageData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [imageFile, setImageFile] = useState(null);
  const [slug, setSlug] = useState('');
  const [finalQuizId, setFinalQuizId] = useState('');
  const [finalQuizName, setFinalQuizName] = useState('');
  const [responsibleMentorId, setResponsibleMentorId] = useState('');
  const [responsibleMentorName, setResponsibleMentorName] = useState('');
  const [mentorsTimeToCheck, setMentorsTimeToCheck] = useState(MENTORS_TIME_DEFAULT);
  const [defaultDeadlineDays, setDefaultDeadlineDays] = useState(DEFAULT_DEADLINE_DAYS);
  const [allowedGroupIds, setAllowedGroupIds] = useState([]);
  const [certificate, setCertificate] = useState(false);
  const [isIncident, setIsIncident] = useState(false);

  const [submitError, setSubmitError] = useState(null);
  const [fieldErrors, setFieldErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [userModalOpen, setUserModalOpen] = useState(false);
  const [quizModalOpen, setQuizModalOpen] = useState(false);
  const [userSearchQuery, setUserSearchQuery] = useState('');
  const [quizSearchQuery, setQuizSearchQuery] = useState('');
  const [userList, setUserList] = useState([]);
  const [quizList, setQuizList] = useState([]);
  const [usersLoading, setUsersLoading] = useState(false);
  const [quizzesLoading, setQuizzesLoading] = useState(false);

  const isIncidentReadonly = pageData?.is_incident ?? false;

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    fetchCreateCoursePageData(isIncidentFromUrl)
      .then((data) => {
        if (!cancelled) {
          setPageData(data);
          setIsIncident(data.is_incident);
        }
      })
      .catch((err) => {
        if (!cancelled) setError(err.message || 'Ошибка загрузки');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, [isIncidentFromUrl]);

  const loadUsers = useCallback(async (query) => {
    setUsersLoading(true);
    try {
      const res = await searchMentors(query);
      setUserList(res.users || []);
    } catch {
      setUserList([]);
    } finally {
      setUsersLoading(false);
    }
  }, []);

  const loadQuizzes = useCallback(async (query) => {
    setQuizzesLoading(true);
    try {
      const res = await searchQuizzes(query);
      setQuizList(res.success ? (res.results || []) : []);
    } catch {
      setQuizList([]);
    } finally {
      setQuizzesLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!userModalOpen) return;
    const t = setTimeout(() => loadUsers(userSearchQuery), 300);
    return () => clearTimeout(t);
  }, [userModalOpen, userSearchQuery, loadUsers]);

  useEffect(() => {
    if (!quizModalOpen) return;
    const t = setTimeout(() => loadQuizzes(quizSearchQuery), 300);
    return () => clearTimeout(t);
  }, [quizModalOpen, quizSearchQuery, loadQuizzes]);

  const handleToggleGroup = useCallback((groupId) => {
    setAllowedGroupIds((prev) =>
      prev.includes(groupId) ? prev.filter((id) => id !== groupId) : [...prev, groupId]
    );
  }, []);

  const handleSubmit = useCallback(
    async (e) => {
      e.preventDefault();
      setSubmitError(null);
      setFieldErrors({});
      setIsSubmitting(true);
      const formData = new FormData();
      formData.append('title', title.trim());
      formData.append('description', description.trim());
      if (imageFile) formData.append('image', imageFile);
      formData.append('slug', slug.trim());
      if (finalQuizId) formData.append('final_quiz', finalQuizId);
      if (responsibleMentorId) formData.append('responsible_mentor', responsibleMentorId);
      formData.append('mentors_time_to_check', String(mentorsTimeToCheck));
      formData.append('default_deadline_days', String(defaultDeadlineDays));
      allowedGroupIds.forEach((id) => formData.append('allowed_groups', String(id)));
      if (certificate) formData.append('certificate', 'on');
      if (isIncident) formData.append('is_incident', 'on');
      if (isIncidentReadonly) formData.append('is_incident_readonly', '1');
      try {
        const res = await createCourse(formData);
        window.location.href = `/courses/course/${res.slug}/`;
      } catch (err) {
        setSubmitError(err.message || 'Ошибка создания курса');
        if (err.errors && typeof err.errors === 'object') setFieldErrors(err.errors);
      } finally {
        setIsSubmitting(false);
      }
    },
    [
      title,
      description,
      imageFile,
      slug,
      finalQuizId,
      responsibleMentorId,
      mentorsTimeToCheck,
      defaultDeadlineDays,
      allowedGroupIds,
      certificate,
      isIncident,
      isIncidentReadonly,
    ]
  );

  const handleCancel = useCallback(() => {
    navigate('/builder/trajectory-management');
  }, [navigate]);

  if (loading && !pageData) {
    return (
      <main className="create-course-page">
        <div className="create-course-page__loading" aria-label="Загрузка">
          Загрузка…
        </div>
      </main>
    );
  }
  if (error) {
    return (
      <main className="create-course-page">
        <div className="create-course-page__error" role="alert">
          {error}
        </div>
      </main>
    );
  }

  const groups = pageData?.groups ?? [];

  return (
    <main className="create-course-page">
      <div className="create-course-page__wrapper">
        <header className="create-course-page__header">
          <h1 className="create-course-page__title">
            Создать курс{isIncidentReadonly ? '-инцидент' : ''}
          </h1>
        </header>

        <form onSubmit={handleSubmit} className="create-course-page__form" noValidate>
          {submitError && (
            <div className="create-course-page__submit-error" role="alert">
              {submitError}
            </div>
          )}

          <section className="create-course-page__section">
            <h2 className="create-course-page__section-title">Основная информация</h2>

            <div className="create-course-page__field">
              <label htmlFor="course-title" className="create-course-page__label">
                Название курса *
              </label>
              <input
                id="course-title"
                type="text"
                className="create-course-page__input"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                aria-invalid={Boolean(fieldErrors.title)}
              />
              {fieldErrors.title && (
                <div className="create-course-page__field-error">{fieldErrors.title[0]}</div>
              )}
            </div>

            <div className="create-course-page__field">
              <label htmlFor="course-description" className="create-course-page__label">
                Описание курса
              </label>
              <textarea
                id="course-description"
                className="create-course-page__textarea"
                rows={6}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                aria-invalid={Boolean(fieldErrors.description)}
              />
              {fieldErrors.description && (
                <div className="create-course-page__field-error">
                  {fieldErrors.description[0]}
                </div>
              )}
            </div>

            <div className="create-course-page__field">
              <label htmlFor="course-image" className="create-course-page__label">
                Изображение курса
              </label>
              <input
                id="course-image"
                type="file"
                accept="image/*"
                className="create-course-page__file"
                onChange={(e) => setImageFile(e.target.files?.[0] ?? null)}
                aria-invalid={Boolean(fieldErrors.image)}
              />
              <span className="create-course-page__help">
                Рекомендуемый размер: 1200x600 пикселей
              </span>
              {fieldErrors.image && (
                <div className="create-course-page__field-error">{fieldErrors.image[0]}</div>
              )}
            </div>
          </section>

          <section className="create-course-page__section">
            <h2 className="create-course-page__section-title">Дополнительно</h2>

            <div className="create-course-page__field">
              <label htmlFor="course-slug" className="create-course-page__label">
                ЧПУ (оставьте пустым для автогенерации)
              </label>
              <input
                id="course-slug"
                type="text"
                className="create-course-page__input"
                value={slug}
                onChange={(e) => setSlug(e.target.value)}
                aria-invalid={Boolean(fieldErrors.slug)}
              />
              {fieldErrors.slug && (
                <div className="create-course-page__field-error">{fieldErrors.slug[0]}</div>
              )}
            </div>

            <div className="create-course-page__field">
              <label className="create-course-page__label">Финальный тест</label>
              <div
                role="button"
                tabIndex={0}
                className="create-course-page__select-field"
                onClick={() => setQuizModalOpen(true)}
                onKeyDown={(e) => e.key === 'Enter' && setQuizModalOpen(true)}
                aria-label="Выберите тест"
              >
                <span className={finalQuizName ? '' : 'create-course-page__placeholder'}>
                  {finalQuizName || 'Выберите тест...'}
                </span>
                <span className="create-course-page__select-icon">&#9660;</span>
              </div>
              {fieldErrors.final_quiz && (
                <div className="create-course-page__field-error">
                  {fieldErrors.final_quiz[0]}
                </div>
              )}
            </div>

            <div className="create-course-page__field">
              <div className="create-course-page__label-row">
                <label className="create-course-page__label">Проверяющий наставник</label>
                <span
                  className="create-course-page__help-icon"
                  tabIndex={0}
                  role="button"
                  aria-label="Подсказка"
                  title="В списке отображаются сотрудники со статусом «Наставник». Этот человек отвечает за проверку и подтверждение корректности выполнения теста обучающегося."
                >
                  ?
                </span>
              </div>
              <div className="create-course-page__mentor-row">
                <div
                  role="button"
                  tabIndex={0}
                  className="create-course-page__select-field"
                  onClick={() => setUserModalOpen(true)}
                  onKeyDown={(e) => e.key === 'Enter' && setUserModalOpen(true)}
                  aria-label="Выберите наставника"
                >
                  <span className={responsibleMentorName ? '' : 'create-course-page__placeholder'}>
                    {responsibleMentorName || 'Выберите пользователя...'}
                  </span>
                  <span className="create-course-page__select-icon">&#9660;</span>
                </div>
                <div className="create-course-page__time-counter">
                  <button
                    type="button"
                    className="create-course-page__time-btn"
                    onClick={() => setMentorsTimeToCheck((v) => Math.max(1, v - 1))}
                    aria-label="Уменьшить"
                  >
                    −
                  </button>
                  <input
                    type="number"
                    min={1}
                    readOnly
                    className="create-course-page__time-input"
                    value={mentorsTimeToCheck}
                    aria-label="Дней на проверку"
                  />
                  <button
                    type="button"
                    className="create-course-page__time-btn"
                    onClick={() => setMentorsTimeToCheck((v) => v + 1)}
                    aria-label="Увеличить"
                  >
                    +
                  </button>
                  <span
                    className="create-course-page__help-icon"
                    tabIndex={0}
                    role="button"
                    aria-label="Подсказка"
                    title="Укажите период, в течение которого наставник должен проверить тест после завершения урока."
                  >
                    ?
                  </span>
                </div>
              </div>
              {fieldErrors.responsible_mentor && (
                <div className="create-course-page__field-error">
                  {fieldErrors.responsible_mentor[0]}
                </div>
              )}
              {fieldErrors.mentors_time_to_check && (
                <div className="create-course-page__field-error">
                  {fieldErrors.mentors_time_to_check[0]}
                </div>
              )}
            </div>

            <div className="create-course-page__field">
              <label htmlFor="course-deadline-days" className="create-course-page__label">
                Срок завершения курса (дней)
              </label>
              <input
                id="course-deadline-days"
                type="number"
                min={1}
                className="create-course-page__input"
                value={defaultDeadlineDays}
                onChange={(e) => setDefaultDeadlineDays(Number(e.target.value) || 7)}
                aria-invalid={Boolean(fieldErrors.default_deadline_days)}
              />
              {fieldErrors.default_deadline_days && (
                <div className="create-course-page__field-error">
                  {fieldErrors.default_deadline_days[0]}
                </div>
              )}
            </div>

            <div className="create-course-page__field">
              <label className="create-course-page__label">Доступен для групп</label>
              <div className="create-course-page__groups">
                {groups.map((g) => (
                  <label key={g.id} className="create-course-page__checkbox-wrap">
                    <input
                      type="checkbox"
                      checked={allowedGroupIds.includes(g.id)}
                      onChange={() => handleToggleGroup(g.id)}
                      className="create-course-page__checkbox"
                    />
                    <span>{g.name}</span>
                  </label>
                ))}
              </div>
              {fieldErrors.allowed_groups && (
                <div className="create-course-page__field-error">
                  {fieldErrors.allowed_groups[0]}
                </div>
              )}
            </div>

            <hr className="create-course-page__hr" />
            <label className="create-course-page__checkbox-wrap">
              <input
                type="checkbox"
                checked={certificate}
                onChange={(e) => setCertificate(e.target.checked)}
                className="create-course-page__checkbox"
              />
              <span>Выдавать сертификат</span>
            </label>
            {fieldErrors.certificate && (
              <div className="create-course-page__field-error">{fieldErrors.certificate[0]}</div>
            )}

            <hr className="create-course-page__hr" />
            <label className="create-course-page__checkbox-wrap">
              <input
                type="checkbox"
                checked={isIncident}
                onChange={(e) => !isIncidentReadonly && setIsIncident(e.target.checked)}
                disabled={isIncidentReadonly}
                className="create-course-page__checkbox"
              />
              <span>Инцидент</span>
            </label>
            {fieldErrors.is_incident && (
              <div className="create-course-page__field-error">{fieldErrors.is_incident[0]}</div>
            )}
          </section>

          <div className="create-course-page__actions">
            <button
              type="submit"
              className="create-course-page__btn create-course-page__btn--primary"
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Создание…' : 'Создать курс'}
            </button>
            <button
              type="button"
              className="create-course-page__btn create-course-page__btn--secondary"
              onClick={handleCancel}
              disabled={isSubmitting}
            >
              Отмена
            </button>
          </div>
        </form>
      </div>

      {/* Модальное окно выбора наставника */}
      {userModalOpen && (
        <div
          className="create-course-page__modal"
          role="dialog"
          aria-modal="true"
          aria-labelledby="user-modal-title"
          onClick={(e) => e.target === e.currentTarget && setUserModalOpen(false)}
        >
          <div className="create-course-page__modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="create-course-page__modal-header">
              <h3 id="user-modal-title">Выберите сотрудника</h3>
              <button
                type="button"
                className="create-course-page__modal-close"
                onClick={() => setUserModalOpen(false)}
                aria-label="Закрыть"
              >
                &times;
              </button>
            </div>
            <div className="create-course-page__modal-body">
              <input
                type="text"
                className="create-course-page__search-input"
                placeholder="Поиск по имени или фамилии..."
                value={userSearchQuery}
                onChange={(e) => setUserSearchQuery(e.target.value)}
                aria-label="Поиск пользователя"
              />
              <div className="create-course-page__list-container">
                {usersLoading ? (
                  <div className="create-course-page__list-loading">Загрузка...</div>
                ) : userList.length === 0 ? (
                  <div className="create-course-page__list-empty">Пользователи не найдены</div>
                ) : (
                  <ul className="create-course-page__list">
                    {userList.map((u) => (
                      <li
                        key={u.id}
                        role="button"
                        tabIndex={0}
                        className="create-course-page__list-item"
                        onClick={() => {
                          setResponsibleMentorId(String(u.id));
                          setResponsibleMentorName(u.full_name || u.username);
                          setUserModalOpen(false);
                        }}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') {
                            setResponsibleMentorId(String(u.id));
                            setResponsibleMentorName(u.full_name || u.username);
                            setUserModalOpen(false);
                          }
                        }}
                      >
                        <span className="create-course-page__list-item-name">{u.full_name}</span>
                        <span className="create-course-page__list-item-meta">@{u.username}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Модальное окно выбора теста */}
      {quizModalOpen && (
        <div
          className="create-course-page__modal"
          role="dialog"
          aria-modal="true"
          aria-labelledby="quiz-modal-title"
          onClick={(e) => e.target === e.currentTarget && setQuizModalOpen(false)}
        >
          <div className="create-course-page__modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="create-course-page__modal-header">
              <h3 id="quiz-modal-title">Выберите тест</h3>
              <button
                type="button"
                className="create-course-page__modal-close"
                onClick={() => setQuizModalOpen(false)}
                aria-label="Закрыть"
              >
                &times;
              </button>
            </div>
            <div className="create-course-page__modal-body">
              <input
                type="text"
                className="create-course-page__search-input"
                placeholder="Поиск по названию теста..."
                value={quizSearchQuery}
                onChange={(e) => setQuizSearchQuery(e.target.value)}
                aria-label="Поиск теста"
              />
              <div className="create-course-page__list-container">
                {quizzesLoading ? (
                  <div className="create-course-page__list-loading">Загрузка...</div>
                ) : (
                  <ul className="create-course-page__list">
                    <li
                      role="button"
                      tabIndex={0}
                      className="create-course-page__list-item create-course-page__list-item--clear"
                      onClick={() => {
                        setFinalQuizId('');
                        setFinalQuizName('');
                        setQuizModalOpen(false);
                      }}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          setFinalQuizId('');
                          setFinalQuizName('');
                          setQuizModalOpen(false);
                        }
                      }}
                    >
                      <span className="create-course-page__list-item-name">
                        — Не назначать финальный тест —
                      </span>
                    </li>
                    {quizList.map((q) => (
                      <li
                        key={q.id}
                        role="button"
                        tabIndex={0}
                        className="create-course-page__list-item"
                        onClick={() => {
                          setFinalQuizId(String(q.id));
                          setFinalQuizName(q.name);
                          setQuizModalOpen(false);
                        }}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') {
                            setFinalQuizId(String(q.id));
                            setFinalQuizName(q.name);
                            setQuizModalOpen(false);
                          }
                        }}
                      >
                        <span className="create-course-page__list-item-name">{q.name}</span>
                        <span className="create-course-page__list-item-meta">
                          {q.questions_count ?? 0} вопросов
                        </span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </main>
  );
};

export default CreateCoursePage;
