import { useState, useEffect } from 'react';
import { fetchAllBadges } from '../../../../api/api';
import Modal from './Modal';
import './BadgesModal.css';

const BadgesModal = ({ isOpen, onClose }) => {
  const [badges, setBadges] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isOpen) {
      loadBadges();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen]);

  const loadBadges = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchAllBadges();
      setBadges(data.badges || []);
      setStats(data.stats || null);
    } catch (err) {
      setError('Ошибка загрузки бейджей. Попробуйте позже.');
      console.error('Ошибка загрузки бейджей:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Все бейджи">
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
      ) : badges.length === 0 ? (
        <div className="gamification-modal-empty">
          <i className="fa fa-medal fa-4x" aria-hidden="true" />
          <h3>У вас пока нет бейджей</h3>
          <p>Выполняйте задания, проходите курсы и тесты для получения бейджей</p>
        </div>
      ) : (
        <>
          {stats && (
            <div className="gamification-badges-stats">
              <div className="gamification-stat-item">
                <span className="gamification-stat-number">{stats.total_received}</span>
                <span className="gamification-stat-label">Получено бейджей</span>
              </div>
              <div className="gamification-stat-item">
                <span className="gamification-stat-number">{stats.total_available}</span>
                <span className="gamification-stat-label">Всего доступно</span>
              </div>
              <div className="gamification-stat-item">
                <span className="gamification-stat-number">{stats.progress_percent}%</span>
                <span className="gamification-stat-label">Прогресс</span>
              </div>
            </div>
          )}
          <div className="gamification-badges-grid-all">
            {badges.map((badge, idx) => (
              <div
                key={`${badge.name}-${idx}`}
                className="gamification-badge-item-all"
                title={badge.description}
              >
                <div className="gamification-badge-icon-container">
                  {badge.icon_url ? (
                    <img
                      src={badge.icon_url}
                      alt={badge.name}
                      className="gamification-badge-icon-large"
                    />
                  ) : (
                    <div className="gamification-badge-icon-large-placeholder">
                      <i className="fa fa-medal fa-2x" aria-hidden="true" />
                    </div>
                  )}
                  {badge.earned_at && (
                    <div className="gamification-badge-earned-date">
                      <i className="fa fa-calendar" aria-hidden="true" />
                      {badge.earned_at}
                    </div>
                  )}
                </div>
                <div className="gamification-badge-info">
                  <h4 className="gamification-badge-title">{badge.name}</h4>
                  <p className="gamification-badge-description">{badge.description}</p>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </Modal>
  );
};

export default BadgesModal;
