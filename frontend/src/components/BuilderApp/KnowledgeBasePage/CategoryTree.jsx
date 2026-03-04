import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const categoryContainsLesson = (category, lessonId) => {
  if (!category || !lessonId) return false;
  const lessons = category.lessons || [];
  if (lessons.some((l) => l.id === lessonId)) {
    return true;
  }
  const subcategories = category.subcategories || [];
  return subcategories.some((sub) => categoryContainsLesson(sub, lessonId));
};

const LessonIcon = () => (
  <svg width="16" height="16" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
    <rect x="4" y="3" width="12" height="14" rx="2" fill="currentColor" opacity="0.9" />
    <line x1="6.5" y1="7.5" x2="13.5" y2="7.5" stroke="currentColor" strokeWidth="1.1" opacity="0.6" />
    <line x1="6.5" y1="10.5" x2="13.5" y2="10.5" stroke="currentColor" strokeWidth="1.1" opacity="0.6" />
    <line x1="6.5" y1="13.5" x2="11.5" y2="13.5" stroke="currentColor" strokeWidth="1.1" opacity="0.6" />
  </svg>
);

/**
 * Рекурсивный узел дерева категорий: название категории, подкатегории, уроки.
 * @param {{ id: number, name: string, order: number, subcategories: Array, lessons: Array }} category
 * @param {number|null} selectedLessonId
 * @param {string} [searchQuery] — фильтр по названию (подсветка/скрытие)
 * @param {number|null} [selectedCategoryId] — ID выбранной категории
 * @param {(id: number) => void} [onCategorySelect] — колбэк выбора категории
 * @param {(lessonId: number) => void} [onLessonSelect] — колбэк выбора урока (сбрасывает категорию)
 * @param {number|null} [inlineAddParentId] — ID категории, для которой показывается inline-добавление подкатегории
 * @param {(parentId: number, name: string) => Promise<void>} [onSubmitSubcategory]
 * @param {() => void} [onCancelSubcategory]
 * @param {number|null} [editingCategoryId] — ID категории в режиме инлайн-редактирования
 * @param {(id: number, name: string) => void} [onRenameCategory]
 * @param {() => void} [onCancelEditCategory]
 */
const CategoryTree = ({
  category,
  selectedLessonId,
  searchQuery = '',
  selectedCategoryId,
  onCategorySelect,
  onLessonSelect,
  inlineAddParentId = null,
  onSubmitSubcategory,
  onCancelSubcategory,
  editingCategoryId = null,
  onRenameCategory,
  onCancelEditCategory,
}) => {
  const navigate = useNavigate();
  const inputRef = useRef(null);
  const editInputRef = useRef(null);
  const isAddingSubcategory = inlineAddParentId === category?.id;
  const isEditing = editingCategoryId === category?.id;
  const [expanded, setExpanded] = useState(() =>
    selectedLessonId ? categoryContainsLesson(category, selectedLessonId) : false,
  );

  useEffect(() => {
    if (isAddingSubcategory && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isAddingSubcategory]);

  useEffect(() => {
    if (isEditing && editInputRef.current) {
      editInputRef.current.focus();
      editInputRef.current.select();
    }
  }, [isEditing]);

  if (!category) return null;

  const { id, name, subcategories = [], lessons = [] } = category;
  const hasChildren = subcategories.length > 0 || lessons.length > 0;
  const q = searchQuery.trim().toLowerCase();
  const nameMatches = !q || name.toLowerCase().includes(q);
  const isSelected = selectedCategoryId === id;

  const handleSelectLesson = (lessonId) => {
    if (onLessonSelect) {
      onLessonSelect(lessonId);
    } else {
      navigate(`/builder/lesson/${lessonId}`);
    }
  };

  const visibleLessons = q
    ? lessons.filter((l) => l.title && l.title.toLowerCase().includes(q))
    : lessons;
  const visibleSubcategories = subcategories.filter((sub) => {
    if (!q) return true;
    return sub.name && sub.name.toLowerCase().includes(q);
  });
  const showNode = nameMatches || visibleLessons.length > 0 || visibleSubcategories.length > 0;
  if (!showNode && q) return null;

  const handleHeaderClick = () => {
    if (isEditing) return;
    if (onCategorySelect) {
      onCategorySelect(id);
    }
  };

  const handleToggleClick = (e) => {
    e.stopPropagation();
    if (hasChildren) {
      setExpanded((prev) => !prev);
    }
  };

  const showExpanded = expanded || isAddingSubcategory;

  const handleInlineSubcategorySubmit = () => {
    const name = inputRef.current?.value?.trim();
    if (!name || !onSubmitSubcategory) return;
    inputRef.current.disabled = true;
    onSubmitSubcategory(id, name).finally(() => {
      onCancelSubcategory?.();
    });
  };

  const handleInlineSubcategoryKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleInlineSubcategorySubmit();
    }
    if (e.key === 'Escape') {
      onCancelSubcategory?.();
    }
  };

  const handleInlineSubcategoryBlur = () => {
    if (inputRef.current?.disabled) return;
    const name = inputRef.current?.value?.trim();
    if (!name) {
      onCancelSubcategory?.();
      return;
    }
    if (window.confirm('Создать категорию «' + name + '»?')) {
      handleInlineSubcategorySubmit();
    } else {
      onCancelSubcategory?.();
    }
  };

  const handleEditSubmit = () => {
    const value = editInputRef.current?.value?.trim();
    if (value && value !== name && onRenameCategory) {
      onRenameCategory(id, value);
    } else {
      onCancelEditCategory?.();
    }
  };

  const handleEditKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleEditSubmit();
    }
    if (e.key === 'Escape') {
      onCancelEditCategory?.();
    }
  };

  const handleEditBlur = () => {
    handleEditSubmit();
  };

  return (
    <li className="kb-sidebar__category" data-id={id}>
      <div
        className={`kb-sidebar__category-header ${
          isSelected ? 'kb-sidebar__category-header--selected' : ''
        } ${isEditing ? 'kb-sidebar__category-header--editing' : ''}`}
        onClick={handleHeaderClick}
        role={!isEditing ? 'button' : undefined}
        aria-expanded={hasChildren ? expanded : undefined}
      >
        {isEditing ? (
          <input
            ref={editInputRef}
            type="text"
            className="kb-sidebar__inline-input kb-sidebar__category-title-edit"
            defaultValue={name}
            onKeyDown={handleEditKeyDown}
            onBlur={handleEditBlur}
            onClick={(e) => e.stopPropagation()}
            aria-label="Название категории"
          />
        ) : (
          <span className="kb-sidebar__category-title" title={name}>
            {name}
          </span>
        )}
        {hasChildren && (
          <button
            type="button"
            className={`kb-sidebar__toggle ${expanded ? 'kb-sidebar__toggle--open' : ''}`}
            onClick={handleToggleClick}
            aria-label={expanded ? 'Свернуть' : 'Развернуть'}
            aria-expanded={expanded}
          >
            {expanded ? '−' : '+'}
          </button>
        )}
      </div>
      {(hasChildren || isAddingSubcategory) && showExpanded && (
        <>
          {visibleLessons.length > 0 && (
            <ul className="kb-sidebar__lesson-list" role="list">
              {visibleLessons.map((lesson) => (
                <li
                  key={lesson.id}
                  className={`kb-sidebar__lesson-item ${selectedLessonId === lesson.id ? 'kb-sidebar__lesson-item--active' : ''}`}
                  data-lesson-id={lesson.id}
                >
                  <button
                    type="button"
                    className="kb-sidebar__lesson-link"
                    onClick={() => handleSelectLesson(lesson.id)}
                    title={lesson.title}
                  >
                    {lesson.title}
                    {(lesson.is_mirror || lesson.has_mirrors) && (
                      <span className="kb-sidebar__mirror-label" title="Зеркало урока">
                        {' '}🔗 (зеркало)
                      </span>
                    )}
                  </button>
                </li>
              ))}
            </ul>
          )}
          {(visibleSubcategories.length > 0 || isAddingSubcategory) && (
            <ul className="kb-sidebar__subcategory-list" role="list">
              {isAddingSubcategory && (
                <li className="kb-sidebar__category kb-sidebar__category--inline-add">
                  <div className="kb-sidebar__category-header">
                    <input
                      ref={inputRef}
                      type="text"
                      className="kb-sidebar__inline-input"
                      placeholder="Название подкатегории..."
                      onKeyDown={handleInlineSubcategoryKeyDown}
                      onBlur={handleInlineSubcategoryBlur}
                      aria-label="Название подкатегории"
                    />
                  </div>
                </li>
              )}
              {visibleSubcategories.map((sub) => (
                <CategoryTree
                  key={sub.id}
                  category={sub}
                  selectedLessonId={selectedLessonId}
                  searchQuery={searchQuery}
                  selectedCategoryId={selectedCategoryId}
                  onCategorySelect={onCategorySelect}
                  onLessonSelect={onLessonSelect}
                  inlineAddParentId={inlineAddParentId}
                  onSubmitSubcategory={onSubmitSubcategory}
                  onCancelSubcategory={onCancelSubcategory}
                  editingCategoryId={editingCategoryId}
                  onRenameCategory={onRenameCategory}
                  onCancelEditCategory={onCancelEditCategory}
                />
              ))}
            </ul>
          )}
        </>
      )}
    </li>
  );
};

export default CategoryTree;
