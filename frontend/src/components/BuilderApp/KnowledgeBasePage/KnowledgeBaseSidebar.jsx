import { useState, useMemo } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import CategoryTree from './CategoryTree';

const TAB_CATEGORIES = 'categories';
const TAB_UNCAT = 'uncat';
const TAB_DICT = 'dict';

// const LessonIcon = () => (
//   <svg width="16" height="16" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
//     <rect x="4" y="3" width="12" height="14" rx="2" fill="currentColor" opacity="0.9" />
//     <line x1="6.5" y1="7.5" x2="13.5" y2="7.5" stroke="currentColor" strokeWidth="1.1" opacity="0.6" />
//     <line x1="6.5" y1="10.5" x2="13.5" y2="10.5" stroke="currentColor" strokeWidth="1.1" opacity="0.6" />
//     <line x1="6.5" y1="13.5" x2="11.5" y2="13.5" stroke="currentColor" strokeWidth="1.1" opacity="0.6" />
//   </svg>
// );

/**
 * Сайдбар базы знаний: вкладки (Категории / Без категории / Словарь), поиск, дерево/списки.
 */
const KnowledgeBaseSidebar = ({
  categories = [],
  uncategorizedLessons = [],
  dictionarySections = [],
  isReadonly,
  selectedLessonId,
  urls = {},
  searchQuery,
  onSearchChange,
}) => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState(TAB_CATEGORIES);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [selectedCategoryId, setSelectedCategoryId] = useState(null);

  const filteredUncategorized = useMemo(() => {
    const q = (searchQuery || '').trim().toLowerCase();
    if (!q) return uncategorizedLessons;
    return uncategorizedLessons.filter((l) => l.title && l.title.toLowerCase().includes(q));
  }, [uncategorizedLessons, searchQuery]);

  const filteredDictSections = useMemo(() => {
    const q = (searchQuery || '').trim().toLowerCase();
    if (!q) return dictionarySections;
    return dictionarySections.filter((s) => s.name && s.name.toLowerCase().includes(q));
  }, [dictionarySections, searchQuery]);

  const handleSelectLesson = (lessonId) => {
    navigate(`/builder/lesson/${lessonId}`);
  };

  const handleCategorySelect = (categoryId) => {
    setSelectedCategoryId(categoryId);
  };

  const getCsrfToken = () => {
    if (typeof document === 'undefined') return '';
    const input = document.querySelector('[name=csrfmiddlewaretoken]');
    return input ? input.value : '';
  };

  const handleAddRootCategory = async () => {
    const name = window.prompt('Введите название новой категории:');
    if (!name) return;
    try {
      const response = await fetch('/builder/categories/ajax_add_root/', {
        method: 'POST',
        headers: {
          'X-CSRFToken': getCsrfToken(),
          'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
        },
        body: new URLSearchParams({ name: name.trim() }),
      });
      const data = await response.json();
      if (data.error) {
        window.alert(`Ошибка: ${data.error}`);
        return;
      }
      if (data.id && window.sessionStorage) {
        window.sessionStorage.setItem('new_category_id', String(data.id));
      }
      window.location.reload();
    } catch (e) {
      window.alert('Ошибка сети');
    }
  };

  const handleAddSubcategory = async () => {
    if (!selectedCategoryId) {
      window.alert('Выделите категорию!');
      return;
    }
    const name = window.prompt('Введите название подкатегории:');
    if (!name) return;
    try {
      const response = await fetch('/builder/categories/ajax_add_sub/', {
        method: 'POST',
        headers: {
          'X-CSRFToken': getCsrfToken(),
          'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
        },
        body: new URLSearchParams({
          name: name.trim(),
          parent_id: String(selectedCategoryId),
        }),
      });
      const data = await response.json();
      if (data.error) {
        window.alert(`Ошибка: ${data.error}`);
        return;
      }
      if (data.id && window.sessionStorage) {
        window.sessionStorage.setItem('new_category_id', String(data.id));
      }
      window.location.reload();
    } catch (e) {
      window.alert('Ошибка сети');
    }
  };

  const findCategoryById = (id, list = categories) => {
    for (const cat of list) {
      if (cat.id === id) return cat;
      const sub = findCategoryById(id, cat.subcategories || []);
      if (sub) return sub;
    }
    return null;
  };

  const handleEditCategoryOrLesson = async () => {
    if (selectedLessonId) {
      navigate(`/builder/lesson/${selectedLessonId}/edit`);
      return;
    }
    if (!selectedCategoryId) {
      window.alert('Выделите категорию или урок!');
      return;
    }
    const cat = findCategoryById(selectedCategoryId);
    const oldName = (cat && cat.name) || '';
    const newName = window.prompt('Новое название категории:', oldName);
    if (!newName || newName.trim() === oldName.trim()) return;
    try {
      const response = await fetch('/builder/categories/ajax_rename/', {
        method: 'POST',
        headers: {
          'X-CSRFToken': getCsrfToken(),
          'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
        },
        body: new URLSearchParams({
          id: String(selectedCategoryId),
          name: newName.trim(),
        }),
      });
      const data = await response.json();
      if (data.error) {
        window.alert(`Ошибка: ${data.error}`);
        return;
      }
      window.location.reload();
    } catch (e) {
      window.alert('Ошибка сети');
    }
  };

  const handleDeleteCategoryOrLesson = () => {
    if (selectedCategoryId && !selectedLessonId) {
      if (window.confirm('Удалить категорию?')) {
        window.location.href = `/builder/categories/${selectedCategoryId}/delete/`;
      }
      return;
    }
    if (selectedLessonId) {
      if (window.confirm('Удалить урок?')) {
        window.location.href = `/builder/lesson/${selectedLessonId}/delete/`;
      }
      return;
    }
    window.alert('Выделите категорию или урок!');
  };

  const handleAddLesson = () => {
    if (selectedCategoryId) {
      navigate(`/builder/add/${selectedCategoryId}`);
    } else {
      navigate('/builder/add');
    }
  };

  const draftCreateUrl = urls.lesson_draft_create && selectedLessonId
    ? urls.lesson_draft_create.replace('{id}', String(selectedLessonId))
    : null;

  return (
    <aside
      className={`kb-sidebar ${sidebarCollapsed ? 'kb-sidebar--collapsed' : ''}`}
      id="kb-sidebar"
      aria-label="Навигация по базе знаний"
    >
      <div className="kb-sidebar__tabs">
        <button
          type="button"
          className={`kb-sidebar__tab ${activeTab === TAB_CATEGORIES ? 'kb-sidebar__tab--active' : ''}`}
          onClick={() => setActiveTab(TAB_CATEGORIES)}
        >
          Категории
        </button>
        <button
          type="button"
          className={`kb-sidebar__tab ${activeTab === TAB_UNCAT ? 'kb-sidebar__tab--active' : ''}`}
          onClick={() => setActiveTab(TAB_UNCAT)}
        >
          Без категории
        </button>
        <button
          type="button"
          className={`kb-sidebar__tab ${activeTab === TAB_DICT ? 'kb-sidebar__tab--active' : ''}`}
          onClick={() => setActiveTab(TAB_DICT)}
        >
          Словарь
        </button>
      </div>

      <div className="kb-sidebar__search">
        <button
          type="button"
          className="kb-sidebar__toggle-btn"
          onClick={() => setSidebarCollapsed((c) => !c)}
          title={sidebarCollapsed ? 'Показать категории' : 'Скрыть категории'}
          aria-label={sidebarCollapsed ? 'Показать панель' : 'Скрыть панель'}
        >
          <span className="kb-sidebar__toggle-icon">{sidebarCollapsed ? '⮞' : '⮜'}</span>
        </button>
        <input
          type="text"
          className="kb-sidebar__search-input"
          placeholder="Поиск по категориям и урокам..."
          value={searchQuery || ''}
          onChange={(e) => onSearchChange(e.target.value)}
          autoComplete="off"
          aria-label="Поиск по категориям и урокам"
        />
      </div>

      <div className="kb-sidebar__content">
        {activeTab === TAB_CATEGORIES && (
          <div className="kb-sidebar__scroll">
            <ul className="kb-sidebar__category-list" role="list">
              {categories.map((cat) => (
                <CategoryTree
                  key={cat.id}
                  category={cat}
                  selectedLessonId={selectedLessonId}
                  searchQuery={searchQuery || ''}
                  selectedCategoryId={selectedCategoryId}
                  onCategorySelect={handleCategorySelect}
                />
              ))}
            </ul>
            {categories.length === 0 && (
              <p className="kb-sidebar__empty">Нет категорий</p>
            )}
          </div>
        )}

        {activeTab === TAB_UNCAT && (
          <div className="kb-sidebar__scroll">
            <ul className="kb-sidebar__lesson-list kb-sidebar__list-flat" role="list">
              {filteredUncategorized.map((lesson) => (
                <li
                  key={lesson.id}
                  className={`kb-sidebar__lesson-item ${selectedLessonId === lesson.id ? 'kb-sidebar__lesson-item--active' : ''}`}
                >
                  <button
                    type="button"
                    className="kb-sidebar__lesson-link"
                    onClick={() => handleSelectLesson(lesson.id)}
                    title={lesson.title}
                  >
                    {lesson.title}
                    {lesson.has_mirrors && (
                      <span className="kb-sidebar__mirror-label" title="Есть зеркала"> 🔗</span>
                    )}
                  </button>
                </li>
              ))}
            </ul>
            {filteredUncategorized.length === 0 && (
              <p className="kb-sidebar__empty">Нет уроков без категории</p>
            )}
          </div>
        )}

        {activeTab === TAB_DICT && (
          <div className="kb-sidebar__scroll">
            <ul className="kb-sidebar__dict-list" role="list">
              {filteredDictSections.map((section) => (
                <li key={section.id} className="kb-sidebar__dict-item" data-id={`dict-section-${section.id}`}>
                  <span className="kb-sidebar__dict-icon" aria-hidden="true">ℹ</span>
                  <a
                    href={`/builder/dictionary/${section.id}/`}
                    className="kb-sidebar__dict-link"
                    title={section.name}
                  >
                    {section.name}
                  </a>
                </li>
              ))}
            </ul>
            {filteredDictSections.length === 0 && (
              <p className="kb-sidebar__empty">Нет разделов словаря</p>
            )}
          </div>
        )}
      </div>

      {!isReadonly && (
        <div className="kb-sidebar__category-actions" aria-label="Управление категориями и уроками">
          <button
            type="button"
            className="kb-sidebar__category-actions-btn"
            onClick={handleAddRootCategory}
            title="Добавить корневую категорию"
          >
            +|
          </button>
          <button
            type="button"
            className="kb-sidebar__category-actions-btn"
            onClick={handleAddSubcategory}
            title="Добавить подкатегорию"
          >
            +
          </button>
          <button
            type="button"
            className="kb-sidebar__category-actions-btn"
            onClick={handleEditCategoryOrLesson}
            title="Изменить название категории или открыть редактирование урока"
          >
            v
          </button>
          <button
            type="button"
            className="kb-sidebar__category-actions-btn"
            onClick={handleDeleteCategoryOrLesson}
            title="Удалить категорию или урок"
          >
            x
          </button>
          <button
            type="button"
            className="kb-sidebar__category-actions-btn"
            onClick={handleAddLesson}
            title="Добавить урок"
          >
            📄
          </button>
        </div>
      )}

      {(urls.update_control || draftCreateUrl) && (
        <div className="kb-sidebar__footer">
          {urls.update_control && (
            <a href={urls.update_control} className="kb-sidebar__footer-btn">
              Контроль обновлений
            </a>
          )}
        </div>
      )}
    </aside>
  );
};

export default KnowledgeBaseSidebar;
