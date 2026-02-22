/**
 * Блок статистики: всего курсов, уроков, авторов.
 */
const CourseListStats = ({ totalCourses, totalLessons, totalAuthors }) => (
  <section className="course-list__stats" aria-label="Статистика">
    <div className="course-list__stats-row">
      <div className="course-list__stat-card course-list__stat-card--primary">
        <div className="course-list__stat-body">
          <span className="course-list__stat-label">Всего курсов</span>
          <span className="course-list__stat-value">{totalCourses ?? 0}</span>
        </div>
        <div className="course-list__stat-icon">
          <i className="fas fa-graduation-cap course-list__stat-icon-i" aria-hidden />
        </div>
      </div>
      <div className="course-list__stat-card course-list__stat-card--info">
        <div className="course-list__stat-body">
          <span className="course-list__stat-label">Всего уроков</span>
          <span className="course-list__stat-value">{totalLessons ?? 0}</span>
        </div>
        <div className="course-list__stat-icon">
          <i className="fas fa-book course-list__stat-icon-i" aria-hidden />
        </div>
      </div>
      <div className="course-list__stat-card course-list__stat-card--warning">
        <div className="course-list__stat-body">
          <span className="course-list__stat-label">Авторов</span>
          <span className="course-list__stat-value">{totalAuthors ?? 0}</span>
        </div>
        <div className="course-list__stat-icon">
          <i className="fas fa-users course-list__stat-icon-i" aria-hidden />
        </div>
      </div>
    </div>
  </section>
);

export default CourseListStats;
