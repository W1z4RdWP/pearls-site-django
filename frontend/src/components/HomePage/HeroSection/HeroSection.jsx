import { Link } from 'react-router-dom';
import './HeroSection.css';

const STATS = [
  { value: '120+', label: 'сотрудников обучено' },
  { value: '25', label: 'актуальных курсов' },
  { value: '98%', label: 'завершили обучение' },
];

const CATEGORIES = [
  { label: 'Популярное' },
  { label: 'Внутренний регламент' },
  { label: 'Квалификация' },
  { label: 'Психология' },
  { label: 'Все курсы' },
];

const FACES = [
  { img: '/static/global/imgs/hero_das.jpg', label: 'Главный врач' },
  { img: '/static/global/imgs/hero_dentist.jpg', label: 'Стоматолог' },
  { img: '/static/global/imgs/doc1.png', label: 'Обучение' },
  { emoji: '\u{1F3C6}', label: 'Наставничество' },
  { emoji: '\u{1F525}', label: 'Вдохновение' },
  { emoji: '\u{1F60A}', label: 'Дружелюбие' },
];

const HeroSection = ({ isAuthenticated }) => {
  const ctaHref = isAuthenticated ? '#courseCarousel' : '/users/login/';

  return (
    <section className="hero">
      <div className="hero__left">
        <h1 className="hero__title">
          Найди себя и прокачайся в
          <br />
          «Территории Улыбки»
        </h1>

        <div className="hero__stats">
          {STATS.map((stat) => (
            <div key={stat.label} className="hero__stat">
              <span className="hero__stat-num">{stat.value}</span>
              <span className="hero__stat-label">{stat.label}</span>
            </div>
          ))}
        </div>

        <div className="hero__categories">
          {CATEGORIES.map((cat) => (
            <Link key={cat.label} to="/courses/trajectory/">
              <button className="hero__category-btn">{cat.label}</button>
            </Link>
          ))}
        </div>

        <a href={ctaHref} className="hero__cta">
          Выбрать курс
        </a>
      </div>

      <div className="hero__right">
        <div className="hero__faces">
          {FACES.map((face) => (
            <div key={face.label} className="hero__face-block">
              {face.img ? (
                <img src={face.img} alt={face.label} className="hero__face-img" />
              ) : (
                <span className="hero__face-emoji">{face.emoji}</span>
              )}
              <span className="hero__face-label">{face.label}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default HeroSection;
