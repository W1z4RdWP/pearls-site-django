const UnratedAnswers = ({ totalUnratedCount, unratedTextAnswers }) => {
  if (!totalUnratedCount || totalUnratedCount === 0) {
    return (
      <div className="dashboard-page__alert dashboard-page__alert--success" role="status">
        <h3 className="dashboard-page__alert-title">
          <i className="fas fa-check-circle" aria-hidden /> Все открытые ответы оценены
        </h3>
        <p className="dashboard-page__alert-text">
          Нет неоцененных открытых ответов в системе.
        </p>
      </div>
    );
  }

  return (
    <section className="dashboard-page__section" aria-labelledby="unrated-title">
      <h2 id="unrated-title" className="dashboard-page__section-title">
        Неоцененные открытые ответы: {totalUnratedCount}
      </h2>
      <div className="dashboard-page__list">
        {unratedTextAnswers.map((group) => (
          <a
            key={`${group.user.id}-${group.quiz_result.id}`}
            href={`/quizzes/review/${group.quiz_result.id}/`}
            className="dashboard-page__list-item"
          >
            <div className="dashboard-page__list-item-row">
              <div className="dashboard-page__list-item-body">
                <strong>{group.user.full_name}</strong>
                <span className="dashboard-page__muted"> • </span>
                <span className="dashboard-page__quiz-title">{group.quiz_result.quiz_title}</span>
                <span className="dashboard-page__muted"> • </span>
                <span className="dashboard-page__question-preview">
                  {group.answers[0]?.question_text ?? ''}
                </span>
              </div>
              <small className="dashboard-page__list-item-date">
                {group.quiz_result.completed_at}
              </small>
            </div>
          </a>
        ))}
      </div>
    </section>
  );
};

export default UnratedAnswers;
