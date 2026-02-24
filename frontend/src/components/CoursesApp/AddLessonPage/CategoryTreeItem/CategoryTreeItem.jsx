import { useState } from 'react';
import './CategoryTreeItem.css';

const CategoryTreeItem = ({
  category,
  selectedIds,
  highlightedId,
  onSelect,
  onDoubleClick,
  searchQuery,
}) => {
  const [expanded, setExpanded] = useState(false);
  const hasChildren = (category.lessons && category.lessons.length > 0) ||
    (category.subcategories && category.subcategories.length > 0);
  const categoryItemId = `category_${category.id}`;
  const isHighlighted = highlightedId === categoryItemId;
  const isSelected = selectedIds.has(categoryItemId);

  const matchesSearch = (text) => {
    if (!searchQuery || !text) return true;
    return text.toLowerCase().includes(searchQuery.toLowerCase());
  };
  const categoryMatches = matchesSearch(category.name);
  const lessonMatches = (lesson) => matchesSearch(lesson.title);
  const someLessonMatches = category.lessons && category.lessons.some(lessonMatches);
  const someSubMatches = category.subcategories && category.subcategories.some(
    (sub) => sub.name && matchesSearch(sub.name)
  );
  const showCategory = !searchQuery || categoryMatches || someLessonMatches || someSubMatches;

  if (!showCategory) return null;

  const handleToggle = (e) => {
    e.stopPropagation();
    if (hasChildren) setExpanded((prev) => !prev);
  };

  const handleHeaderClick = (e) => {
    if (e.target.classList.contains('category-tree-item__arrow')) return;
    onSelect('category', category.id, category.name);
  };

  const handleHeaderDoubleClick = (e) => {
    if (e.target.classList.contains('category-tree-item__arrow')) return;
    onDoubleClick('category', category.id, category.name);
  };

  return (
    <li className="category-tree-item" data-id={category.id}>
      <div
        className={`category-tree-item__header ${isHighlighted || isSelected ? 'category-tree-item__header--selected' : ''}`}
        onClick={handleHeaderClick}
        onDoubleClick={handleHeaderDoubleClick}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            handleHeaderClick(e);
          }
        }}
        aria-label={`Категория ${category.name}`}
      >
        <span className="category-tree-item__title" title={category.name}>
          {searchQuery && categoryMatches ? (
            <>
              {category.name.split(new RegExp(`(${searchQuery.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi')).map((part, i) =>
                part.toLowerCase() === searchQuery.toLowerCase() ? (
                  <mark key={i} className="category-tree-item__highlight">{part}</mark>
                ) : (
                  part
                )
              )}
            </>
          ) : (
            category.name
          )}
        </span>
        {hasChildren && (
          <span
            className="category-tree-item__arrow"
            onClick={handleToggle}
            onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); handleToggle(e); } }}
            role="button"
            tabIndex={0}
            aria-expanded={expanded}
          >
            {expanded ? '−' : '+'}
          </span>
        )}
      </div>
      {category.lessons && category.lessons.length > 0 && (
        <ul
          className="category-tree-item__lesson-list"
          style={{ display: expanded || searchQuery ? 'block' : 'none' }}
        >
          {category.lessons.map((lesson) => {
            const lid = `lesson_${lesson.id}`;
            const show = !searchQuery || lessonMatches(lesson);
            if (!show) return null;
            const highlighted = highlightedId === lid;
            const selected = selectedIds.has(lid);
            return (
              <li
                key={lesson.id}
                className={`category-tree-item__lesson ${highlighted || selected ? 'category-tree-item__lesson--selected' : ''}`}
                data-lesson-id={lesson.id}
                onClick={(e) => { e.stopPropagation(); onSelect('lesson', lesson.id, lesson.title); }}
                onDoubleClick={(e) => { e.stopPropagation(); onDoubleClick('lesson', lesson.id, lesson.title); }}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    onSelect('lesson', lesson.id, lesson.title);
                  }
                }}
              >
                <a className="category-tree-item__lesson-link" title={lesson.title}>
                  {searchQuery && lessonMatches(lesson) ? (
                    <>
                      {lesson.title.split(new RegExp(`(${searchQuery.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi')).map((part, i) =>
                        part.toLowerCase() === searchQuery.toLowerCase() ? (
                          <mark key={i} className="category-tree-item__highlight">{part}</mark>
                        ) : (
                          part
                        )
                      )}
                    </>
                  ) : (
                    lesson.title
                  )}
                  {(lesson.is_mirror || lesson.has_mirrors) && (
                    <span className="category-tree-item__mirror-label" title="Зеркало урока">
                      {' '}🔗 (зеркало)
                    </span>
                  )}
                </a>
              </li>
            );
          })}
        </ul>
      )}
      {category.subcategories && category.subcategories.length > 0 && (
        <ul
          className="category-tree-item__subcategory-list"
          style={{ display: expanded || searchQuery ? 'block' : 'none' }}
        >
          {category.subcategories.map((sub) => (
            <CategoryTreeItem
              key={sub.id}
              category={sub}
              selectedIds={selectedIds}
              highlightedId={highlightedId}
              onSelect={onSelect}
              onDoubleClick={onDoubleClick}
              searchQuery={searchQuery}
            />
          ))}
        </ul>
      )}
    </li>
  );
};

export default CategoryTreeItem;
