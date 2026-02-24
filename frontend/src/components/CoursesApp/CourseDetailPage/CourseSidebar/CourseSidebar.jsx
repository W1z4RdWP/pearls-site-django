import './CourseSidebar.css';

const CourseSidebar = ({
  userCourse, isStaff, isSuperuser, course, progress,
  finalQuiz, nextMaterialLink, nextCourseInTrajectory, incident,
}) => {
  const status = userCourse?.status;

  const renderDeadlineAlert = () => {
    if (!userCourse?.deadline || isStaff) return null;
    if (userCourse.is_deadline_overdue) {
      return (
        <div className="course-sidebar__alert course-sidebar__alert--danger">
          <i className="fa fa-exclamation-triangle" aria-hidden="true" />
          <strong>Просрочен</strong>
          <p>Срок завершения курса истек: {userCourse.deadline}</p>
        </div>
      );
    }
    return (
      <div className="course-sidebar__alert course-sidebar__alert--warning">
        <i className="fa fa-clock-o" aria-hidden="true" />
        <strong>Завершить до {userCourse.deadline}</strong>
      </div>
    );
  };

  const renderFinalQuiz = () => {
    if (!finalQuiz || status !== 'started') return null;

    return (
      <div className="course-sidebar__final-quiz">
        <h6 className="course-sidebar__fq-heading">
          <i className="fa fa-graduation-cap" aria-hidden="true" /> Финальный тест
        </h6>
        {progress.all_completed ? (
          <>
            {finalQuiz.status === 'pending' && (
              <div className="course-sidebar__alert course-sidebar__alert--warning">
                <i className="fa fa-hourglass-half" aria-hidden="true" />
                <strong>Тест ожидает проверки</strong>
                <p>Ваш тест отправлен на проверку наставнику. Результаты будут доступны после проверки.</p>
              </div>
            )}
            {finalQuiz.status !== 'pending' && (
              <p>Для завершения курса необходимо пройти финальный тест</p>
            )}
            {finalQuiz.is_locked && (
              <div className="course-sidebar__alert course-sidebar__alert--warning">
                <i className="fa fa-exclamation-triangle" aria-hidden="true" />
                <strong>Тест заблокирован!</strong> Исчерпаны все попытки.
                <p>Необходимо повторить материал курса для разблокировки теста.</p>
              </div>
            )}
            {!finalQuiz.is_locked && finalQuiz.attempt_limit > 0 && (
              <div className="course-sidebar__attempts">
                <i className="fa fa-info-circle" aria-hidden="true" />{' '}
                <strong>Лимит попыток:</strong> {finalQuiz.attempt_limit}
                {finalQuiz.failed_attempts > 0 && (
                  <>
                    <br /><strong>Использовано:</strong> {finalQuiz.failed_attempts}
                    <br /><strong>Осталось:</strong> {finalQuiz.attempts_left}
                  </>
                )}
              </div>
            )}
            <div className="course-sidebar__actions">
              {finalQuiz.status === 'pending' ? (
                <span className="course-sidebar__btn course-sidebar__btn--disabled">
                  <i className="fa fa-hourglass-half" aria-hidden="true" /> Тест ожидает проверки
                </span>
              ) : finalQuiz.is_locked ? (
                <span className="course-sidebar__btn course-sidebar__btn--disabled">
                  <i className="fa fa-lock" aria-hidden="true" /> Тест заблокирован
                </span>
              ) : finalQuiz.passed ? (
                <a href={finalQuiz.link} className="course-sidebar__btn">
                  <i className="fa fa-check-circle" aria-hidden="true" /> Посмотреть результат
                </a>
              ) : (
                <a href={finalQuiz.link} className="course-sidebar__btn">
                  <i className="fa fa-graduation-cap" aria-hidden="true" /> Пройти тест
                </a>
              )}
            </div>
          </>
        ) : (
          <>
            <p>
              Для успешной сдачи финального тестирования, пожалуйста, внимательно изучите весь
              представленный материал. Тест будет назначен по завершении обучения.
            </p>
            <div className="course-sidebar__actions">
              <span className="course-sidebar__btn course-sidebar__btn--disabled">
                <i className="fa fa-lock" aria-hidden="true" /> Пройти тест
              </span>
            </div>
          </>
        )}
      </div>
    );
  };

  const renderStatusContent = () => {
    if (!userCourse) {
      if (isStaff) {
        return (
          <div className="course-sidebar__staff-msg">
            <p>Вы авторизованы как администратор системы</p>
            <p>Статусы курса отключены</p>
          </div>
        );
      }
      return (
        <div className="course-sidebar__login">
          <p>Чтобы начать курс, пожалуйста, войдите в систему</p>
          <a href="/users/login" className="course-sidebar__btn">
            <i className="fa fa-sign-in" aria-hidden="true" /> Войти в систему
          </a>
        </div>
      );
    }

    if (status === 'blocked') return null;

    if (status === 'available') {
      if (isStaff) {
        return (
          <div className="course-sidebar__staff-msg">
            <p>{isSuperuser ? 'Вы авторизованы как суперпользователь' : 'Вы авторизованы как администратор системы'}</p>
            <p>Статусы курса отключены</p>
          </div>
        );
      }
      return (
        <>
          <span className="course-sidebar__status course-sidebar__status--available">
            <i className="fa fa-unlock" aria-hidden="true" /> Доступен
          </span>
          <p>Для того, чтобы начать курс, пожалуйста, нажмите на кнопку «Начать курс».</p>
          {renderDeadlineAlert()}
        </>
      );
    }

    if (status === 'started') {
      return (
        <>
          <span className="course-sidebar__status course-sidebar__status--started">
            <i className="fa fa-play" aria-hidden="true" /> В процессе
          </span>
          {userCourse.start_date && (
            <p className="course-sidebar__date">
              <i className="fa fa-calendar" aria-hidden="true" /> Начат: {userCourse.start_date}
            </p>
          )}
          {renderDeadlineAlert()}
          {renderFinalQuiz()}
          {nextMaterialLink && (
            <div className="course-sidebar__actions">
              <a href={nextMaterialLink} className="course-sidebar__btn">
                <i className="fa fa-arrow-right" aria-hidden="true" /> Продолжить обучение
              </a>
            </div>
          )}
        </>
      );
    }

    if (status === 'completed') {
      return (
        <>
          <span className="course-sidebar__status course-sidebar__status--completed">
            <i className="fa fa-check-circle" aria-hidden="true" /> Завершен
          </span>
          {userCourse.start_date && (
            <p className="course-sidebar__date">
              <i className="fa fa-calendar" aria-hidden="true" /> Начат: {userCourse.start_date}
            </p>
          )}
          {userCourse.end_date && (
            <p className="course-sidebar__date">
              <i className="fa fa-trophy" aria-hidden="true" /> Завершен: {userCourse.end_date}
            </p>
          )}
          {nextCourseInTrajectory && (
            <div className="course-sidebar__actions">
              <a href={`/courses/course/${nextCourseInTrajectory.slug}/`} className="course-sidebar__btn">
                <i className="fa fa-arrow-right" aria-hidden="true" /> {nextCourseInTrajectory.title} →
              </a>
            </div>
          )}
        </>
      );
    }

    return null;
  };

  const renderIncidentButtons = () => {
    if (!incident || !isStaff) return null;
    return (
      <div className="course-sidebar__admin">
        <h6 className="course-sidebar__admin-title">
          <i className="fa fa-user-plus" aria-hidden="true" /> Назначение курса
        </h6>
        <div className="course-sidebar__admin-buttons course-sidebar__admin-buttons--col">
          {incident.has_expert && (
            <a
              href={`/courses/course/${course.slug}/assign-expert/`}
              className="course-sidebar__mini-btn course-sidebar__mini-btn--add"
              title={`Назначить курс руководителю ${incident.expert_name}`}
            >
              <i className="fa fa-user-tie" aria-hidden="true" />
              <span>Назначить руководителю</span>
            </a>
          )}
          {incident.has_assigned && (
            <a
              href={`/courses/course/${course.slug}/assign-assigned/`}
              className="course-sidebar__mini-btn course-sidebar__mini-btn--add"
              title="Назначить курс назначенным пользователям"
            >
              <i className="fa fa-users" aria-hidden="true" />
              <span>Назначить сотрудникам</span>
            </a>
          )}
        </div>
      </div>
    );
  };

  const renderAdminPanel = () => {
    if (!isStaff) return null;
    return (
      <div className="course-sidebar__admin">
        <h6 className="course-sidebar__admin-title">
          <i className="fa fa-cog" aria-hidden="true" /> Администрирование
        </h6>
        <div className="course-sidebar__admin-buttons">
          <a href={`/courses/course/${course.slug}/add-lesson/`} className="course-sidebar__mini-btn course-sidebar__mini-btn--add" title="Добавить урок">
            <i className="fa fa-plus" aria-hidden="true" />
            <span className="course-sidebar__mini-btn-text">Добавить</span>
          </a>
          {course.is_incident && incident ? (
            <>
              <a href="/builder/incidents/" className="course-sidebar__mini-btn">Инциденты</a>
              <a href={`/builder/incidents/${incident.id}/edit/`} className="course-sidebar__mini-btn course-sidebar__mini-btn--edit" title="Редактировать инцидент">
                <i className="fa fa-edit" aria-hidden="true" />
                <span className="course-sidebar__mini-btn-text">Редактировать инцидент</span>
              </a>
            </>
          ) : (
            <>
              <a href={`/courses/course/${course.slug}/edit`} className="course-sidebar__mini-btn course-sidebar__mini-btn--edit" title="Редактировать">
                <i className="fa fa-edit" aria-hidden="true" />
                <span className="course-sidebar__mini-btn-text">Редактировать</span>
              </a>
              <button
                className="course-sidebar__mini-btn course-sidebar__mini-btn--delete"
                title="Удалить курс"
                onClick={() => {
                  if (window.confirm('Вы уверены, что хотите удалить этот курс? Все уроки будут удалены!')) {
                    window.location.href = `/courses/course/${course.slug}/delete/`;
                  }
                }}
              >
                <i className="fa fa-trash" aria-hidden="true" />
                <span className="course-sidebar__mini-btn-text">Удалить</span>
              </button>
            </>
          )}
        </div>
      </div>
    );
  };

  return (
    <aside className="course-sidebar">
      <div className="course-sidebar__header">
        <h4>Информация о курсе</h4>
      </div>
      <div className="course-sidebar__body">
        {renderStatusContent()}
      </div>
      {renderIncidentButtons()}
      {renderAdminPanel()}
    </aside>
  );
};

export default CourseSidebar;
