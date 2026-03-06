/**
 * Пустое состояние: курсы не найдены.
 * @param {string} [createCourseUrl] — ссылка на создание курса
 * @param {string} [emptyTitle] — заголовок
 * @param {string} [emptyText] — описание
 * @param {string} [buttonText] — текст кнопки
 */
const CourseListEmpty = ({
  createCourseUrl = '/courses/create-course/',
  emptyTitle = 'Курсы не найдены',
  emptyText = 'На платформе пока нет созданных курсов',
  buttonText = 'Создать первый курс',
}) => (
  <div className="course-list__empty">
    <i className="fas fa-graduation-cap course-list__empty-icon" aria-hidden />
    <h5 className="course-list__empty-title">{emptyTitle}</h5>
    <p className="course-list__empty-text">{emptyText}</p>
    <a href={createCourseUrl} className="course-list__empty-btn">
      <i className="fas fa-plus" aria-hidden /> {buttonText}
    </a>
  </div>
);

export default CourseListEmpty;
