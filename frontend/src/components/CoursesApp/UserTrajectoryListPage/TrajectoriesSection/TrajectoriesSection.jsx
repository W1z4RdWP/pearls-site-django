import TrajectoryCard from '../TrajectoryCard/TrajectoryCard';
import './TrajectoriesSection.css';

/**
 * Секция «Ваши траектории обучения»: список карточек или сообщение об отсутствии.
 */
const TrajectoriesSection = ({ userTrajectories }) => {
  const hasTrajectories = userTrajectories && userTrajectories.length > 0;

  return (
    <section className="trajectories-section" aria-label="Ваши траектории обучения">
      <h1 className="trajectories-section__title">
        <i className="fa fa-road" aria-hidden="true" /> Ваши траектории обучения
      </h1>
      {!hasTrajectories ? (
        <div className="trajectories-section__empty alert alert-info" role="status">
          Вам не назначено ни одной траектории. Обратитесь к администрации.
        </div>
      ) : (
        <div className="trajectories-section__grid row">
          {userTrajectories.map((ut) => (
            <div key={ut.id} className="col-md-6 col-lg-4 mb-4">
              <TrajectoryCard
                id={ut.id}
                trajectory={ut.trajectory}
                completed={ut.completed}
                startedAt={ut.started_at}
                detailUrl={ut.detail_url}
              />
            </div>
          ))}
        </div>
      )}
    </section>
  );
};

export default TrajectoriesSection;
