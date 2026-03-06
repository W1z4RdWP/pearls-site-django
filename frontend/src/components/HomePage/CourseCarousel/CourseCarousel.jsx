import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import './CourseCarousel.css';

const AUTOPLAY_INTERVAL = 5000;

const CourseCarousel = ({ courses }) => {
  const [activeIndex, setActiveIndex] = useState(0);

  const goNext = useCallback(() => {
    if (courses.length === 0) return;
    setActiveIndex((prev) => (prev + 1) % courses.length);
  }, [courses.length]);

  const goPrev = useCallback(() => {
    if (courses.length === 0) return;
    setActiveIndex((prev) => (prev - 1 + courses.length) % courses.length);
  }, [courses.length]);

  useEffect(() => {
    if (courses.length <= 1) return;
    const timer = setInterval(goNext, AUTOPLAY_INTERVAL);
    return () => clearInterval(timer);
  }, [goNext, courses.length]);

  if (!courses || courses.length === 0) {
    return null;
  }

  return (
    <section className="course-carousel" id="courseCarousel">
      <Link to="/courses/trajectories/" className="course-carousel__all-btn">
        Все курсы
      </Link>

      <div className="course-carousel__wrapper">
        <div className="course-carousel__inner">
          {courses.map((course, idx) => (
            <div
              key={course.id}
              className={`course-carousel__item ${idx === activeIndex ? 'course-carousel__item--active' : ''}`}
            >
              <Link to={`/courses/${course.slug}/`}>
                <img
                  src={course.image_url}
                  alt={course.title}
                  className="course-carousel__image"
                />
              </Link>
              <div className="course-carousel__info">
                <Link to={`/courses/${course.slug}/`} className="course-carousel__title-link">
                  <h5 className="course-carousel__title">{course.title}</h5>
                </Link>
                <p className="course-carousel__description">{course.description_plain}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Стрелки */}
        {courses.length > 1 && (
          <div className="course-carousel__arrows">
            <button
              className="course-carousel__arrow course-carousel__arrow--prev"
              onClick={goPrev}
              aria-label="Предыдущий курс"
            >
              <i className="fa-solid fa-chevron-left" />
            </button>
            <button
              className="course-carousel__arrow course-carousel__arrow--next"
              onClick={goNext}
              aria-label="Следующий курс"
            >
              <i className="fa-solid fa-chevron-right" />
            </button>
          </div>
        )}
      </div>
    </section>
  );
};

export default CourseCarousel;
