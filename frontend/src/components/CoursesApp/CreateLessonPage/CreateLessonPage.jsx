import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { fetchCreateLessonPageData, createLesson } from '../../../api/courses_api';
import './CreateLessonPage.css';

const CreateLessonPage = () => {
  const { courseSlug } = useParams();
  const navigate = useNavigate();
  const [pageData, setPageData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [requiredTime, setRequiredTime] = useState(7);
  const [courseIds, setCourseIds] = useState([]);

  const [submitError, setSubmitError] = useState(null);
  const [fieldErrors, setFieldErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      if (!courseSlug) {
        setError('Не указан курс');
        setLoading(false);
        return;
      }
      try {
        const data = await fetchCreateLessonPageData(courseSlug);
        if (cancelled) return;
        setPageData(data);
        const currentId = data.course?.id;
        setCourseIds(currentId != null ? [currentId] : []);
      } catch (err) {
        if (!cancelled) {
          setError(err.message || 'Не удалось загрузить данные');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, [courseSlug]);

  const handleCourseIdsChange = useCallback((e) => {
    const options = e.target.options;
    const selected = [];
    for (let i = 0; i < options.length; i++) {
      if (options[i].selected) selected.push(Number(options[i].value));
    }
    setCourseIds(selected);
  }, []);

  const handleSubmit = useCallback(
    async (e) => {
      e.preventDefault();
      setSubmitError(null);
      setFieldErrors({});
      const trimmedTitle = title.trim();
      if (!trimmedTitle) {
        setFieldErrors({ title: ['Укажите название урока'] });
        return;
      }
      setIsSubmitting(true);
      try {
        const result = await createLesson(courseSlug, {
          title: trimmedTitle,
          content: content.trim(),
          required_time: requiredTime,
          course_ids: courseIds.length > 0 ? courseIds : undefined,
        });
        if (result.redirect_url) {
          window.location.href = result.redirect_url;
        } else {
          navigate(`/courses/course/${pageData?.course?.slug || courseSlug}/`);
        }
      } catch (err) {
        setSubmitError(err.message || 'Ошибка создания урока');
        if (err.errors && typeof err.errors === 'object') {
          setFieldErrors(err.errors);
        }
      } finally {
        setIsSubmitting(false);
      }
    },
    [title, content, requiredTime, courseIds, courseSlug, navigate, pageData?.course?.slug]
  );

  const handleCancel = useCallback(() => {
    if (pageData?.course?.slug) {
      window.location.href = `/courses/course/${pageData.course.slug}/`;
    } else {
      navigate(-1);
    }
  }, [navigate, pageData?.course?.slug]);

  if (loading) {
    return (
      <main className="create-lesson-page">
        <div className="create-lesson-page__loading">Загрузка…</div>
      </main>
    );
  }

  if (error || !pageData) {
    return (
      <main className="create-lesson-page">
        <div className="create-lesson-page__error" role="alert">
          {error || 'Данные не загружены'}
        </div>
      </main>
    );
  }

  const { course, courses = [] } = pageData;

  return (
    <main className="create-lesson-page">
      <section className="create-lesson-page__section content-section">
        <h1 className="create-lesson-page__title">
          Создать урок для курса {course?.title}
        </h1>
        <form onSubmit={handleSubmit} className="create-lesson-form" noValidate>
          {submitError && (
            <div className="create-lesson-form__error" role="alert">
              {submitError}
            </div>
          )}

          <div className="create-lesson-form__group">
            <label htmlFor="lesson-title" className="create-lesson-form__label">
              Название урока *
            </label>
            <input
              id="lesson-title"
              type="text"
              className="create-lesson-form__input"
              placeholder="Введите название урока"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              aria-invalid={Boolean(fieldErrors.title)}
            />
            {fieldErrors.title && (
              <div className="create-lesson-form__field-error">
                {fieldErrors.title[0]}
              </div>
            )}
          </div>

          <div className="create-lesson-form__group">
            <label htmlFor="lesson-content" className="create-lesson-form__label">
              Содержание
            </label>
            <textarea
              id="lesson-content"
              className="create-lesson-form__textarea"
              rows={12}
              placeholder="Текст урока (поддерживается HTML)"
              value={content}
              onChange={(e) => setContent(e.target.value)}
              aria-invalid={Boolean(fieldErrors.content)}
            />
            {fieldErrors.content && (
              <div className="create-lesson-form__field-error">
                {fieldErrors.content[0]}
              </div>
            )}
          </div>

          <div className="create-lesson-form__group">
            <label htmlFor="lesson-required-time" className="create-lesson-form__label">
              Необходимое время (минуты)
            </label>
            <input
              id="lesson-required-time"
              type="number"
              min={1}
              max={999}
              className="create-lesson-form__input"
              value={requiredTime}
              onChange={(e) => setRequiredTime(Number(e.target.value) || 7)}
              aria-invalid={Boolean(fieldErrors.required_time)}
            />
            <p className="create-lesson-form__help">
              Время в минутах, необходимое для прохождения урока
            </p>
            {fieldErrors.required_time && (
              <div className="create-lesson-form__field-error">
                {fieldErrors.required_time[0]}
              </div>
            )}
          </div>

          {courses.length > 0 && (
            <div className="create-lesson-form__group">
              <label htmlFor="lesson-courses" className="create-lesson-form__label">
                Выберите курсы, куда добавить урок
              </label>
              <select
                id="lesson-courses"
                multiple
                className="create-lesson-form__select create-lesson-form__select--multiple"
                value={courseIds.map(String)}
                onChange={handleCourseIdsChange}
                aria-invalid={Boolean(fieldErrors.courses)}
              >
                {courses.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.title}
                  </option>
                ))}
              </select>
              <p className="create-lesson-form__help">
                Удерживайте Ctrl (Cmd), чтобы выбрать несколько курсов
              </p>
              {fieldErrors.courses && (
                <div className="create-lesson-form__field-error">
                  {fieldErrors.courses[0]}
                </div>
              )}
            </div>
          )}

          <div className="create-lesson-form__actions">
            <button
              type="submit"
              className="create-lesson-form__btn create-lesson-form__btn--primary"
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Создание…' : 'Создать урок'}
            </button>
            <button
              type="button"
              className="create-lesson-form__btn create-lesson-form__btn--secondary"
              onClick={handleCancel}
              disabled={isSubmitting}
            >
              Отмена
            </button>
          </div>
        </form>
      </section>
    </main>
  );
};

export default CreateLessonPage;
