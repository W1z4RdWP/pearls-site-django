import { Link } from 'react-router-dom';
import './CourseCard.css';

/**
 * Карточка одного курса: изображение, заголовок, прогресс/детали, дедлайн, кнопки.
 */
const CourseCard = ({ courseData }) => {
  const { course, status, percent, completed_materials, total_materials, completed_lessons, total_lessons, completed_quizzes, total_quizzes, completed_homeworks, total_homeworks, deadline, is_deadline_overdue, quiz_passed, final_quiz_status, final_quiz_start_url } = courseData;
  const totalTests = (total_quizzes || 0) + (total_homeworks || 0);
  const completedTests = (completed_quizzes || 0) + (completed_homeworks || 0);
  const isAvailable = status === 'available';
  const showProgress = !isAvailable;

  const statusIcon = status === 'completed' ? 'fa-check-circle' : status === 'in_progress' ? 'fa-clock-o' : 'fa-unlock';
  const showDeadline = deadline && !['completed', 'blocked'].includes(status);
  const needFinalQuiz = status === 'in_progress' && course.final_quiz && percent === 100 && !quiz_passed;

  return (
    <div className={`course-card course-card--${status}`}>
      <div className="course-card__image">
        {course.image_url ? (
          <img src={course.image_url} alt={course.title} />
        ) : (
          <div className="course-card__image-placeholder">
            <i className="fa fa-graduation-cap" aria-hidden="true" />
          </div>
        )}
        {course.total_time_minutes > 0 && (
          <div className="course-card__time-badge">
            <div className="course-card__time-number">{course.total_time_minutes}</div>
            <div className="course-card__time-label">мин</div>
          </div>
        )}
        <div className={`course-card__status-badge course-card__status-badge--${status}`}>
          <i className={`fa ${statusIcon}`} aria-hidden="true" />
        </div>
      </div>

      <div className="course-card__content">
        <h3 className="course-card__title">{course.title}</h3>

        {isAvailable ? (
          <div className="course-card__details">
            {total_lessons > 0 && (
              <div className="course-card__detail-item">
                <i className="fa fa-book" aria-hidden="true" /> <span>{total_lessons} уроков</span>
              </div>
            )}
            {totalTests > 0 && (
              <div className="course-card__detail-item">
                <i className="fa fa-question-circle" aria-hidden="true" /> <span>{totalTests} тестов</span>
              </div>
            )}
            {totalTests > 0 && total_lessons > 0 && (
              <div className="course-card__detail-item">
                <i className="fa fa-list" aria-hidden="true" /> <span>{total_materials} материалов</span>
              </div>
            )}
          </div>
        ) : (
          <>
            <div className="course-card__progress">
              <div className="course-card__progress-info">
                <span className="course-card__progress-text">{percent}% завершено</span>
                <span className="course-card__progress-details">
                  {completed_materials} из {total_materials} материалов
                </span>
              </div>
              <div className="course-card__progress-bar">
                <div className="course-card__progress-fill" style={{ width: `${percent}%` }} />
              </div>
            </div>
            <div className="course-card__details">
              <div className="course-card__detail-item">
                <i className="fa fa-book" aria-hidden="true" />{' '}
                <span>{completed_lessons}/{total_lessons} уроков</span>
              </div>
              {totalTests > 0 && (
                <div className="course-card__detail-item">
                  <i className="fa fa-question-circle" aria-hidden="true" />{' '}
                  <span>{completedTests}/{totalTests} тестов</span>
                </div>
              )}
            </div>
          </>
        )}

        {showDeadline && (
          <div className={`course-card__deadline course-card__deadline--${is_deadline_overdue ? 'overdue' : 'warning'}`}>
            {is_deadline_overdue ? (
              <>
                <i className="fa fa-exclamation-triangle text-danger" aria-hidden="true" /> <strong>Просрочен</strong>
                <span className="text-muted small"> (до {deadline})</span>
              </>
            ) : (
              <>
                <i className="fa fa-clock-o text-warning" aria-hidden="true" /> <strong>Завершить до {deadline}</strong>
              </>
            )}
          </div>
        )}

        <div className="course-card__actions">
          {status === 'blocked' && (
            <span className="course-card__status-badge-inline course-card__status-badge-inline--blocked">
              <i className="fa fa-lock" aria-hidden="true" /> Заблокирован
            </span>
          )}
          {status === 'completed' && (
            <span className="course-card__status-badge-inline course-card__status-badge-inline--completed">
              <i className="fa fa-trophy" aria-hidden="true" /> Курс завершен
            </span>
          )}
          {needFinalQuiz && (
            final_quiz_status === 'pending' ? (
              <span className="course-card__status-badge-inline course-card__status-badge-inline--pending">
                <i className="fa fa-hourglass-half" aria-hidden="true" /> Тест ожидает проверки
              </span>
            ) : final_quiz_start_url ? (
              <a href={final_quiz_start_url} className="btn btn-warning btn-sm">
                <i className="fa fa-question-circle" aria-hidden="true" /> Пройти финальный тест
              </a>
            ) : null
          )}
          <Link to={`/courses/course/${course.slug}`} className="btn btn-primary btn-sm course-card__btn-main">
            {isAvailable ? (
              <><i className="fa fa-play" aria-hidden="true" /> Начать курс</>
            ) : (
              <><i className="fa fa-arrow-right" aria-hidden="true" /> Продолжить</>
            )}
          </Link>
          {course.is_incident && (
            <div className="course-card__incident-badge">
              <span className="badge bg-danger">
                <i className="fa fa-exclamation-triangle" aria-hidden="true" /> Курс-инцидент
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CourseCard;
