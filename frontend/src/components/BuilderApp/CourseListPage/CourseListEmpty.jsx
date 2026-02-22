/**
 * Пустое состояние: курсы не найдены.
 */
const createCourseUrl = '/courses/create-course/';

const CourseListEmpty = () => (
  <div className="course-list__empty">
    <i className="fas fa-graduation-cap course-list__empty-icon" aria-hidden />
    <h5 className="course-list__empty-title">Курсы не найдены</h5>
    <p className="course-list__empty-text">На платформе пока нет созданных курсов</p>
    <a href={createCourseUrl} className="course-list__empty-btn">
      <i className="fas fa-plus" aria-hidden /> Создать первый курс
    </a>
  </div>
);

export default CourseListEmpty;
