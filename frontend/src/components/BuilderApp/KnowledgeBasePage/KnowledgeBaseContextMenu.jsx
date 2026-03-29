import { useEffect } from 'react';
import { createPortal } from 'react-dom';

/**
 * Контекстное меню базы знаний (как в master_detail.html):
 * Копировать, Вырезать, Вставить, Зеркало, Вставить зеркало, Назначить, Показать все зеркала / Скрыть.
 */
const KnowledgeBaseContextMenu = ({
  visible,
  position: { x, y },
  target,
  clipboardData,
  mirrorSourceLessonId,
  mirrorsFilterActive,
  onClose,
  onCopy,
  onCut,
  onPaste,
  onMirror,
  onMirrorHere,
  onAssign,
  onShowAllMirrors,
  onHideMirrors,
}) => {
  const isLesson = target?.type === 'lesson';
  const isCategory = target?.type === 'category';
  const canPaste = !!clipboardData && (isCategory || isLesson);
  const canMirror = isLesson;
  const canMirrorHere = isCategory && !!mirrorSourceLessonId;
  const showMirrorsItem = isLesson && (target?.hasMirrors || target?.isMirror) && !mirrorsFilterActive;
  const showHideItem = mirrorsFilterActive;

  useEffect(() => {
    if (!visible) return;
    const handleClickOutside = (e) => {
      if (!e.target.closest('.kb-context-menu')) {
        onClose();
      }
    };
    const handleScroll = () => onClose();
    document.addEventListener('click', handleClickOutside);
    document.addEventListener('contextmenu', handleClickOutside);
    document.addEventListener('scroll', handleScroll, true);
    return () => {
      document.removeEventListener('click', handleClickOutside);
      document.removeEventListener('contextmenu', handleClickOutside);
      document.removeEventListener('scroll', handleScroll, true);
    };
  }, [visible, onClose]);

  if (!visible) return null;

  return createPortal(
    <div
      className="kb-context-menu"
      style={{ left: x, top: y }}
      role="menu"
      onClick={(e) => e.stopPropagation()}
    >
      <div className="kb-context-menu__item" role="menuitem" onClick={() => (isCategory || isLesson) && onCopy()}>
        Скопировать
      </div>
      <div className="kb-context-menu__item" role="menuitem" onClick={() => (isCategory || isLesson) && onCut()}>
        Вырезать
      </div>
      <div
        className="kb-context-menu__item"
        role="menuitem"
        style={{ opacity: canPaste ? 1 : 0.5, pointerEvents: canPaste ? '' : 'none', cursor: canPaste ? 'pointer' : 'not-allowed' }}
        onClick={() => canPaste && onPaste()}
      >
        Вставить
      </div>
      <div
        className="kb-context-menu__item"
        role="menuitem"
        style={{ opacity: canMirror ? 1 : 0.5, pointerEvents: canMirror ? '' : 'none', cursor: canMirror ? 'pointer' : 'not-allowed' }}
        onClick={() => canMirror && onMirror()}
      >
        Зеркало
      </div>
      <div
        className="kb-context-menu__item"
        role="menuitem"
        style={{ opacity: canMirrorHere ? 1 : 0.5, pointerEvents: canMirrorHere ? '' : 'none', cursor: canMirrorHere ? 'pointer' : 'not-allowed' }}
        onClick={() => canMirrorHere && onMirrorHere()}
      >
        Вставить зеркало
      </div>
      <div
        className="kb-context-menu__item"
        role="menuitem"
        onClick={() => (isLesson || isCategory) && onAssign()}
      >
        Назначить
      </div>
      {showMirrorsItem && (
        <div className="kb-context-menu__item" role="menuitem" onClick={onShowAllMirrors}>
          Показать все зеркала
        </div>
      )}
      {showHideItem && (
        <div className="kb-context-menu__item" role="menuitem" onClick={onHideMirrors}>
          Скрыть
        </div>
      )}
    </div>,
    document.body
  );
};

export default KnowledgeBaseContextMenu;
