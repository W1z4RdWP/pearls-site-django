import './MaterialItem.css';

const TYPE_LABELS = {
  lesson: 'Урок',
  quiz: 'Тест',
  homework: 'Задание',
};

const TYPE_ICONS = {
  lesson: 'fa-book',
  quiz: 'fa-graduation-cap',
  homework: 'fa-tasks',
};

const MaterialItem = ({ material, isStaff, courseSlug, onDelete }) => {
  const { type, id, title, status, link, lesson_quiz, badge } = material;
  const isAccessible = status !== 'locked';
  const itemClass = `material-item material-item--${type} ${!isAccessible ? 'material-item--blocked' : ''}`;

  const renderBadge = () => {
    if (status === 'locked') return <span className="material-item__badge material-item__badge--locked">🔒</span>;
    if (status === 'completed') return <span className="material-item__badge material-item__badge--success">✓</span>;
    if (status === 'pending') return <span className="material-item__badge material-item__badge--pending"><i className="fa fa-hourglass-half" /></span>;
    if (status === 'incorrect') return <span className="material-item__badge material-item__badge--danger">↻</span>;
    return null;
  };

  const renderLessonQuizIcon = () => {
    if (type !== 'lesson' || !lesson_quiz) return null;
    if (lesson_quiz.passed) {
      return <i className="fa fa-check-circle material-item__quiz-icon material-item__quiz-icon--success" title="Тест завершен" />;
    }
    if (lesson_quiz.status === 'pending') {
      return <i className="fa fa-hourglass-half material-item__quiz-icon material-item__quiz-icon--warning" title="Тест ожидает проверки" />;
    }
    return <i className="fa fa-graduation-cap material-item__quiz-icon material-item__quiz-icon--info" title="Требуется пройти тест" />;
  };

  const typeLabel = () => {
    let label = TYPE_LABELS[type] || type;
    if (type === 'homework' && status === 'incorrect') label = 'Задание (требуется исправление)';
    return label;
  };

  const content = (
    <>
      <span className="material-item__icon">
        <i className={`fa ${TYPE_ICONS[type] || 'fa-file'}`} aria-hidden="true" />
      </span>
      <div className="material-item__info">
        <div className="material-item__title">{title}</div>
        <div className="material-item__type">
          {typeLabel()}
          {renderLessonQuizIcon()}
        </div>
      </div>
      {renderBadge()}
    </>
  );

  return (
    <div className={itemClass}>
      {isAccessible && link ? (
        <a href={link} className="material-item__link">
          {content}
        </a>
      ) : (
        <div className="material-item__link material-item__link--disabled">
          {content}
        </div>
      )}

      {isStaff && onDelete && (
        <button
          className="material-item__delete"
          title={`Удалить ${TYPE_LABELS[type] || 'элемент'} из курса`}
          onClick={() => {
            if (window.confirm(`Вы уверены, что хотите удалить ${TYPE_LABELS[type]?.toLowerCase() || 'элемент'} из курса?`)) {
              onDelete(type, id);
            }
          }}
        >
          <i className="fa fa-times" aria-hidden="true" />
        </button>
      )}
    </div>
  );
};

export default MaterialItem;
