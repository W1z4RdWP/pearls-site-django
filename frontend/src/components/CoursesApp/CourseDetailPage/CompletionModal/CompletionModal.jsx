import './CompletionModal.css';

const CompletionModal = ({ trajectoriesInfo, onClose }) => {
  const hasTrajectory = trajectoriesInfo.length > 0;

  const handleOverlayClick = () => {
    if (hasTrajectory) {
      window.location.href = trajectoriesInfo[0].detail_url;
    } else {
      onClose();
    }
  };

  return (
    <div className="completion-modal" onClick={handleOverlayClick} role="dialog" aria-label="Курс завершен">
      <div className="completion-modal__content" onClick={(e) => e.stopPropagation()}>
        <div className="completion-modal__icon">
          <i className="fa fa-check-circle" aria-hidden="true" />
        </div>
        <h2 className="completion-modal__title">Курс завершен!</h2>
        <p className="completion-modal__text">Поздравляем с успешным завершением курса!</p>
        <div className="completion-modal__actions">
          {hasTrajectory ? (
            trajectoriesInfo.map((ti) => (
              <a
                key={ti.user_trajectory_id}
                href={ti.detail_url}
                className="completion-modal__btn completion-modal__btn--primary"
              >
                <i className="fa fa-arrow-left" aria-hidden="true" /> Вернуться к траектории
              </a>
            ))
          ) : (
            <button className="completion-modal__btn completion-modal__btn--secondary" onClick={onClose}>
              <i className="fa fa-times" aria-hidden="true" /> Закрыть
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default CompletionModal;
