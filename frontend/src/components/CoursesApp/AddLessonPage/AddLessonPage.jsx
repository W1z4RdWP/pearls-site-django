import { useState, useEffect, useCallback, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { fetchAddLessonData, addLessonMaterials } from '../../../api/courses_api';
import CategoryTreeItem from './CategoryTreeItem/CategoryTreeItem';
import './AddLessonPage.css';

const TABS = [
  { id: 'categories', label: 'Категории' },
  { id: 'uncategorized', label: 'Без категории' },
  { id: 'tests', label: 'Тесты/Задания' },
];

const getItemId = (type, id) => {
  if (type === 'uncategorized') return `uncategorized_${id}`;
  return `${type}_${id}`;
};

const getTypeLabel = (type) => {
  switch (type) {
    case 'category': return 'Категория';
    case 'quiz': return 'Тест';
    case 'homework': return 'Задание';
    case 'uncategorized': return 'Урок (без категории)';
    default: return 'Урок';
  }
};

const getTypeIcon = (type) => {
  switch (type) {
    case 'category': return '📁';
    case 'quiz': return '🧪';
    case 'homework': return '📝';
    case 'uncategorized': return '📄';
    default: return '📄';
  }
};

const AddLessonPage = () => {
  const { slug } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedItems, setSelectedItems] = useState([]);
  const [activeTab, setActiveTab] = useState('categories');
  const [searchQuery, setSearchQuery] = useState('');
  const [highlightedId, setHighlightedId] = useState(null);
  const [selectedCategoryId, setSelectedCategoryId] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const selectedIdsSet = useMemo(
    () => new Set(selectedItems.map((i) => i.itemId)),
    [selectedItems]
  );

  const loadData = useCallback(async () => {
    if (!slug) return;
    setLoading(true);
    setError(null);
    try {
      const result = await fetchAddLessonData(slug);
      setData(result);
    } catch (err) {
      setError(err.message || 'Ошибка загрузки данных');
    } finally {
      setLoading(false);
    }
  }, [slug]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleSelect = useCallback((type, id, title) => {
    const itemId = getItemId(type, id);
    setHighlightedId(itemId);
    if (type === 'category') {
      setSelectedCategoryId(id);
    } else {
      setSelectedCategoryId(null);
    }
  }, []);

  const handleDoubleClick = useCallback((type, id, title) => {
    const itemId = getItemId(type, id);
    setSelectedItems((prev) => {
      const has = prev.some((i) => i.itemId === itemId);
      if (has) return prev.filter((i) => i.itemId !== itemId);
      return [...prev, { itemId, type, title }];
    });
  }, []);

  const handleRemoveSelected = useCallback((itemId) => {
    setSelectedItems((prev) => prev.filter((i) => i.itemId !== itemId));
  }, []);

  const handleSubmit = useCallback(async () => {
    if (selectedItems.length === 0) return;
    setSubmitting(true);
    try {
      const result = await addLessonMaterials(slug, selectedItems.map((i) => i.itemId));
      if (result.redirect_url) {
        navigate(result.redirect_url);
      } else {
        await loadData();
      }
    } catch (err) {
      alert(err.message || 'Ошибка при добавлении материалов');
    } finally {
      setSubmitting(false);
    }
  }, [slug, selectedItems, navigate, loadData]);

  const handleCreateLesson = useCallback(() => {
    if (!selectedCategoryId) return;
    const returnUrl = encodeURIComponent(window.location.href);
    navigate(`/builder/add/${selectedCategoryId}/?return_url=${returnUrl}`);
  }, [selectedCategoryId, navigate]);

  const handleCancel = useCallback(() => {
    navigate(-1);
  }, [navigate]);

  if (loading) {
    return (
      <main className="add-lesson-page" aria-label="Загрузка">
        <div className="add-lesson-page__loading">Загрузка…</div>
      </main>
    );
  }

  if (error) {
    return (
      <main className="add-lesson-page" aria-label="Ошибка">
        <div className="add-lesson-page__error" role="alert">{error}</div>
        <button type="button" className="add-lesson-page__back" onClick={() => navigate(-1)}>
          Назад
        </button>
      </main>
    );
  }

  if (!data) return null;

  const {
    course,
    categories_data: categoriesData = [],
    uncategorized_lessons: uncategorizedLessons = [],
    all_quizzes: allQuizzes = [],
    all_homeworks: allHomeworks = [],
  } = data;

  const panelTitle = TABS.find((t) => t.id === activeTab)?.label || 'Материалы';

  const filterBySearch = (list, getText) => {
    if (!searchQuery.trim()) return list;
    const q = searchQuery.toLowerCase();
    return list.filter((item) => (getText(item) || '').toLowerCase().includes(q));
  };

  const filteredUncategorized = filterBySearch(uncategorizedLessons, (l) => l.title);
  const filteredQuizzes = filterBySearch(allQuizzes, (q) => q.name);
  const filteredHomeworks = filterBySearch(allHomeworks, (h) => h.title);
  const searchCount = activeTab === 'categories'
    ? null
    : activeTab === 'uncategorized'
      ? filteredUncategorized.length
      : filteredQuizzes.length + filteredHomeworks.length;

  return (
    <main className="add-lesson-page" aria-label="Выбрать материалы для курса">
      <div className="add-lesson-page__modal">
        <header className="add-lesson-page__header">
          <h2 className="add-lesson-page__title">Выбрать материалы</h2>
          <button
            type="button"
            className="add-lesson-page__close"
            onClick={handleCancel}
            aria-label="Закрыть"
          >
            &times;
          </button>
        </header>

        <div className="add-lesson-page__body">
          <div className="add-lesson-page__left">
            <div className="add-lesson-page__panel-header">
              <div className="add-lesson-page__tabs">
                {TABS.map((tab) => (
                  <button
                    key={tab.id}
                    type="button"
                    className={`add-lesson-page__tab ${activeTab === tab.id ? 'add-lesson-page__tab--active' : ''}`}
                    onClick={() => { setActiveTab(tab.id); setSearchQuery(''); }}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>
              <div className="add-lesson-page__panel-row">
                <span className="add-lesson-page__panel-title">{panelTitle}</span>
                <div className="add-lesson-page__search-wrap">
                  <span className="add-lesson-page__search-icon" aria-hidden="true">🔍</span>
                  <input
                    type="text"
                    className="add-lesson-page__search"
                    placeholder="Поиск"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    aria-label="Поиск"
                  />
                </div>
              </div>
              {searchQuery && searchCount !== null && (
                <p className="add-lesson-page__search-results">
                  Найдено: <span>{searchCount}</span>
                </p>
              )}
            </div>
            <div className="add-lesson-page__panel-content">
              {activeTab === 'categories' && (
                <ul className="add-lesson-page__category-tree">
                  {categoriesData.map((cat) => (
                    <CategoryTreeItem
                      key={cat.id}
                      category={cat}
                      selectedIds={selectedIdsSet}
                      highlightedId={highlightedId}
                      onSelect={handleSelect}
                      onDoubleClick={handleDoubleClick}
                      searchQuery={searchQuery.trim() || null}
                    />
                  ))}
                </ul>
              )}
              {activeTab === 'uncategorized' && (
                <ul className="add-lesson-page__list">
                  {filteredUncategorized.length === 0 ? (
                    <li className="add-lesson-page__empty-item">Нет уроков без категории</li>
                  ) : (
                    filteredUncategorized.map((lesson) => {
                      const itemId = getItemId('uncategorized', lesson.id);
                      const isSelected = selectedIdsSet.has(itemId) || highlightedId === itemId;
                      return (
                        <li
                          key={lesson.id}
                          className={`add-lesson-page__list-item ${isSelected ? 'add-lesson-page__list-item--selected' : ''}`}
                          data-lesson-id={lesson.id}
                          onClick={() => handleSelect('uncategorized', lesson.id, lesson.title)}
                          onDoubleClick={() => handleDoubleClick('uncategorized', lesson.id, lesson.title)}
                          role="button"
                          tabIndex={0}
                        >
                          <a className="add-lesson-page__list-link" title={lesson.title}>{lesson.title}</a>
                        </li>
                      );
                    })
                  )}
                </ul>
              )}
              {activeTab === 'tests' && (
                <div className="add-lesson-page__tests">
                  <section className="add-lesson-page__tests-section">
                    <h3 className="add-lesson-page__tests-heading">
                      <i className="fas fa-question-circle" aria-hidden="true" /> Тесты
                    </h3>
                    <ul className="add-lesson-page__list">
                      {filteredQuizzes.length === 0 ? (
                        <li className="add-lesson-page__empty-item">Нет доступных тестов</li>
                      ) : (
                        filteredQuizzes.map((quiz) => {
                          const itemId = `quiz_${quiz.id}`;
                          const isSelected = selectedIdsSet.has(itemId) || highlightedId === itemId;
                          return (
                            <li
                              key={quiz.id}
                              className={`add-lesson-page__list-item ${isSelected ? 'add-lesson-page__list-item--selected' : ''}`}
                              data-quiz-id={quiz.id}
                              onClick={() => handleSelect('quiz', quiz.id, quiz.name)}
                              onDoubleClick={() => handleDoubleClick('quiz', quiz.id, quiz.name)}
                              role="button"
                              tabIndex={0}
                            >
                              <a className="add-lesson-page__list-link" title={quiz.name}>{quiz.name}</a>
                            </li>
                          );
                        })
                      )}
                    </ul>
                  </section>
                  <section className="add-lesson-page__tests-section">
                    <h3 className="add-lesson-page__tests-heading">
                      <i className="fas fa-tasks" aria-hidden="true" /> Задания
                    </h3>
                    <ul className="add-lesson-page__list">
                      {filteredHomeworks.length === 0 ? (
                        <li className="add-lesson-page__empty-item">Нет доступных заданий</li>
                      ) : (
                        filteredHomeworks.map((hw) => {
                          const itemId = `homework_${hw.id}`;
                          const title = hw.title || hw.name;
                          const isSelected = selectedIdsSet.has(itemId) || highlightedId === itemId;
                          return (
                            <li
                              key={hw.id}
                              className={`add-lesson-page__list-item add-lesson-page__list-item--homework ${isSelected ? 'add-lesson-page__list-item--selected' : ''}`}
                              data-homework-id={hw.id}
                              onClick={() => handleSelect('homework', hw.id, title)}
                              onDoubleClick={() => handleDoubleClick('homework', hw.id, title)}
                              role="button"
                              tabIndex={0}
                            >
                              <a className="add-lesson-page__list-link add-lesson-page__list-link--homework" title={title}>{title}</a>
                            </li>
                          );
                        })
                      )}
                    </ul>
                  </section>
                </div>
              )}
            </div>
          </div>

          <div className="add-lesson-page__right">
            <div className="add-lesson-page__panel-header add-lesson-page__panel-header--right">
              Выбранные материалы
            </div>
            <div className="add-lesson-page__panel-content">
              {selectedItems.length === 0 ? (
                <div className="add-lesson-page__empty-state">
                  <div className="add-lesson-page__empty-icon">📁</div>
                  <p>Выберите материалы для добавления в курс</p>
                </div>
              ) : (
                <ul className="add-lesson-page__selected-list">
                  {selectedItems.map((item) => (
                    <li key={item.itemId} className="add-lesson-page__selected-item" data-item-id={item.itemId}>
                      <span className="add-lesson-page__selected-icon">{getTypeIcon(item.type)}</span>
                      <div className="add-lesson-page__selected-content">
                        <div className="add-lesson-page__selected-title">{item.title}</div>
                        <div className="add-lesson-page__selected-type">{getTypeLabel(item.type)}</div>
                      </div>
                      <button
                        type="button"
                        className="add-lesson-page__remove-item"
                        onClick={() => handleRemoveSelected(item.itemId)}
                        aria-label={`Удалить ${item.title}`}
                      >
                        &times;
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </div>

        <footer className="add-lesson-page__footer">
          <button type="button" className="add-lesson-page__btn add-lesson-page__btn--secondary" onClick={handleCancel}>
            Отмена
          </button>
          {selectedCategoryId && (
            <button
              type="button"
              className="add-lesson-page__btn add-lesson-page__btn--outline"
              onClick={handleCreateLesson}
            >
              <span className="add-lesson-page__btn-icon">📄</span> Создать урок
            </button>
          )}
          <button
            type="button"
            className="add-lesson-page__btn add-lesson-page__btn--primary"
            disabled={selectedItems.length === 0 || submitting}
            onClick={handleSubmit}
          >
            {submitting ? 'Добавление…' : 'Продолжить'}
          </button>
        </footer>
      </div>
    </main>
  );
};

export default AddLessonPage;
