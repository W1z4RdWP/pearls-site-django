import { useState, useEffect, useCallback } from 'react';
import './StaffCarousel.css';

const SLIDES = [
  {
    title: 'Гибридная образовательная среда нового поколения',
    points: [
      'Глубокое усвоение материала за счет применения знаний в реальных ситуациях.',
      'Быстрое выявление и устранение пробелов в понимании теоретического материала.',
      'Повышение уверенности сотрудников в выполнении задач, требующих практических навыков.',
    ],
    image: '/static/global/imgs/staff1.png',
    alt: 'Обучение',
  },
  {
    title: 'Доступ к обучающим материалам 24/7',
    points: [
      'Возможность обучаться в удобное время, совмещая обучение с основной деятельностью.',
      'Ускорение адаптации новых сотрудников.',
      'Снижение потерь информации при передаче знаний внутри команды.',
    ],
    image: '/static/global/imgs/staff2.png',
    alt: 'Тренинги',
  },
  {
    title: 'Единая база знаний',
    points: [
      'Удобный доступ ко всем регламентам, инструкциям, материалам в одном месте.',
      'Быстрая адаптация новых сотрудников за счет готовых обучающих материалов.',
      'Снижение потерь информации при передаче знаний внутри команды.',
    ],
    image: '/static/global/imgs/staff3.png',
    alt: 'Команда',
  },
];

const AUTOPLAY_INTERVAL = 6000;

const StaffCarousel = () => {
  const [activeIndex, setActiveIndex] = useState(0);

  const goToSlide = useCallback((index) => {
    setActiveIndex(index);
  }, []);

  const goNext = useCallback(() => {
    setActiveIndex((prev) => (prev + 1) % SLIDES.length);
  }, []);

  const goPrev = useCallback(() => {
    setActiveIndex((prev) => (prev - 1 + SLIDES.length) % SLIDES.length);
  }, []);

  // Автопрокрутка
  useEffect(() => {
    const timer = setInterval(goNext, AUTOPLAY_INTERVAL);
    return () => clearInterval(timer);
  }, [goNext]);

  return (
    <section className="staff-carousel">
      <div className="staff-carousel__wrapper">
        {/* Индикаторы */}
        <div className="staff-carousel__indicators">
          {SLIDES.map((_, idx) => (
            <button
              key={idx}
              className={`staff-carousel__indicator ${idx === activeIndex ? 'staff-carousel__indicator--active' : ''}`}
              onClick={() => goToSlide(idx)}
              aria-label={`Слайд ${idx + 1}`}
            />
          ))}
        </div>

        {/* Слайды */}
        <div className="staff-carousel__inner">
          {SLIDES.map((slide, idx) => (
            <div
              key={idx}
              className={`staff-carousel__item ${idx === activeIndex ? 'staff-carousel__item--active' : ''}`}
            >
              <div className="staff-carousel__overlay">
                <p className="staff-carousel__title">{slide.title}</p>
                <ul className="staff-carousel__points">
                  {slide.points.map((point, pIdx) => (
                    <li key={pIdx}>{point}</li>
                  ))}
                </ul>
              </div>
              <img src={slide.image} alt={slide.alt} className="staff-carousel__image" />
            </div>
          ))}
        </div>

        {/* Стрелки */}
        <button
          className="staff-carousel__arrow staff-carousel__arrow--prev"
          onClick={goPrev}
          aria-label="Предыдущий слайд"
        >
          <i className="fa-solid fa-chevron-left" />
        </button>
        <button
          className="staff-carousel__arrow staff-carousel__arrow--next"
          onClick={goNext}
          aria-label="Следующий слайд"
        >
          <i className="fa-solid fa-chevron-right" />
        </button>
      </div>
    </section>
  );
};

export default StaffCarousel;
