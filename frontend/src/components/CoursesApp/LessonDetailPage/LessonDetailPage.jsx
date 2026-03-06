import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  fetchLessonDetail,
  completeLesson,
  deleteLesson,
} from '../../../api/courses_api';
import './LessonDetailPage.css';

const METRICS_VIDEO_RU = 'https://kinescope.io/embed/6jhMqUizYEgMyMDYb6bo2g';
const METRICS_VIDEO_KZ = 'https://kinescope.io/embed/cSgZQgbtFC1AtNdYXaVKbV';

const LessonDetailPage = () => {
  const { courseSlug, lessonId } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [confirmationChecked, setConfirmationChecked] = useState(false);
  const [showContinueModal, setShowContinueModal] = useState(false);
  const [submitLoading, setSubmitLoading] = useState(false);

  const loadData = useCallback(async () => {
    if (!courseSlug || !lessonId) return;
    setLoading(true);
    setError(null);
    try {
      const searchParams = new URLSearchParams(window.location.search);
      const params = {};
      if (searchParams.get('quiz_completed') === '1') params.quiz_completed = '1';
      const result = await fetchLessonDetail(courseSlug, Number(lessonId), params);
      if (result.error === 'redirect' && result.redirect_url) {
        window.location.href = result.redirect_url;
        return;
      }
      setData(result);
    } catch (err) {
      if (err.redirect_url) {
        window.location.href = err.redirect_url;
        return;
      }
      setError(err.message || 'Ошибка загрузки урока');
    } finally {
      setLoading(false);
    }
  }, [courseSlug, lessonId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  useEffect(() => {
    if (data?.lesson?.title) {
      document.title = data.lesson.title;
    }
    return () => {
      document.title = 'Главная';
    };
  }, [data?.lesson?.title]);

  const handleCompleteClick = () => {
    if (data?.is_dental_checkup_course) {
      window.location.href = '/courses/metrics/';
      return;
    }
    setShowContinueModal(true);
  };

  const getContinuePayload = () => {
    if (!data) return {};
    const { lesson_quiz, lesson_quiz_passed, next_material, is_last_lesson } = data;
    if (lesson_quiz && !lesson_quiz_passed) {
      return { go_to_quiz: lesson_quiz.id };
    }
    if (is_last_lesson) return {};
    if (next_material?.type === 'quiz') return { go_to_quiz: next_material.id };
    if (next_material?.type === 'homework') return { go_to_homework: next_material.id };
    return { continue_learning: true };
  };

  const handleContinueConfirm = async () => {
    setSubmitLoading(true);
    try {
      const payload = getContinuePayload();
      const result = await completeLesson(courseSlug, Number(lessonId), payload);
      setShowContinueModal(false);
      if (result?.redirect_url) {
        window.location.href = result.redirect_url;
      } else {
        navigate(`/courses/course/${courseSlug}/`);
      }
    } catch (err) {
      alert(err.message || 'Ошибка завершения урока');
    } finally {
      setSubmitLoading(false);
    }
  };

  const handleRest = async () => {
    setSubmitLoading(true);
    try {
      const result = await completeLesson(courseSlug, Number(lessonId), {
        return_to_course: true,
      });
      setShowContinueModal(false);
      if (result?.redirect_url) {
        window.location.href = result.redirect_url;
      } else {
        navigate(`/courses/course/${courseSlug}/`);
      }
    } catch (err) {
      alert(err.message || 'Ошибка');
    } finally {
      setSubmitLoading(false);
    }
  };

  const handleDeleteLesson = async () => {
    if (!window.confirm('Вы уверены, что хотите удалить этот урок из курса?')) return;
    try {
      const result = await deleteLesson(Number(lessonId));
      if (result?.redirect_url) {
        window.location.href = result.redirect_url;
      } else {
        navigate('/');
      }
    } catch (err) {
      alert(err.message || 'Ошибка удаления');
    }
  };

  if (loading) {
    return (
      <main className="lesson-detail-page" aria-label="Загрузка урока">
        <div className="lesson-detail-page__container">
          <p className="lesson-detail-page__loading" aria-live="polite">
            Загрузка…
          </p>
        </div>
      </main>
    );
  }

  if (error && !data) {
    return (
      <main className="lesson-detail-page" aria-label="Ошибка">
        <div className="lesson-detail-page__container">
          <p className="lesson-detail-page__error" role="alert">
            {error}
          </p>
          <button
            type="button"
            className="lesson-detail-page__back-btn"
            onClick={() => navigate(`/courses/course/${courseSlug}/`)}
          >
            Вернуться к курсу
          </button>
        </div>
      </main>
    );
  }

  if (!data) return null;

  const {
    course,
    lesson,
    previous_lesson,
    next_lesson,
    next_material,
    is_dental_checkup_course,
    is_first_lesson,
    is_metrics_lesson,
    is_metrics_kz_lesson,
    is_external_user,
    user_country,
    lesson_quiz,
    lesson_quiz_passed,
    quiz_just_completed,
    is_last_lesson,
    is_staff,
  } = data;

  const courseUrl = `/courses/course/${course.slug}/`;
  const lessonUrl = (id) => `/courses/course/${course.slug}/lesson/${id}/`;

  const renderContent = () => {
    if (is_metrics_lesson) {
      const embedUrl =
        is_external_user && user_country === 'Казахстан'
          ? METRICS_VIDEO_KZ
          : METRICS_VIDEO_RU;
      return (
        <div className="lesson-detail-page__video-wrapper lesson-detail-page__video-wrapper--16x9">
          <iframe
            src={embedUrl}
            title="Видео урока"
            allow="autoplay; fullscreen; picture-in-picture; encrypted-media; gyroscope; accelerometer; clipboard-write; screen-wake-lock;"
            frameBorder="0"
            allowFullScreen
            className="lesson-detail-page__video-iframe"
          />
        </div>
      );
    }
    if (is_metrics_kz_lesson) {
      return (
        <div className="lesson-detail-page__video-wrapper lesson-detail-page__video-wrapper--16x9">
          <iframe
            src={METRICS_VIDEO_KZ}
            title="Видео урока"
            allow="autoplay; fullscreen; picture-in-picture; encrypted-media; gyroscope; accelerometer; clipboard-write; screen-wake-lock;"
            frameBorder="0"
            allowFullScreen
            className="lesson-detail-page__video-iframe"
          />
        </div>
      );
    }
    return (
      <>
        <div
          className="lesson-detail-page__content ck-content"
          dangerouslySetInnerHTML={{ __html: lesson.content || '' }}
        />
        {lesson.video_id && (
          <div className="lesson-detail-page__video-wrapper lesson-detail-page__rutube">
            <iframe
              src={`https://rutube.ru/video/embed/${lesson.video_id}/`}
              title="Видео Rutube"
              frameBorder="0"
              allowFullScreen
            />
          </div>
        )}
      </>
    );
  };

  const modalIcon =
    next_material?.type === 'quiz'
      ? 'fa-clipboard-check'
      : next_material?.type === 'homework'
        ? 'fa-pencil-alt'
        : 'fa-question-circle';
  const modalTitle =
    lesson_quiz && !lesson_quiz_passed
      ? 'Для завершения урока необходимо пройти связанный тест!'
      : is_last_lesson
        ? 'Урок завершен! Это был последний урок курса.'
        : next_material?.type === 'quiz'
          ? 'Урок завершен! Следующий этап - тест.'
          : next_material?.type === 'homework'
            ? 'Урок завершен! Следующий этап - задание.'
            : 'Урок завершен! Хотите продолжить обучение?';
  const continueButtonText =
    lesson_quiz && !lesson_quiz_passed
      ? 'Перейти к тесту'
      : is_last_lesson
        ? 'Вернуться к курсу'
        : next_material?.type === 'quiz'
          ? 'Перейти к тесту'
          : next_material?.type === 'homework'
            ? 'Перейти к заданию'
            : 'Да, продолжаем!';

  return (
    <main className="lesson-detail-page">
      <div className="lesson-detail-page__container">
        <nav className="lesson-detail-page__nav" aria-label="Навигация по уроку">
          <a
            href={courseUrl}
            className="lesson-detail-page__nav-btn lesson-detail-page__nav-btn--secondary"
          >
            <i className="fa fa-arrow-left" aria-hidden="true" /> Вернуться к курсу
          </a>
          {previous_lesson ? (
            <a
              href={lessonUrl(previous_lesson.id)}
              className="lesson-detail-page__nav-btn lesson-detail-page__nav-btn--primary"
            >
              ← {previous_lesson.title}
            </a>
          ) : (
            <span
              className="lesson-detail-page__nav-btn lesson-detail-page__nav-btn--disabled"
              aria-disabled="true"
            >
              ← Это первый урок
            </span>
          )}
          {is_dental_checkup_course && is_first_lesson ? (
            <a
              href="/courses/metrics/"
              className="lesson-detail-page__nav-btn lesson-detail-page__nav-btn--primary"
            >
              Форма метрик эффективности →
            </a>
          ) : lesson_quiz && !lesson_quiz_passed ? (
            <a
              href={`/quizzes/${lesson_quiz.id}/start/?course_slug=${course.slug}&lesson_id=${lesson.id}`}
              className="lesson-detail-page__nav-btn lesson-detail-page__nav-btn--success"
            >
              <i className="fa fa-graduation-cap" aria-hidden="true" /> Перейти к
              тесту: {lesson_quiz.name} →
            </a>
          ) : next_material?.type === 'homework' ? (
            <a
              href={`/quizzes/homework/${next_material.id}/submit/?course_slug=${course.slug}`}
              className="lesson-detail-page__nav-btn lesson-detail-page__nav-btn--warning"
            >
              <i className="fa fa-pencil-alt" aria-hidden="true" /> Перейти к заданию:{' '}
              {next_material.title} →
            </a>
          ) : next_lesson ? (
            <a
              href={lessonUrl(next_lesson.id)}
              className="lesson-detail-page__nav-btn lesson-detail-page__nav-btn--primary"
            >
              {next_lesson.title} →
            </a>
          ) : (
            <span
              className="lesson-detail-page__nav-btn lesson-detail-page__nav-btn--disabled"
              aria-disabled="true"
            >
              Это последний урок →
            </span>
          )}
        </nav>

        <section className="lesson-detail-page__content-section">
          <h1 className="lesson-detail-page__course-title">{course.title}</h1>
          <h2 className="lesson-detail-page__lesson-title">{lesson.title}</h2>

          {quiz_just_completed && lesson_quiz && lesson_quiz_passed && (
            <div
              className="lesson-detail-page__alert lesson-detail-page__alert--success"
              role="status"
            >
              <i className="fa fa-check-circle" aria-hidden="true" />{' '}
              <strong>Тест успешно пройден!</strong> Теперь вы можете завершить урок.
            </div>
          )}

          <div className="lesson-detail-page__body">{renderContent()}</div>

          {!is_dental_checkup_course && !is_staff && (
            <div className="lesson-detail-page__confirmation">
              <label className="lesson-detail-page__confirmation-label">
                <input
                  type="checkbox"
                  checked={confirmationChecked}
                  onChange={(e) => setConfirmationChecked(e.target.checked)}
                  className="lesson-detail-page__confirmation-input"
                  aria-describedby="confirmation-desc"
                />
                <span id="confirmation-desc">
                  Подтверждаю ознакомление с учебным материалом и полное понимание
                  его содержания. Дополнительных вопросов не имеется.
                </span>
              </label>
            </div>
          )}
        </section>

        <div className="lesson-detail-page__actions">
          {is_dental_checkup_course ? (
            <a href="/courses/metrics/" className="lesson-detail-page__btn lesson-detail-page__btn--complete">
              <i className="fa fa-arrow-right" aria-hidden="true" /> Перейти к
              заполнению метрик
            </a>
          ) : (is_staff || confirmationChecked) ? (
            <button
              type="button"
              className="lesson-detail-page__btn lesson-detail-page__btn--complete"
              onClick={handleCompleteClick}
            >
              <i className="fa fa-check" aria-hidden="true" /> Завершить урок
            </button>
          ) : null}
          {is_staff && (
            <>
              <button
                type="button"
                className="lesson-detail-page__btn lesson-detail-page__btn--delete"
                onClick={handleDeleteLesson}
              >
                <i className="fa fa-trash" aria-hidden="true" /> Удалить урок
              </button>
              <a
                href={`/courses/lesson/${lesson.id}/edit/`}
                className="lesson-detail-page__btn lesson-detail-page__btn--edit"
              >
                <i className="fa fa-edit" aria-hidden="true" /> Редактировать
              </a>
            </>
          )}
        </div>
      </div>

      {showContinueModal && (
        <div
          className="lesson-detail-page__modal-overlay"
          role="dialog"
          aria-labelledby="continue-modal-title"
          aria-modal="true"
        >
          <div className="lesson-detail-page__modal">
            <div className="lesson-detail-page__modal-header">
              <h5 id="continue-modal-title" className="lesson-detail-page__modal-title">
                <i className="fa fa-graduation-cap" aria-hidden="true" /> Продолжаем
                обучение?
              </h5>
            </div>
            <div className="lesson-detail-page__modal-body">
              <div className="lesson-detail-page__modal-icon">
                <i className={`fa ${modalIcon}`} aria-hidden="true" />
              </div>
              <p className="lesson-detail-page__modal-lead">{modalTitle}</p>
              {lesson_quiz && !lesson_quiz_passed && (
                <p className="lesson-detail-page__modal-muted">
                  Урок <strong>«{lesson.title}»</strong> имеет обязательный тест{' '}
                  <strong>«{lesson_quiz.name}»</strong>, который необходимо пройти для
                  завершения урока.
                </p>
              )}
              {is_last_lesson && (
                <p className="lesson-detail-page__modal-muted">
                  Вы можете вернуться к курсу и проверить свой прогресс или отдохнуть.
                </p>
              )}
              {next_material && !is_last_lesson && !(lesson_quiz && !lesson_quiz_passed) && (
                <p className="lesson-detail-page__modal-muted">
                  {next_material.type === 'quiz' || next_material.type === 'homework'
                    ? `После завершения урока вас ждет ${next_material.type === 'quiz' ? 'тест' : 'задание'} «${next_material.title}». Готовы?`
                    : 'Вы можете перейти к следующему уроку или отдохнуть и вернуться позже.'}
                </p>
              )}
            </div>
            <div className="lesson-detail-page__modal-footer">
              {!is_last_lesson && (
                <button
                  type="button"
                  className="lesson-detail-page__modal-btn lesson-detail-page__modal-btn--secondary"
                  onClick={handleRest}
                  disabled={submitLoading}
                >
                  <i className="fa fa-bed" aria-hidden="true" /> Отдохну
                </button>
              )}
              <button
                type="button"
                className="lesson-detail-page__modal-btn lesson-detail-page__modal-btn--primary"
                onClick={handleContinueConfirm}
                disabled={submitLoading}
              >
                <i
                  className={
                    lesson_quiz && !lesson_quiz_passed
                      ? 'fa fa-graduation-cap'
                      : is_last_lesson
                        ? 'fa fa-check'
                        : next_material?.type === 'quiz'
                          ? 'fa fa-clipboard-check'
                          : next_material?.type === 'homework'
                            ? 'fa fa-pencil-alt'
                            : 'fa fa-arrow-right'
                  }
                  aria-hidden="true"
                />{' '}
                {continueButtonText}
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
};

export default LessonDetailPage;
