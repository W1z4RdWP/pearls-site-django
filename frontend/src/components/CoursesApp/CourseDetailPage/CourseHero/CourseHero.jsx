import { useState } from 'react';
import './CourseHero.css';

const CourseHero = ({ course, trajectoriesInfo }) => {
  const [descriptionVisible, setDescriptionVisible] = useState(true);

  const handleToggle = () => setDescriptionVisible((v) => !v);

  return (
    <section className="course-hero" aria-label={course.title}>
      <div className="container">
        <div className="course-hero__row">
          <div className="course-hero__content">
            <button
              className="course-hero__toggle"
              onClick={handleToggle}
              aria-expanded={descriptionVisible}
            >
              <i className={`fa ${descriptionVisible ? 'fa-eye-slash' : 'fa-eye'}`} aria-hidden="true" />
              {descriptionVisible ? ' Скрыть описание' : ' Показать описание'}
            </button>

            {descriptionVisible && (
              <div className="course-hero__description">
                <h1 className="course-hero__title">{course.title}</h1>
                <div
                  className="course-hero__lead"
                  dangerouslySetInnerHTML={{ __html: course.description }}
                />
                {trajectoriesInfo.length > 0 && (
                  <div className="course-hero__badges">
                    {trajectoriesInfo.map((ti) => (
                      <span className="course-hero__badge" key={ti.user_trajectory_id}>
                        {ti.trajectory_name} ({ti.order}/{ti.total_courses})
                      </span>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          {course.image_url && descriptionVisible && (
            <div className="course-hero__image-wrap">
              <img
                src={course.image_url}
                alt={course.title}
                className="course-hero__image"
              />
            </div>
          )}
        </div>
      </div>
    </section>
  );
};

export default CourseHero;
