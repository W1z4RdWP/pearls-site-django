import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { fetchEditLessonData, submitEditLesson } from '../../../api/courses_api';
import './EditLessonPage.css';

const EditLessonPage = () => {
  const { lessonId } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [formErrors, setFormErrors] = useState(null);

  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [order, setOrder] = useState(1);
  const [requiredTime, setRequiredTime] = useState(7);
  const [courseIds, setCourseIds] = useState([]);
  const [finalQuizId, setFinalQuizId] = useState(null);

  const loadData = useCallback(async () => {
    if (!lessonId) return;
    setLoading(true);
    setError(null);
    try {
      const result = await fetchEditLessonData(Number(lessonId));
      setData(result);
      setTitle(result.lesson.title);
      setContent(result.lesson.content || '');
      setOrder(result.lesson.order);
      setRequiredTime(result.lesson.required_time ?? 7);
      setCourseIds(result.lesson.course_ids || []);
      setFinalQuizId(result.lesson.final_quiz_id ?? null);
    } catch (err) {
      setError(err.message || 'Ошибка загрузки данных');
    } finally {
      setLoading(false);
    }
  }, [lessonId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  useEffect(() => {
    if (data?.lesson?.title) {
      document.title = `Редактирование урока: ${data.lesson.title}`;
    }
    return () => { document.title = 'Главная'; };
  }, [data?.lesson?.title]);

  const handleCourseIdsChange = (e) => {
    const options = e.target.options;
    const selected = [];
    for (let i = 0; i < options.length; i++) {
      if (options[i].selected) selected.push(Number(options[i].value));
    }
    setCourseIds(selected);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setFormErrors(null);
    setSubmitting(true);
    try {
      const result = await submitEditLesson(Number(lessonId), {
        title: title.trim(),
        content,
        order: Number(order) || 1,
        required_time: Math.max(1, Math.min(999, Number(requiredTime) || 7)),
        course_ids: courseIds.length > 0 ? courseIds : (data?.lesson?.course_ids || []),
        final_quiz_id: finalQuizId || null,
      });
      if (result.success && result.redirect_url) {
        navigate(result.redirect_url);
      }
    } catch (err) {
      if (err.errors) {
        setFormErrors(err.errors);
      } else {
        setFormErrors({ _: [err.message || 'Ошибка сохранения'] });
      }
    } finally {
      setSubmitting(false);
    }
  };

  const handleCancel = () => {
    if (data?.cancel_url) {
      navigate(data.cancel_url);
    } else {
      navigate(-1);
    }
  };

  if (loading) {
    return (
      <main className="edit-lesson-page" aria-label="Загрузка формы редактирования урока">
        <div className="edit-lesson-page__container">
          <p className="edit-lesson-page__loading" aria-live="polite">Загрузка…</p>
        </div>
      </main>
    );
  }

  if (error) {
    return (
      <main className="edit-lesson-page" aria-label="Ошибка">
        <div className="edit-lesson-page__container">
          <p className="edit-lesson-page__error" role="alert">{error}</p>
        </div>
      </main>
    );
  }

  if (!data) return null;

  const courseTitle = data.course?.title || 'курс';

  return (
    <main className="edit-lesson-page" aria-label="Редактирование урока">
      <div className="edit-lesson-page__container">
        <section className="edit-lesson-page__section content-section">
          <h2 className="edit-lesson-page__title">
            Редактирование урока в курсе {courseTitle}
          </h2>

          <form
            className="edit-lesson-page__form"
            onSubmit={handleSubmit}
            noValidate
          >
            {formErrors && (
              <div className="edit-lesson-page__form-errors" role="alert">
                {Object.entries(formErrors).map(([field, messages]) => (
                  <div key={field}>
                    {messages.map((msg, i) => (
                      <p key={i} className="edit-lesson-page__form-error-msg">{msg}</p>
                    ))}
                  </div>
                ))}
              </div>
            )}

            <div className="edit-lesson-page__field mb-3">
              <label htmlFor="edit-lesson-title" className="edit-lesson-page__label">
                Название урока
              </label>
              <input
                id="edit-lesson-title"
                type="text"
                className="edit-lesson-page__input"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                maxLength={200}
                required
                aria-required="true"
              />
            </div>

            <div className="edit-lesson-page__field mb-3">
              <label htmlFor="edit-lesson-content" className="edit-lesson-page__label">
                Содержимое
              </label>
              <textarea
                id="edit-lesson-content"
                className="edit-lesson-page__textarea edit-lesson-page__textarea--content"
                value={content}
                onChange={(e) => setContent(e.target.value)}
                rows={14}
                aria-describedby="edit-lesson-content-hint"
              />
              <span id="edit-lesson-content-hint" className="edit-lesson-page__hint">
                Поддерживается HTML. Для вставки видео используйте корректные iframe.
              </span>
            </div>

            <div className="edit-lesson-page__row">
              <div className="edit-lesson-page__field edit-lesson-page__field--inline">
                <label htmlFor="edit-lesson-order" className="edit-lesson-page__label">
                  Порядок
                </label>
                <input
                  id="edit-lesson-order"
                  type="number"
                  min={1}
                  className="edit-lesson-page__input edit-lesson-page__input--number"
                  value={order}
                  onChange={(e) => setOrder(e.target.value)}
                />
              </div>
              <div className="edit-lesson-page__field edit-lesson-page__field--inline">
                <label htmlFor="edit-lesson-required-time" className="edit-lesson-page__label">
                  Необходимое время (минуты)
                </label>
                <input
                  id="edit-lesson-required-time"
                  type="number"
                  min={1}
                  max={999}
                  className="edit-lesson-page__input edit-lesson-page__input--number"
                  value={requiredTime}
                  onChange={(e) => setRequiredTime(e.target.value)}
                />
              </div>
            </div>

            <div className="edit-lesson-page__field mb-3">
              <label htmlFor="edit-lesson-courses" className="edit-lesson-page__label">
                Выберите курсы, куда добавить урок
              </label>
              <select
                id="edit-lesson-courses"
                multiple
                className="edit-lesson-page__select edit-lesson-page__select--multiple"
                value={courseIds.map(String)}
                onChange={handleCourseIdsChange}
                aria-describedby="edit-lesson-courses-hint"
              >
                {(data.courses_choices || []).map((c) => (
                  <option key={c.id} value={c.id}>{c.title}</option>
                ))}
              </select>
              <span id="edit-lesson-courses-hint" className="edit-lesson-page__hint">
                Удерживайте Ctrl (Cmd на Mac), чтобы выбрать несколько курсов.
              </span>
            </div>

            <div className="edit-lesson-page__button-group button-group mt-4">
              <button
                type="submit"
                className="edit-lesson-page__btn edit-lesson-page__btn--primary"
                disabled={submitting}
                aria-busy={submitting}
              >
                {submitting ? 'Сохранение…' : 'Сохранить изменения'}
              </button>
              <button
                type="button"
                className="edit-lesson-page__btn edit-lesson-page__btn--secondary"
                onClick={handleCancel}
                disabled={submitting}
              >
                Отмена
              </button>
            </div>
          </form>
        </section>
      </div>
    </main>
  );
};

export default EditLessonPage;
