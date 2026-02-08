import { Link } from 'react-router-dom';
import './Footer.css';

const SOCIAL_LINKS = [
  {
    href: 'https://vk.com/territorysmile',
    alt: 'ВКонтакте',
    icon: '/static/global/imgs/vk.png',
  },
  {
    href: 'https://telegram.me/Stomatologiya_saratov',
    alt: 'Telegram',
    icon: '/static/global/imgs/tg.png',
  },
  {
    href: 'https://32cdi.ru/',
    alt: 'Территория Улыбки',
    icon: '/static/global/imgs/terr_smile.png',
  },
];

const CONTACTS = [
  { href: 'mailto:info@32cdi.ru', text: 'info@smileterritory.ru' },
  { href: 'tel:+78452725552', text: '+7 (906) 307-43-32' },
  {
    href: 'https://32cdi.ru/contacts/',
    text: 'г. Саратов, ул. Огородная, 144/146',
    external: true,
  },
];

const REQUISITES = [
  'ИП Данилова Татьяна Евгеньевна',
  'ИНН: 645103548600',
  'ОГРНИП: 408028109291300006299',
  'г. Саратов, ул. Томская, 7, 82',
];

const Footer = ({ isAuthenticated, isExternal, isStaff, siteVersion }) => {
  return (
    <footer className="footer">
      <div className="footer__container">
        {/* Бренд */}
        <div className="footer__col footer__brand">
          {!isExternal ? (
            <Link to="/">
              <img
                src="/static/global/imgs/logo_light_theme.png"
                alt="Логотип"
                className="footer__logo"
              />
            </Link>
          ) : (
            <img
              src="/static/global/imgs/logo_light_theme.png"
              alt="Логотип"
              className="footer__logo"
            />
          )}
          <p className="footer__tagline">
            Территория улыбки — учись, вдохновляйся, совершенствуйся!
          </p>
        </div>

        {/* Навигация */}
        {isAuthenticated && !isExternal && (
          <div className="footer__col footer__links">
            <h5 className="footer__heading">Навигация</h5>
            <ul>
              <li>
                <Link to="/">Главная</Link>
              </li>
              <li>
                <Link to="/about">О нас</Link>
              </li>
              {isStaff && (
                <li>
                  <Link to="/changelog">Изменения</Link>
                </li>
              )}
              <li>
                <a href="/users/profile/">Профиль</a>
              </li>
            </ul>
          </div>
        )}

        {/* Соцсети */}
        <div className="footer__col footer__social">
          <h5 className="footer__heading">Мы в соцсетях</h5>
          <div className="footer__social-icons">
            {SOCIAL_LINKS.map((social) => (
              <a
                key={social.alt}
                href={social.href}
                target="_blank"
                rel="noopener noreferrer"
                aria-label={social.alt}
              >
                <img src={social.icon} alt={social.alt} className="footer__social-icon" />
              </a>
            ))}
          </div>
        </div>

        {/* Контакты */}
        <div className="footer__col footer__contact">
          <h5 className="footer__heading">Контакты</h5>
          <ul>
            {CONTACTS.map((contact) => (
              <li key={contact.text}>
                <a
                  href={contact.href}
                  {...(contact.external ? { target: '_blank', rel: 'noopener noreferrer' } : {})}
                >
                  {contact.text}
                </a>
              </li>
            ))}
          </ul>
        </div>

        {/* Реквизиты */}
        <div className="footer__col footer__requisites">
          <h5 className="footer__heading">Реквизиты</h5>
          <ul>
            {REQUISITES.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      </div>

      {/* Нижняя часть */}
      <div className="footer__bottom">
        {siteVersion && <span className="footer__version">Версия: {siteVersion}</span>}
        <img
          src="/static/global/imgs/logo_light_theme.png"
          alt="Логотип"
          className="footer__logo-mobile"
        />
        <a href="/privacy-policy/" className="footer__policy">
          Политика конфиденциальности
        </a>
      </div>
    </footer>
  );
};

export default Footer;
