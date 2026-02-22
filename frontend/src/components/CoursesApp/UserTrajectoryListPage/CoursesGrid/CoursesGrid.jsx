import CourseCard from '../CourseCard/CourseCard';
import './CoursesGrid.css';

/**
 * Сетка карточек курсов. При statusFilter === 'all' группы по статусу (не completed, затем completed);
 * иначе — плоский список. Пустое состояние, если курсов нет.
 */
const STATUS_ORDER = ['available', 'in_progress', 'blocked'];

const groupByStatus = (coursesData) => {
  const nonCompleted = [];
  const completed = [];
  coursesData.forEach((cd) => {
    if (cd.status === 'completed') {
      completed.push(cd);
    } else {
      nonCompleted.push(cd);
    }
  });
  const byStatus = {};
  nonCompleted.forEach((cd) => {
    if (!byStatus[cd.status]) byStatus[cd.status] = [];
    byStatus[cd.status].push(cd);
  });
  const ordered = STATUS_ORDER.filter((s) => byStatus[s]?.length).map((s) => ({ status: s, list: byStatus[s] }));
  return { ordered, completed };
};

const CoursesGrid = ({ coursesData, statusFilter }) => {
  const hasCourses = coursesData && coursesData.length > 0;

  if (!hasCourses) {
    return (
      <div className="courses-grid-empty">
        <i className="fa fa-graduation-cap courses-grid-empty__icon" aria-hidden="true" />
        <h3 className="courses-grid-empty__title">Курсы не найдены</h3>
        <p className="courses-grid-empty__text">По выбранному фильтру курсы не найдены</p>
      </div>
    );
  }

  const showGrouped = statusFilter === 'all';
  const { ordered, completed } = showGrouped ? groupByStatus(coursesData) : { ordered: [], completed: [] };

  if (!showGrouped) {
    return (
      <div className="courses-grid">
        {coursesData.map((courseData, index) => (
          <div key={courseData.course.id} className="courses-grid__item" style={{ animationDelay: `${index * 0.1}s` }}>
            <CourseCard courseData={courseData} />
          </div>
        ))}
      </div>
    );
  }

  const items = [];
  ordered.forEach((group, groupIndex) => {
    if (groupIndex > 0) {
      items.push(<div key={`div-${group.status}`} className="courses-grid__divider" />);
    }
    group.list.forEach((courseData) => {
      items.push(
        <div key={courseData.course.id} className="courses-grid__item">
          <CourseCard courseData={courseData} />
        </div>
      );
    });
  });
  if (completed.length > 0) {
    if (ordered.length > 0) {
      items.push(<div key="div-completed" className="courses-grid__divider" />);
    }
    completed.forEach((courseData) => {
      items.push(
        <div key={courseData.course.id} className="courses-grid__item">
          <CourseCard courseData={courseData} />
        </div>
      );
    });
  }

  return <div className="courses-grid">{items}</div>;
};

export default CoursesGrid;
