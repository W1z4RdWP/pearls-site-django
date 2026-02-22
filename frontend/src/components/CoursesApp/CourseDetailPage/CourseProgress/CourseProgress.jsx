import './CourseProgress.css';

const CourseProgress = ({ progress }) => {
  const { percent, completed_lessons, total_lessons, completed_quizzes,
    total_quizzes, completed_homeworks, total_homeworks } = progress;

  const totalTests = total_quizzes + total_homeworks;
  const completedTests = completed_quizzes + completed_homeworks;

  return (
    <div className="course-progress">
      <div className="course-progress__bar-track">
        <div
          className="course-progress__bar-fill"
          style={{ width: `${percent}%` }}
          role="progressbar"
          aria-valuenow={percent}
          aria-valuemin={0}
          aria-valuemax={100}
        />
      </div>
      <p className="course-progress__text">
        {completed_lessons}/{total_lessons} уроков
        {totalTests > 0 && <>, {completedTests}/{totalTests} тестов</>}
        {' '}({percent}%)
      </p>
    </div>
  );
};

export default CourseProgress;
