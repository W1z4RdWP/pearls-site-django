import './NoQuizAttempts.css';

const NoQuizAttempts = () => {
  return (
    <div className="no-quiz-attempts">
      <i className="fas fa-clipboard-list no-quiz-attempts__icon" aria-hidden="true" />
      <h4 className="no-quiz-attempts__title">
        Попытки тестов и заданий не найдены
      </h4>
      <p className="no-quiz-attempts__text">
        У вас пока нет завершённых попыток тестов или отправленных заданий
      </p>
    </div>
  );
};

export default NoQuizAttempts;
