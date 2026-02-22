import { useState, useEffect, useCallback } from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import {
  fetchCourseEditData,
  updateCourse,
  searchMentors,
  searchQuizzes,
} from '../../../api/courses_api';
import './EditCoursePage.css';

const MENTORS_TIME_DEFAULT = 2;
const DEFAULT_DEADLINE_DAYS = 7;

const EditCoursePage = () => {
  const { slug } = useParams();
  const navigate = useNavigate();

  const [pageData, setPageData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [imageFile, setImageFile] = useState(null);
  const [slugField, setSlugField] = useState('');
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

  useEffect(() => {
    if (!slug) return;
    let cancelled = false;
    setLoading(true);
    setError(null);
    fetchCourseEditData(slug)
      .then((data) => {
        if (!cancelled) {
          setPageData(data);
          const c = data.course || {};
          setTitle(c.title || '');
          setDescription(c.description || '');
          setSlugField(c.slug || '');
          setFinalQuizId(c.final_quiz ? String(c.final_quiz.id) : '');
          setFinalQuizName(c.final_quiz ? c.final_quiz.name : '');
          setResponsibleMentorId(c.responsible_mentor ? String(c.responsible_mentor.id) : '');
          setResponsibleMentorName(c.responsible_mentor ? c.responsible_mentor.full_name : '');
          setMentorsTimeToCheck(c.mentors_time_to_check ?? MENTORS_TIME_DEFAULT);
          setDefaultDeadlineDays(c.default_deadline_days ?? DEFAULT_DEADLINE_DAYS);
          setAllowedGroupIds(c.allowed_group_ids || []);
          setCertificate(!!c.certificate);
          setIsIncident(!!c.is_incident);
        }
      })
      .catch((err) => {
        if (!cancelled) setError(err.message || 'Ошибка загрузки');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, [slug]);

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
      if (!slug) return;
      setSubmitError(null);
      setFieldErrors({});
      setIsSubmitting(true);
      const formData = new FormData();
      formData.append('title', title.trim());
      formData.append('description', description.trim());
      if (imageFile) formData.append('image', imageFile);
      formData.append('slug', slugField.trim());
      formData.append('final_quiz', finalQuizId || '');
      if (responsibleMentorId) formData.append('responsible_mentor', responsibleMentorId);
      formData.append('mentors_time_to_check', String(mentorsTimeToCheck));
      formData.append('default_deadline_days', String(defaultDeadlineDays));
      allowedGroupIds.forEach((id) => formData.append('allowed_groups', String(id)));
      formData.append('certificate', certificate ? 'on' : '');
      formData.append('is_incident', isIncident ? 'on' : '');
      try {
        const res = await updateCourse(slug, formData);
        navigate(res.redirect_url || `/courses/course/${res.slug}/`);
      } catch (err) {
        setSubmitError(err.message || 'Ошибка сохранения');
        if (err.errors && typeof err.errors === 'object') setFieldErrors(err.errors);
      } finally {
        setIsSubmitting(false);
      }
    },
    [
      slug,
      title,
      description,
      imageFile,
      slugField,
      finalQuizId,
      responsibleMentorId,
      mentorsTimeToCheck,
      defaultDeadlineDays,
      allowedGroupIds,
      certificate,
      isIncident,
      navigate,
    ]
  );

  const courseDetailUrl = pageData?.course_detail_url || (slug ? `/courses/course/${slug}/` : '#');

  if (loading && !pageData) {
    return (
      <main className="edit-course-page">
        <div className="edit-course-page__loading" aria-label="Загрузка">
          Загрузка…
        </div>
      </main>
    );
  }
  if (error) {
    return (
      <main className="edit-course-page">
        <div className="edit-course-page__error" role="alert">
          {error}
        </div>
      </main>
    );
  }
  if (!pageData) {
    return null;
  }

  const groups = pageData.groups ?? [];
  const currentImageUrl = pageData.course?.image_url;

  return (
    <main className="edit-course-page">
      <div className="edit-course-page__wrapper">
        <header className="edit-course-page__header">
          <Link to={courseDetailUrl} className="edit-course-page__back">
            ← Назад
          </Link>
          <h1 className="edit-course-page__title">
            Редактировать курс «{pageData.course?.title || title}»
          </h1>
        </header>

        <form onSubmit={handleSubmit} className="edit-course-page__form" noValidate>
          {submitError && (
            <div className="edit-course-page__submit-error" role="alert">
              {submitError}
            </div>
          )}

          <section className="edit-course-page__section">
            <h2 className="edit-course-page__section-title">Основная информация</h2>

            <div className="edit-course-page__field">
              <label htmlFor="course-title" className="edit-course-page__label">
                Название курса *
              </label>
              <input
                id="course-title"
                type="text"
                className="edit-course-page__input"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                aria-invalid={Boolean(fieldErrors.title)}
              />
              {fieldErrors.title && (
                <div className="edit-course-page__field-error">{fieldErrors.title[0]}</div>
              )}
            </div>

            <div className="edit-course-page__field">
              <label htmlFor="course-description" className="edit-course-page__label">
                Описание курса
              </label>
              <textarea
                id="course-description"
                className="edit-course-page__textarea"
                rows={6}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                aria-invalid={Boolean(fieldErrors.description)}
              />
              {fieldErrors.description && (
                <div className="edit-course-page__field-error">
                  {fieldErrors.description[0]}
                </div>
              )}
            </div>

            <div className="edit-course-page__field">
              <label htmlFor="course-image" className="edit-course-page__label">
                Изображение курса
              </label>
              <input
                id="course-image"
                type="file"
                accept="image/*"
                className="edit-course-page__file"
                onChange={(e) => setImageFile(e.target.files?.[0] ?? null)}
                aria-invalid={Boolean(fieldErrors.image)}
              />
              <span className="edit-course-page__help">
                Рекомендуемый размер: 1200x600 пикселей
              </span>
              {currentImageUrl && (
                <div className="edit-course-page__current-image">
                  <label className="edit-course-page__label">Текущее изображение:</label>
                  <img
                    src={currentImageUrl}
                    alt="Текущее изображение курса"
                    className="edit-course-page__current-image-img"
                  />
                </div>
              )}
              {fieldErrors.image && (
                <div className="edit-course-page__field-error">{fieldErrors.image[0]}</div>
              )}
            </div>
          </section>

          <section className="edit-course-page__section">
            <h2 className="edit-course-page__section-title">Настройки курса</h2>

            <div className="edit-course-page__field">
              <label htmlFor="course-slug" className="edit-course-page__label">
                ЧПУ (оставьте пустым для автогенерации)
              </label>
              <input
                id="course-slug"
                type="text"
                className="edit-course-page__input"
                value={slugField}
                onChange={(e) => setSlugField(e.target.value)}
                aria-invalid={Boolean(fieldErrors.slug)}
              />
              {fieldErrors.slug && (
                <div className="edit-course-page__field-error">{fieldErrors.slug[0]}</div>
              )}
            </div>

            <div className="edit-course-page__field">
              <label className="edit-course-page__label">Финальный тест</label>
              <div
                role="button"
                tabIndex={0}
                className="edit-course-page__select-field"
                onClick={() => setQuizModalOpen(true)}
                onKeyDown={(e) => e.key === 'Enter' && setQuizModalOpen(true)}
                aria-label="Выберите тест"
              >
                <span className={finalQuizName ? '' : 'edit-course-page__placeholder'}>
                  {finalQuizName || 'Выберите тест...'}
                </span>
                <span className="edit-course-page__select-icon">&#9660;</span>
              </div>
              {fieldErrors.final_quiz && (
                <div className="edit-course-page__field-error">
                  {fieldErrors.final_quiz[0]}
                </div>
              )}
            </div>

            <div className="edit-course-page__field">
              <div className="edit-course-page__label-row">
                <label className="edit-course-page__label">Проверяющий наставник</label>
                <span
                  className="edit-course-page__help-icon"
                  tabIndex={0}
                  role="button"
                  aria-label="Подсказка"
                  title="В списке отображаются сотрудники со статусом «Наставник». Этот человек отвечает за проверку и подтверждение корректности выполнения теста обучающегося. Поле обязательное для заполнения."
                >
                  ?
                </span>
              </div>
              <div className="edit-course-page__mentor-row">
                <div
                  role="button"
                  tabIndex={0}
                  className="edit-course-page__select-field"
                  onClick={() => setUserModalOpen(true)}
                  onKeyDown={(e) => e.key === 'Enter' && setUserModalOpen(true)}
                  aria-label="Выберите наставника"
                >
                  <span className={responsibleMentorName ? '' : 'edit-course-page__placeholder'}>
                    {responsibleMentorName || 'Выберите пользователя...'}
                  </span>
                  <span className="edit-course-page__select-icon">&#9660;</span>
                </div>
                <div className="edit-course-page__time-counter">
                  <button
                    type="button"
                    className="edit-course-page__time-btn"
                    onClick={() => setMentorsTimeToCheck((v) => Math.max(1, v - 1))}
                    aria-label="Уменьшить"
                  >
                    −
                  </button>
                  <input
                    type="number"
                    min={1}
                    readOnly
                    className="edit-course-page__time-input"
                    value={mentorsTimeToCheck}
                    aria-label="Дней на проверку"
                  />
                  <button
                    type="button"
                    className="edit-course-page__time-btn"
                    onClick={() => setMentorsTimeToCheck((v) => v + 1)}
                    aria-label="Увеличить"
                  >
                    +
                  </button>
                  <span
                    className="edit-course-page__help-icon"
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
                <div className="edit-course-page__field-error">
                  {fieldErrors.responsible_mentor[0]}
                </div>
              )}
              {fieldErrors.mentors_time_to_check && (
                <div className="edit-course-page__field-error">
                  {fieldErrors.mentors_time_to_check[0]}
                </div>
              )}
            </div>

            <div className="edit-course-page__field">
              <label htmlFor="course-deadline-days" className="edit-course-page__label">
                Срок завершения курса (дней)
              </label>
              <input
                id="course-deadline-days"
                type="number"
                min={1}
                className="edit-course-page__input"
                value={defaultDeadlineDays}
                onChange={(e) => setDefaultDeadlineDays(Number(e.target.value) || 7)}
                aria-invalid={Boolean(fieldErrors.default_deadline_days)}
              />
              {fieldErrors.default_deadline_days && (
                <div className="edit-course-page__field-error">
                  {fieldErrors.default_deadline_days[0]}
                </div>
              )}
            </div>

            <div className="edit-course-page__field">
              <label className="edit-course-page__label">Доступен для групп</label>
              <div className="edit-course-page__groups">
                {groups.map((g) => (
                  <label key={g.id} className="edit-course-page__checkbox-wrap">
                    <input
                      type="checkbox"
                      checked={allowedGroupIds.includes(g.id)}
                      onChange={() => handleToggleGroup(g.id)}
                      className="edit-course-page__checkbox"
                    />
                    <span>{g.name}</span>
                  </label>
                ))}
              </div>
              {fieldErrors.allowed_groups && (
                <div className="edit-course-page__field-error">
                  {fieldErrors.allowed_groups[0]}
                </div>
              )}
            </div>

            <hr className="edit-course-page__hr" />
            <label className="edit-course-page__checkbox-wrap">
              <input
                type="checkbox"
                checked={certificate}
                onChange={(e) => setCertificate(e.target.checked)}
                className="edit-course-page__checkbox"
              />
              <span>Выдавать сертификат</span>
            </label>
            {fieldErrors.certificate && (
              <div className="edit-course-page__field-error">{fieldErrors.certificate[0]}</div>
            )}

            <hr className="edit-course-page__hr" />
            <label className="edit-course-page__checkbox-wrap">
              <input
                type="checkbox"
                checked={isIncident}
                onChange={(e) => setIsIncident(e.target.checked)}
                className="edit-course-page__checkbox"
              />
              <span>Инцидент</span>
            </label>
            {fieldErrors.is_incident && (
              <div className="edit-course-page__field-error">{fieldErrors.is_incident[0]}</div>
            )}
          </section>

          <div className="edit-course-page__actions">
            <button
              type="submit"
              className="edit-course-page__btn edit-course-page__btn--primary"
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Сохранение…' : 'Сохранить изменения'}
            </button>
            <Link
              to={courseDetailUrl}
              className="edit-course-page__btn edit-course-page__btn--secondary"
            >
              Отмена
            </Link>
          </div>
        </form>
      </div>

      {/* Модальное окно выбора наставника */}
      {userModalOpen && (
        <div
          className="edit-course-page__modal"
          role="dialog"
          aria-modal="true"
          aria-labelledby="edit-user-modal-title"
        >
          <div className="edit-course-page__modal-content">
            <div className="edit-course-page__modal-header">
              <h3 id="edit-user-modal-title">Выберите сотрудника</h3>
              <button
                type="button"
                className="edit-course-page__modal-close"
                onClick={() => setUserModalOpen(false)}
                aria-label="Закрыть"
              >
                &times;
              </button>
            </div>
            <div className="edit-course-page__modal-body">
              <input
                type="text"
                className="edit-course-page__search-input"
                placeholder="Поиск по имени или фамилии..."
                value={userSearchQuery}
                onChange={(e) => setUserSearchQuery(e.target.value)}
                aria-label="Поиск пользователя"
              />
              <div className="edit-course-page__list-container">
                {usersLoading ? (
                  <div className="edit-course-page__list-loading">Загрузка...</div>
                ) : userList.length === 0 ? (
                  <div className="edit-course-page__list-empty">Пользователи не найдены</div>
                ) : (
                  <ul className="edit-course-page__list">
                    {userList.map((u) => (
                      <li
                        key={u.id}
                        role="button"
                        tabIndex={0}
                        className="edit-course-page__list-item"
                        onClick={() => {
                          setResponsibleMentorId(String(u.id));
                          setResponsibleMentorName(u.full_name || u.username);
                          setUserModalOpen(false);
                        }}
                        onKeyDown={(e) =>
                          e.key === 'Enter' &&
                          (setResponsibleMentorId(String(u.id)),
                            setResponsibleMentorName(u.full_name || u.username),
                            setUserModalOpen(false))
                        }
                      >
                        <span className="edit-course-page__list-item-name">{u.full_name}</span>
                        <span className="edit-course-page__list-item-meta">@{u.username}</span>
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
          className="edit-course-page__modal"
          role="dialog"
          aria-modal="true"
          aria-labelledby="edit-quiz-modal-title"
        >
          <div className="edit-course-page__modal-content">
            <div className="edit-course-page__modal-header">
              <h3 id="edit-quiz-modal-title">Выберите тест</h3>
              <button
                type="button"
                className="edit-course-page__modal-close"
                onClick={() => setQuizModalOpen(false)}
                aria-label="Закрыть"
              >
                &times;
              </button>
            </div>
            <div className="edit-course-page__modal-body">
              <input
                type="text"
                className="edit-course-page__search-input"
                placeholder="Поиск по названию теста..."
                value={quizSearchQuery}
                onChange={(e) => setQuizSearchQuery(e.target.value)}
                aria-label="Поиск теста"
              />
              <div className="edit-course-page__list-container">
                {quizzesLoading ? (
                  <div className="edit-course-page__list-loading">Загрузка...</div>
                ) : (
                  <ul className="edit-course-page__list">
                    <li
                      role="button"
                      tabIndex={0}
                      className="edit-course-page__list-item edit-course-page__list-item--clear"
                      onClick={() => {
                        setFinalQuizId('');
                        setFinalQuizName('');
                        setQuizModalOpen(false);
                      }}
                      onKeyDown={(e) =>
                        e.key === 'Enter' &&
                        (setFinalQuizId(''), setFinalQuizName(''), setQuizModalOpen(false))
                      }
                    >
                      <span className="edit-course-page__list-item-name">
                        — Не назначать финальный тест —
                      </span>
                    </li>
                    {quizList.map((q) => (
                      <li
                        key={q.id}
                        role="button"
                        tabIndex={0}
                        className="edit-course-page__list-item"
                        onClick={() => {
                          setFinalQuizId(String(q.id));
                          setFinalQuizName(q.name);
                          setQuizModalOpen(false);
                        }}
                        onKeyDown={(e) =>
                          e.key === 'Enter' &&
                          (setFinalQuizId(String(q.id)),
                            setFinalQuizName(q.name),
                            setQuizModalOpen(false))
                        }
                      >
                        <span className="edit-course-page__list-item-name">{q.name}</span>
                        <span className="edit-course-page__list-item-meta">
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

export default EditCoursePage;
