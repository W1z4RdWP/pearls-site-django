import { useState, useMemo, useRef, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import CategoryTree from './CategoryTree';
import KnowledgeBaseContextMenu from './KnowledgeBaseContextMenu';
import { createRootCategory, createSubcategory, renameCategory } from '../../../api/builder_api';

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
  onCategoriesUpdated,
}) => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState(TAB_CATEGORIES);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [selectedCategoryId, setSelectedCategoryId] = useState(null);
  /** null | 'root' | { parentId: number } — режим inline-добавления категории */
  const [inlineAddMode, setInlineAddMode] = useState(null);
  const rootCategoryInputRef = useRef(null);
  /** Контекстное меню: { visible, x, y, target: { type, id, hasMirrors?, isMirror? } } */
  const [contextMenu, setContextMenu] = useState({ visible: false, x: 0, y: 0, target: null });
  const [clipboardData, setClipboardData] = useState(null);
  const [mirrorSourceLessonId, setMirrorSourceLessonId] = useState(null);
  /** ID урока для фильтра «Показать все зеркала»; null = не фильтровать */
  const [mirrorsFilterLessonId, setMirrorsFilterLessonId] = useState(null);
  /** ID категории в режиме инлайн-редактирования названия */
  const [editingCategoryId, setEditingCategoryId] = useState(null);

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

  const handleCategorySelect = (categoryId) => {
    setSelectedCategoryId(categoryId);
    navigate('/builder/content');
  };

  const handleLessonSelect = (lessonId) => {
    setSelectedCategoryId(null);
    navigate(`/builder/lesson/${lessonId}`);
  };

  const getCsrfToken = () => {
    if (typeof document === 'undefined') return '';
    const input = document.querySelector('[name=csrfmiddlewaretoken]');
    return input ? input.value : '';
  };

  useEffect(() => {
    if (inlineAddMode === 'root' && rootCategoryInputRef.current) {
      rootCategoryInputRef.current.focus();
    }
  }, [inlineAddMode]);

  const submitRootCategory = async (name) => {
    if (!name?.trim()) return;
    try {
      await createRootCategory(name.trim());
      setInlineAddMode(null);
      onCategoriesUpdated?.();
    } catch (e) {
      window.alert(e.message || 'Ошибка сети');
      if (rootCategoryInputRef.current) rootCategoryInputRef.current.disabled = false;
    }
  };

  const handleAddRootCategory = () => {
    setInlineAddMode('root');
  };

  const handleRootInlineKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      const name = rootCategoryInputRef.current?.value?.trim();
      if (name) {
        rootCategoryInputRef.current.disabled = true;
        submitRootCategory(name);
      } else {
        setInlineAddMode(null);
      }
    }
    if (e.key === 'Escape') {
      setInlineAddMode(null);
    }
  };

  const handleRootInlineBlur = () => {
    if (rootCategoryInputRef.current?.disabled) return;
    const name = rootCategoryInputRef.current?.value?.trim();
    if (!name) {
      setInlineAddMode(null);
      return;
    }
    if (window.confirm('Создать категорию «' + name + '»?')) {
      rootCategoryInputRef.current.disabled = true;
      submitRootCategory(name);
    } else {
      setInlineAddMode(null);
    }
  };

  const handleAddSubcategory = () => {
    if (!selectedCategoryId) {
      window.alert('Выделите категорию!');
      return;
    }
    setInlineAddMode({ parentId: selectedCategoryId });
  };

  const handleSubmitSubcategory = async (parentId, name) => {
    if (!name?.trim()) return;
    try {
      await createSubcategory(parentId, name.trim());
      setInlineAddMode(null);
      onCategoriesUpdated?.();
    } catch (e) {
      window.alert(e.message || 'Ошибка сети');
      setInlineAddMode(null);
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

  const categoryContainsLesson = useCallback((cat, lessonId) => {
    if (!cat) return false;
    const lessons = cat.lessons || [];
    if (lessons.some((l) => l.id === lessonId)) return true;
    const subcategories = cat.subcategories || [];
    return subcategories.some((sub) => categoryContainsLesson(sub, lessonId));
  }, []);

  const filterCategoriesToLesson = useCallback((list, lessonId) => {
    return list
      .map((cat) => {
        const subFiltered = filterCategoriesToLesson(cat.subcategories || [], lessonId);
        const hasInSubs = subFiltered.length > 0;
        const lessons = (cat.lessons || []).filter((l) => l.id === lessonId);
        const hasHere = lessons.length > 0;
        if (!hasHere && !hasInSubs) return null;
        return {
          ...cat,
          subcategories: subFiltered,
          lessons: hasHere ? lessons : [],
        };
      })
      .filter(Boolean);
  }, []);

  const displayCategories = useMemo(() => {
    if (!mirrorsFilterLessonId) return categories;
    return filterCategoriesToLesson(categories, mirrorsFilterLessonId);
  }, [categories, mirrorsFilterLessonId, filterCategoriesToLesson]);

  useEffect(() => {
    if (isReadonly) return;
    fetch('/builder/clipboard/')
      .then((r) => r.json())
      .then((data) => {
        setClipboardData(data.empty ? null : data);
      })
      .catch(() => setClipboardData(null));
  }, [isReadonly]);

  const handleContextMenu = (e) => {
    if (isReadonly) return;
    const li = e.target.closest('li');
    if (!li) return;
    const categoryEl = li.closest('.kb-sidebar__category');
    const lessonItemEl = li.classList?.contains('kb-sidebar__lesson-item') ? li : null;
    let target = null;
    if (categoryEl && categoryEl === li) {
      const id = categoryEl.getAttribute('data-id');
      if (id) target = { type: 'category', id: String(id) };
    } else if (lessonItemEl) {
      const lessonId = lessonItemEl.getAttribute('data-lesson-id');
      const uncatId = lessonItemEl.getAttribute('data-id');
      const hasMirrors = lessonItemEl.hasAttribute('data-has-mirrors');
      const id = lessonId || (uncatId && uncatId.startsWith('uncat-') ? uncatId.replace('uncat-', '') : null);
      const parentCat = lessonItemEl.closest('.kb-sidebar__category');
      const parentCategoryId = parentCat ? parentCat.getAttribute('data-id') || '' : '';
      if (id) target = { type: 'lesson', id: String(id), parentCategoryId, hasMirrors: !!hasMirrors, isMirror: false };
    }
    if (target) {
      e.preventDefault();
      e.stopPropagation();
      setContextMenu({ visible: true, x: e.pageX, y: e.pageY, target });
    }
  };

  const closeContextMenu = useCallback(() => setContextMenu((c) => ({ ...c, visible: false })), []);

  const apiPost = (url, body) => {
    return fetch(url, {
      method: 'POST',
      headers: {
        'X-CSRFToken': getCsrfToken(),
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    }).then((r) => r.json());
  };

  const handleCopy = useCallback(() => {
    if (!contextMenu.target) return;
    const { type, id } = contextMenu.target;
    apiPost('/builder/copy/', { id, type }).then((data) => {
      if (data.error) {
        window.alert('Ошибка: ' + data.error);
        return;
      }
      setClipboardData({ id, type, action: 'copy' });
      closeContextMenu();
    }).catch(() => window.alert('Ошибка сети'));
  }, [contextMenu.target, closeContextMenu]);

  const handleCut = useCallback(() => {
    if (!contextMenu.target) return;
    const { type, id } = contextMenu.target;
    apiPost('/builder/cut/', { id, type }).then((data) => {
      if (data.error) {
        window.alert('Ошибка: ' + data.error);
        return;
      }
      setClipboardData({ id, type, action: 'cut' });
      closeContextMenu();
    }).catch(() => window.alert('Ошибка сети'));
  }, [contextMenu.target, closeContextMenu]);

  const handlePaste = useCallback(() => {
    if (!clipboardData || !contextMenu.target) return;
    const { type, id, parentCategoryId } = contextMenu.target;
    let targetCategory = type === 'category' ? id : (parentCategoryId || '');
    if (clipboardData.type === 'category' && (type === 'lesson' || !targetCategory)) {
      if (!window.confirm('Категория будет создана в корне дерева. Продолжить?')) {
        closeContextMenu();
        return;
      }
      targetCategory = '';
    }
    apiPost('/builder/paste/', { target_category: targetCategory }).then((data) => {
      if (data.error) {
        window.alert('Ошибка: ' + data.error);
        return;
      }
      setClipboardData(null);
      closeContextMenu();
      window.location.reload();
    }).catch(() => window.alert('Ошибка сети'));
  }, [clipboardData, contextMenu.target, closeContextMenu]);

  const handleMirror = useCallback(() => {
    if (!contextMenu.target || contextMenu.target.type !== 'lesson') return;
    setMirrorSourceLessonId(contextMenu.target.id);
    closeContextMenu();
    window.alert('Теперь выберите категорию, куда вставить зеркало, через контекстное меню!');
  }, [contextMenu.target, closeContextMenu]);

  const handleMirrorHere = useCallback(() => {
    if (!contextMenu.target || contextMenu.target.type !== 'category' || !mirrorSourceLessonId) return;
    apiPost('/builder/mirror/', {
      lesson_id: mirrorSourceLessonId,
      category_id: contextMenu.target.id,
    }).then((data) => {
      if (data.error) {
        window.alert('Ошибка: ' + data.error);
        return;
      }
      setMirrorSourceLessonId(null);
      closeContextMenu();
      window.alert('Зеркало создано!');
      window.location.reload();
    }).catch(() => window.alert('Ошибка сети'));
  }, [contextMenu.target, mirrorSourceLessonId, closeContextMenu]);

  const openAssignmentModal = useCallback((lessonIds, categoryName) => {
    const url = '/user_management/';
    const params = new URLSearchParams({ assign_lessons: lessonIds.join(','), from: 'builder' });
    window.open(`${url}?${params}`, '_blank', 'noopener');
  }, []);

  const handleAssign = useCallback(() => {
    if (!contextMenu.target) return;
    const { type, id } = contextMenu.target;
    closeContextMenu();
    if (type === 'lesson') {
      openAssignmentModal([id]);
      return;
    }
    if (type === 'category') {
      fetch(`/builder/api/categories/${id}/lessons/`)
        .then((r) => r.json())
        .then((data) => {
          if (data.error || !data.lesson_ids?.length) {
            window.alert(data.error || 'В категории нет уроков');
            return;
          }
          openAssignmentModal(data.lesson_ids, data.category_name);
        })
        .catch(() => window.alert('Ошибка загрузки уроков'));
    }
  }, [contextMenu.target, closeContextMenu, openAssignmentModal]);

  const handleShowAllMirrors = useCallback(() => {
    if (!contextMenu.target || contextMenu.target.type !== 'lesson') return;
    setMirrorsFilterLessonId(contextMenu.target.id);
    closeContextMenu();
  }, [contextMenu.target, closeContextMenu]);

  const handleHideMirrors = useCallback(() => {
    setMirrorsFilterLessonId(null);
    closeContextMenu();
  }, [closeContextMenu]);

  const handleEditCategoryOrLesson = () => {
    if (selectedLessonId) {
      navigate(`/builder/lesson/${selectedLessonId}/edit`);
      return;
    }
    if (!selectedCategoryId) {
      window.alert('Выделите категорию или урок!');
      return;
    }
    setEditingCategoryId(selectedCategoryId);
  };

  const handleRenameCategory = async (categoryId, newName) => {
    if (!newName?.trim()) return;
    try {
      await renameCategory(categoryId, newName);
      setEditingCategoryId(null);
      onCategoriesUpdated?.();
    } catch (e) {
      window.alert(e.message || 'Ошибка сети');
    }
  };

  const handleCancelEditCategory = () => {
    setEditingCategoryId(null);
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

      <div className="kb-sidebar__content" onContextMenu={handleContextMenu}>
        {mirrorsFilterLessonId && (
          <div className="kb-sidebar__mirrors-filter-hint">
            <button
              type="button"
              className="kb-sidebar__mirrors-filter-reset"
              onClick={() => setMirrorsFilterLessonId(null)}
            >
              Сбросить фильтр зеркал
            </button>
          </div>
        )}
        {activeTab === TAB_CATEGORIES && (
          <div className="kb-sidebar__scroll">
            <ul className="kb-sidebar__category-list" role="list">
              {inlineAddMode === 'root' && (
                <li className="kb-sidebar__category kb-sidebar__category--inline-add">
                  <div className="kb-sidebar__category-header">
                    <input
                      ref={rootCategoryInputRef}
                      type="text"
                      className="kb-sidebar__inline-input"
                      placeholder="Название категории..."
                      onKeyDown={handleRootInlineKeyDown}
                      onBlur={handleRootInlineBlur}
                      aria-label="Название категории"
                    />
                  </div>
                </li>
              )}
              {displayCategories.map((cat) => (
                <CategoryTree
                  key={cat.id}
                  category={cat}
                  selectedLessonId={selectedLessonId}
                  searchQuery={searchQuery || ''}
                  selectedCategoryId={selectedCategoryId}
                  onCategorySelect={handleCategorySelect}
                  onLessonSelect={handleLessonSelect}
                  inlineAddParentId={inlineAddMode?.parentId ?? null}
                  onSubmitSubcategory={handleSubmitSubcategory}
                  onCancelSubcategory={() => setInlineAddMode(null)}
                  editingCategoryId={editingCategoryId}
                  onRenameCategory={handleRenameCategory}
                  onCancelEditCategory={handleCancelEditCategory}
                />
              ))}
            </ul>
            {displayCategories.length === 0 && !inlineAddMode && (
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
                  data-id={`uncat-${lesson.id}`}
                  data-has-mirrors={lesson.has_mirrors ? '1' : undefined}
                >
                  <button
                    type="button"
                    className="kb-sidebar__lesson-link"
                    onClick={() => handleLessonSelect(lesson.id)}
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
            className="kb-sidebar__category-actions-btn kb-sidebar__category-actions-btn--primary"
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
            disabled={!selectedCategoryId}
          >
            +
          </button>
          <button
            type="button"
            className="kb-sidebar__category-actions-btn"
            onClick={handleEditCategoryOrLesson}
            title="Редактировать категорию (название) или открыть редактирование урока"
            disabled={!selectedCategoryId && !selectedLessonId}
          >
            v
          </button>
          <button
            type="button"
            className="kb-sidebar__category-actions-btn"
            onClick={handleDeleteCategoryOrLesson}
            title="Удалить категорию или урок"
            disabled={!selectedCategoryId && !selectedLessonId}
          >
            x
          </button>
          <button
            type="button"
            className="kb-sidebar__category-actions-btn kb-sidebar__category-actions-btn--primary"
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

      {!isReadonly && (
        <KnowledgeBaseContextMenu
          visible={contextMenu.visible}
          position={{ x: contextMenu.x, y: contextMenu.y }}
          target={contextMenu.target}
          clipboardData={clipboardData}
          mirrorSourceLessonId={mirrorSourceLessonId}
          mirrorsFilterActive={!!mirrorsFilterLessonId}
          onClose={closeContextMenu}
          onCopy={handleCopy}
          onCut={handleCut}
          onPaste={handlePaste}
          onMirror={handleMirror}
          onMirrorHere={handleMirrorHere}
          onAssign={handleAssign}
          onShowAllMirrors={handleShowAllMirrors}
          onHideMirrors={handleHideMirrors}
        />
      )}
    </aside>
  );
};

export default KnowledgeBaseSidebar;
