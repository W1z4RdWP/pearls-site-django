import { useState, useEffect } from 'react';
import { fetchAllAchievements } from '../../../../api/api';
import Modal from './Modal';
import './AchievementsModal.css';

const AchievementsModal = ({ isOpen, onClose }) => {
  const [achievements, setAchievements] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isOpen) {
      loadAchievements();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen]);

  const loadAchievements = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchAllAchievements();
      setAchievements(data.achievements || []);
      setStats(data.stats || null);
    } catch (err) {
      setError('Ошибка загрузки достижений. Попробуйте позже.');
      console.error('Ошибка загрузки достижений:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Все достижения">
      {loading ? (
        <div className="gamification-modal-loading">
          <i className="fa fa-spinner fa-spin fa-2x" aria-hidden="true" />
          <p>Загрузка...</p>
        </div>
      ) : error ? (
        <div className="gamification-modal-error">
          <i className="fa fa-exclamation-triangle fa-2x" aria-hidden="true" />
          <p>{error}</p>
        </div>
      ) : achievements.length === 0 ? (
        <div className="gamification-modal-empty">
          <i className="fa fa-trophy fa-4x" aria-hidden="true" />
          <h3>У вас пока нет достижений</h3>
          <p>Особые достижения появятся здесь за уникальные успехи в обучении</p>
        </div>
      ) : (
        <>
          {stats && (
            <div className="gamification-achievements-stats">
              <div className="gamification-stat-item">
                <span className="gamification-stat-number">{stats.total_received}</span>
                <span className="gamification-stat-label">Получено достижений</span>
              </div>
            </div>
          )}
          <div className="gamification-achievements-grid-all">
            {achievements.map((achievement, idx) => (
              <div
                key={`${achievement.name}-${idx}`}
                className="gamification-achievement-item-all"
                title={achievement.description}
              >
                <div className="gamification-achievement-icon-container">
                  {achievement.icon_url ? (
                    <img
                      src={achievement.icon_url}
                      alt={achievement.name}
                      className="gamification-achievement-icon-large"
                    />
                  ) : (
                    <div className="gamification-achievement-icon-large-placeholder">
                      <i className="fa fa-trophy fa-2x" aria-hidden="true" />
                    </div>
                  )}
                  {achievement.earned_at && (
                    <div className="gamification-achievement-earned-date">
                      <i className="fa fa-calendar" aria-hidden="true" />
                      {achievement.earned_at}
                    </div>
                  )}
                </div>
                <div className="gamification-achievement-info">
                  <h4 className="gamification-achievement-title">{achievement.name}</h4>
                  <p className="gamification-achievement-description">{achievement.description}</p>
                  {achievement.achievement_type_display && (
                    <div className="gamification-achievement-type">
                      <i className="fa fa-star" aria-hidden="true" />
                      {achievement.achievement_type_display}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </Modal>
  );
};

export default AchievementsModal;
