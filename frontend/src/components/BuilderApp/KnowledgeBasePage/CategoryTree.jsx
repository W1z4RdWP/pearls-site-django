import { useState } from 'react';

const categoryContainsLesson = (category, lessonId) => {
  if (!category || !lessonId) return false;
  const lessons = category.lessons || [];
  if (lessons.some((l) => l.id === lessonId)) {
    return true;
  }
  const subcategories = category.subcategories || [];
  return subcategories.some((sub) => categoryContainsLesson(sub, lessonId));
};
import { useNavigate } from 'react-router-dom';

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
 */
const CategoryTree = ({
  category,
  selectedLessonId,
  searchQuery = '',
  selectedCategoryId,
  onCategorySelect,
}) => {
  const navigate = useNavigate();
  const [expanded, setExpanded] = useState(() =>
    selectedLessonId ? categoryContainsLesson(category, selectedLessonId) : false,
  );

  if (!category) return null;

  const { id, name, subcategories = [], lessons = [] } = category;
  const hasChildren = subcategories.length > 0 || lessons.length > 0;
  const q = searchQuery.trim().toLowerCase();
  const nameMatches = !q || name.toLowerCase().includes(q);
  const isSelected = selectedCategoryId === id;

  const handleSelectLesson = (lessonId) => {
    navigate(`/builder/lesson/${lessonId}`);
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
    if (onCategorySelect) {
      onCategorySelect(id);
    }
    if (hasChildren) {
      setExpanded((e) => !e);
    }
  };

  return (
    <li className="kb-sidebar__category" data-id={id}>
      <div
        className={`kb-sidebar__category-header ${
          isSelected ? 'kb-sidebar__category-header--selected' : ''
        }`}
        onClick={handleHeaderClick}
        role={hasChildren ? 'button' : undefined}
        aria-expanded={hasChildren ? expanded : undefined}
      >
        <span className="kb-sidebar__category-title" title={name}>
          {name}
        </span>
        {hasChildren && (
          <span className={`kb-sidebar__toggle ${expanded ? 'kb-sidebar__toggle--open' : ''}`}>+</span>
        )}
      </div>
      {hasChildren && expanded && (
        <>
          {visibleLessons.length > 0 && (
            <ul className="kb-sidebar__lesson-list" role="list">
              {visibleLessons.map((lesson) => (
                <li
                  key={lesson.id}
                  className={`kb-sidebar__lesson-item ${selectedLessonId === lesson.id ? 'kb-sidebar__lesson-item--active' : ''}`}
                  data-lesson-id={lesson.id}
                >
                  {/* <span className="kb-sidebar__lesson-icon" aria-hidden="true">
                    <LessonIcon />
                  </span> */}
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
          {visibleSubcategories.length > 0 && (
            <ul className="kb-sidebar__subcategory-list" role="list">
              {visibleSubcategories.map((sub) => (
                <CategoryTree
                  key={sub.id}
                  category={sub}
                  selectedLessonId={selectedLessonId}
                  searchQuery={searchQuery}
                  selectedCategoryId={selectedCategoryId}
                  onCategorySelect={onCategorySelect}
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
