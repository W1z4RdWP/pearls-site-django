/**
 * Карточка одной траектории обучения.
 */
const TrajectoryCard = ({ id, trajectory, completed, startedAt, detailUrl }) => {
  return (
    <div className="trajectory-card trajectory-card__root">
      <div className="trajectory-card__body">
        <h4 className="trajectory-card__title">{trajectory.name}</h4>
        <p className="trajectory-card__description text-muted">{trajectory.description}</p>
        <ul className="trajectory-card__meta list-unstyled">
          <li>
            <b>Статус:</b>{' '}
            {completed ? (
              <span className="badge bg-success">Завершена</span>
            ) : (
              <span className="badge bg-primary">В процессе</span>
            )}
          </li>
          <li>
            <b>Дата назначения:</b> {startedAt}
          </li>
        </ul>
        <a href={detailUrl} className="btn btn-modern trajectory-card__link w-100">
          Перейти к траектории
        </a>
      </div>
    </div>
  );
};

export default TrajectoryCard;
