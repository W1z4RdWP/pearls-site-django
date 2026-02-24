import { Link } from 'react-router-dom';
import MaterialItem from '../MaterialItem/MaterialItem';
import './MaterialsList.css';

const MaterialsList = ({ materials, isStaff, courseSlug, userCourseStatus, hasMaterials, onStartCourse, onDeleteMaterial }) => {
  return (
    <div className="materials-list">
      <div className="materials-list__section">
        <div className="materials-list__header">
          <h3 className="materials-list__title">Материалы курса</h3>
          <div className="materials-list__actions">
            {isStaff && (
              <>
                <a
                  href={`/courses/course/${courseSlug}/reorder/`}
                  className="materials-list__btn materials-list__btn--edit"
                  title="Изменить порядок"
                >
                  <i className="fa fa-sort" aria-hidden="true" />
                  <span className="materials-list__btn-text">Изменить порядок</span>
                </a>
              </>
            )}
            {userCourseStatus === 'available' && !isStaff && (
              <button
                className={`materials-list__btn materials-list__btn--start ${!hasMaterials ? 'materials-list__btn--disabled' : ''}`}
                onClick={hasMaterials ? onStartCourse : undefined}
                disabled={!hasMaterials}
                title={!hasMaterials ? 'Курс не содержит материалов' : 'Начать курс'}
              >
                <i className="fa fa-play" aria-hidden="true" />
                <span className="materials-list__btn-text">Начать курс</span>
              </button>
            )}
          </div>
        </div>
        <div className="materials-list__items">
          {materials.map((m) => (
            <MaterialItem
              key={`${m.type}-${m.id}`}
              material={m}
              isStaff={isStaff}
              courseSlug={courseSlug}
              onDelete={onDeleteMaterial}
            />
          ))}
          {materials.length === 0 && (
            <p className="materials-list__empty">Материалы курса пока не добавлены.</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default MaterialsList;
