import { useState, useMemo } from 'react';
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import MaterialItem from '../MaterialItem/MaterialItem';
import { reorderMaterials } from '../../../../api/courses_api';
import './MaterialsList.css';

const TYPE_ICONS = {
  lesson: 'fa-book',
  quiz: 'fa-graduation-cap',
  homework: 'fa-tasks',
};

const TYPE_LABELS = {
  lesson: 'Урок',
  quiz: 'Тест',
  homework: 'Задание',
};

function SortableMaterialRow({ material }) {
  const id = `${material.type}-${material.id}`;
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`materials-list__sortable-row ${isDragging ? 'materials-list__sortable-row--dragging' : ''}`}
    >
      <span
        className="materials-list__drag-handle"
        aria-label="Перетащить для изменения порядка"
        {...attributes}
        {...listeners}
      >
        <i className="fa fa-grip-vertical" aria-hidden="true" />
      </span>
      <span className="materials-list__sortable-icon">
        <i className={`fa ${TYPE_ICONS[material.type] || 'fa-file'}`} aria-hidden="true" />
      </span>
      <div className="materials-list__sortable-info">
        <span className="materials-list__sortable-title">{material.title}</span>
        <span className="materials-list__sortable-type">{TYPE_LABELS[material.type] || material.type}</span>
      </div>
    </div>
  );
}

const MaterialsList = ({
  materials,
  isStaff,
  courseSlug,
  userCourseStatus,
  hasMaterials,
  onStartCourse,
  onDeleteMaterial,
  onMaterialsReordered,
}) => {
  const [reorderMode, setReorderMode] = useState(false);
  const [reorderList, setReorderList] = useState([]);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState(null);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 8 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  );

  const sortableIds = useMemo(
    () => reorderList.map((m) => `${m.type}-${m.id}`),
    [reorderList],
  );

  const handleStartReorder = () => {
    setReorderList([...materials]);
    setSaveError(null);
    setReorderMode(true);
  };

  const handleCancelReorder = () => {
    setReorderMode(false);
    setReorderList([]);
    setSaveError(null);
  };

  const handleDragEnd = (event) => {
    const { active, over } = event;
    if (over && active.id !== over.id) {
      setReorderList((prev) => {
        const oldIndex = prev.findIndex((m) => `${m.type}-${m.id}` === active.id);
        const newIndex = prev.findIndex((m) => `${m.type}-${m.id}` === over.id);
        if (oldIndex === -1 || newIndex === -1) return prev;
        return arrayMove(prev, oldIndex, newIndex);
      });
    }
  };

  const handleSaveOrder = async () => {
    setSaving(true);
    setSaveError(null);
    try {
      const payload = reorderList.map((m) => ({ type: m.type, id: m.id }));
      await reorderMaterials(courseSlug, payload);
      onMaterialsReordered?.();
      setReorderMode(false);
      setReorderList([]);
    } catch (err) {
      setSaveError(err.message || 'Не удалось сохранить порядок');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="materials-list">
      <div className="materials-list__section">
        <div className="materials-list__header">
          <h3 className="materials-list__title">Материалы курса</h3>
          <div className="materials-list__actions">
            {isStaff && !reorderMode && (
              <button
                type="button"
                className="materials-list__btn materials-list__btn--edit"
                title="Изменить порядок"
                onClick={handleStartReorder}
              >
                <i className="fa fa-sort" aria-hidden="true" />
                <span className="materials-list__btn-text">Изменить порядок</span>
              </button>
            )}
            {reorderMode && (
              <>
                <button
                  type="button"
                  className="materials-list__btn materials-list__btn--save"
                  disabled={saving}
                  onClick={handleSaveOrder}
                >
                  <i className="fa fa-check" aria-hidden="true" />
                  <span className="materials-list__btn-text">{saving ? 'Сохранение…' : 'Сохранить'}</span>
                </button>
                <button
                  type="button"
                  className="materials-list__btn materials-list__btn--edit"
                  disabled={saving}
                  onClick={handleCancelReorder}
                >
                  <i className="fa fa-times" aria-hidden="true" />
                  <span className="materials-list__btn-text">Отмена</span>
                </button>
              </>
            )}
            {userCourseStatus === 'available' && !isStaff && (
              <button
                type="button"
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

        {reorderMode ? (
          <>
            <p className="materials-list__reorder-hint">Перетащите элементы для изменения порядка, затем нажмите «Сохранить».</p>
            {saveError && (
              <p className="materials-list__error" role="alert">
                {saveError}
              </p>
            )}
            <div className="materials-list__items">
              <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
                <SortableContext items={sortableIds} strategy={verticalListSortingStrategy}>
                  {reorderList.map((m) => (
                    <SortableMaterialRow key={`${m.type}-${m.id}`} material={m} />
                  ))}
                </SortableContext>
              </DndContext>
            </div>
          </>
        ) : (
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
        )}
      </div>
    </div>
  );
};

export default MaterialsList;
