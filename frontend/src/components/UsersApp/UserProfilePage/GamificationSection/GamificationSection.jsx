import { useState } from 'react';
import './GamificationSection.css';
import BadgesModal from './BadgesModal';
import AchievementsModal from './AchievementsModal';

const CHECKUP_COURSE_SLUG = 'chek-ap-stomatologicheskoi-kliniki';

const GamificationSection = ({
  isExternal,
  recentBadges = [],
  totalBadges = 0,
  recentAchievements = [],
  totalAchievements = 0,
}) => {
  const [isBadgesModalOpen, setIsBadgesModalOpen] = useState(false);
  const [isAchievementsModalOpen, setIsAchievementsModalOpen] = useState(false);

  if (isExternal) {
    return (
      <section className="gamification-section" aria-label="Чек-ап">
        <div className="gamification-section__card">
          <div className="gamification-section__card-header">
            <h4>
              <i className="fa fa-stethoscope" aria-hidden="true" /> Чек-ап стоматологической клиники
            </h4>
          </div>
          <div className="gamification-section__card-content">
            <p className="gamification-section__checkup-text">
              Пройдите комплексную оценку вашей стоматологической клиники
            </p>
            <a
              href={`/courses/${CHECKUP_COURSE_SLUG}/`}
              className="gamification-section__btn"
            >
              <i className="fa fa-play-circle" aria-hidden="true" /> Перейти к чек-апу
            </a>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className="gamification-section" aria-label="Бейджи и достижения">
      <div className="gamification-section__grid">
        <div className="gamification-section__card">
          <div className="gamification-section__card-header">
            <h4>
              <i className="fa fa-medal" aria-hidden="true" /> Бейджи
            </h4>
            <span className="gamification-section__badge-count">{totalBadges}</span>
          </div>
          <div className="gamification-section__card-content">
            {recentBadges.length > 0 ? (
              <>
                <div className="gamification-section__grid-items">
                  {recentBadges.map((b, idx) => (
                    <div
                      key={`${b.name}-${idx}`}
                      className="gamification-section__item"
                      title={b.description}
                    >
                      {b.icon_url ? (
                        <img
                          src={b.icon_url}
                          alt={b.name}
                          className="gamification-section__item-icon"
                        />
                      ) : (
                        <div className="gamification-section__item-icon-placeholder">
                          <i className="fa fa-medal" aria-hidden="true" />
                        </div>
                      )}
                      <span className="gamification-section__item-name">{b.name}</span>
                      {b.earned_at && (
                        <small className="gamification-section__item-date">{b.earned_at}</small>
                      )}
                    </div>
                  ))}
                </div>
                {totalBadges > 0 && (
                  <div className="gamification-section__show-more">
                    <button
                      onClick={() => setIsBadgesModalOpen(true)}
                      className="gamification-section__btn gamification-section__btn--sm"
                    >
                      <i className="fa fa-eye" aria-hidden="true" /> Показать все ({totalBadges})
                    </button>
                  </div>
                )}
              </>
            ) : (
              <div className="gamification-section__empty">
                <i className="fa fa-medal fa-2x" aria-hidden="true" />
                <p>У вас пока нет бейджей</p>
                <small>Выполняйте задания и проходите курсы для получения бейджей</small>
              </div>
            )}
          </div>
        </div>

        <div className="gamification-section__card">
          <div className="gamification-section__card-header">
            <h4>
              <i className="fa fa-trophy" aria-hidden="true" /> Достижения
            </h4>
            <span className="gamification-section__badge-count">{totalAchievements}</span>
          </div>
          <div className="gamification-section__card-content">
            {recentAchievements.length > 0 ? (
              <>
                <div className="gamification-section__grid-items">
                  {recentAchievements.map((a, idx) => (
                    <div
                      key={`${a.name}-${idx}`}
                      className="gamification-section__item"
                      title={a.description}
                    >
                      {a.icon_url ? (
                        <img
                          src={a.icon_url}
                          alt={a.name}
                          className="gamification-section__item-icon"
                        />
                      ) : (
                        <div className="gamification-section__item-icon-placeholder gamification-section__item-icon-placeholder--achievement">
                          <i className="fa fa-trophy" aria-hidden="true" />
                        </div>
                      )}
                      <span className="gamification-section__item-name">{a.name}</span>
                      {a.earned_at && (
                        <small className="gamification-section__item-date">{a.earned_at}</small>
                      )}
                    </div>
                  ))}
                </div>
                {totalAchievements > 0 && (
                  <div className="gamification-section__show-more">
                    <button
                      onClick={() => setIsAchievementsModalOpen(true)}
                      className="gamification-section__btn gamification-section__btn--sm"
                    >
                      <i className="fa fa-eye" aria-hidden="true" /> Показать все ({totalAchievements})
                    </button>
                  </div>
                )}
              </>
            ) : (
              <div className="gamification-section__empty">
                <i className="fa fa-trophy fa-2x" aria-hidden="true" />
                <p>У вас пока нет достижений</p>
                <small>Особые достижения появятся здесь</small>
              </div>
            )}
          </div>
        </div>
      </div>
      <BadgesModal
        isOpen={isBadgesModalOpen}
        onClose={() => setIsBadgesModalOpen(false)}
      />
      <AchievementsModal
        isOpen={isAchievementsModalOpen}
        onClose={() => setIsAchievementsModalOpen(false)}
      />
    </section>
  );
};

export default GamificationSection;
