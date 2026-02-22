import { useState, useRef, useEffect } from 'react';

/**
 * Одна строка списка курсов: индекс, название, мета, автор, выпадающее меню действий.
 */
const CourseListItem = ({
  index,
  course,
  urls,
  onDelete,
}) => {
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setDropdownOpen(false);
      }
    };
    document.addEventListener('click', handleClickOutside);
    return () => document.removeEventListener('click', handleClickOutside);
  }, []);

  const handleDeleteClick = () => {
    if (window.confirm(`Вы уверены, что хотите удалить курс "${course.title}"?\n\nЭто действие нельзя отменить.`)) {
      onDelete(course.slug);
    }
    setDropdownOpen(false);
  };

  const baseUrl = urls?.course_detail || '/courses/course/';
  const detailUrl = `${baseUrl}${course.slug}/`;
  const editUrl = `${urls?.edit_course || '/courses/course/'}${course.slug}/edit/`;
  const addLessonUrl = `${urls?.add_lesson || '/courses/course/'}${course.slug}/add-lesson/`;

  return (
    <div className={`course-list__item${dropdownOpen ? ' course-list__item--dropdown-open' : ''}`}>
      <div className="course-list__item-grid">
        <div className="course-list__item-index">{index}.</div>
        <div className="course-list__item-info">
          <h6 className="course-list__item-title">{course.title}</h6>
        </div>
        <div className="course-list__item-right">
          <div className="course-list__item-meta">
            <small className="course-list__item-meta-text">
              <i className="fas fa-book" aria-hidden /> {course.lesson_count} уроков
              <span className="course-list__item-meta-sep">•</span>
              <i className="fas fa-clock" aria-hidden /> {course.total_time_hours}ч
            </small>
            <small className="course-list__item-author">
              <i className="fas fa-user" aria-hidden /> {course.author_name}
            </small>
          </div>
          <div className="course-list__item-actions" ref={dropdownRef}>
            <button
              type="button"
              className="course-list__item-dropdown-toggle"
              onClick={() => setDropdownOpen((v) => !v)}
              aria-expanded={dropdownOpen}
              aria-haspopup="true"
              aria-label="Действия с курсом"
            >
              <i className="fas fa-ellipsis-v" aria-hidden />
            </button>
            {dropdownOpen && (
              <ul className="course-list__item-dropdown" role="menu">
                <li role="none">
                  <a className="course-list__item-dropdown-link" href={detailUrl} role="menuitem">
                    <i className="fas fa-eye" aria-hidden /> Просмотр
                  </a>
                </li>
                <li role="none">
                  <a className="course-list__item-dropdown-link" href={editUrl} role="menuitem">
                    <i className="fas fa-edit" aria-hidden /> Редактировать
                  </a>
                </li>
                <li role="none">
                  <a className="course-list__item-dropdown-link" href={addLessonUrl} role="menuitem">
                    <i className="fas fa-plus" aria-hidden /> Добавить материал
                  </a>
                </li>
                <li role="none"><hr className="course-list__item-dropdown-divider" /></li>
                <li role="none">
                  <button
                    type="button"
                    className="course-list__item-dropdown-link course-list__item-dropdown-link--danger"
                    onClick={handleDeleteClick}
                    role="menuitem"
                  >
                    <i className="fas fa-trash" aria-hidden /> Удалить
                  </button>
                </li>
              </ul>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default CourseListItem;
