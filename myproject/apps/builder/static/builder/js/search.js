/**
 * Поиск по дереву базы знаний
 * Ищет соответствия в категориях, подкатегориях и уроках
 */

class KnowledgeBaseSearch {
    constructor() {
        this.searchInput = document.getElementById('tree-search-input');
        this.categoriesBlock = document.getElementById('categories-block');
        this.uncategorizedBlock = document.getElementById('uncategorized-block');
        this.dictBlock = document.getElementById('dict-block');
        this.searchTimeout = null;
        this.originalState = new Map(); // Сохраняем исходное состояние для восстановления
        
        this.init();
    }

    init() {
        if (!this.searchInput) return;
        
        this.searchInput.addEventListener('input', (e) => {
            this.handleSearch(e.target.value);
        });

        this.searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.clearSearch();
            }
        });

        // Сохраняем исходное состояние при загрузке
        this.saveOriginalState();
    }

    /**
     * Сохраняет исходное состояние дерева для восстановления после очистки поиска
     */
    saveOriginalState() {
        const elements = [
            ...this.categoriesBlock.querySelectorAll('.category-block'),
            ...this.uncategorizedBlock.querySelectorAll('.category-block'),
            ...this.dictBlock.querySelectorAll('.category-block')
        ];

        elements.forEach(element => {
            const id = element.getAttribute('data-id');
            if (id) {
                this.originalState.set(id, {
                    display: element.style.display,
                    visibility: element.style.visibility,
                    expanded: this.isElementExpanded(element)
                });
            }
        });
    }

    /**
     * Проверяет, развернут ли элемент (есть ли видимые дочерние элементы)
     */
    isElementExpanded(element) {
        const subcategoryList = element.querySelector('.subcategory-list');
        const lessonList = element.querySelector('.lesson-list');
        
        if (subcategoryList) {
            return subcategoryList.style.display !== 'none';
        }
        if (lessonList) {
            return lessonList.style.display !== 'none';
        }
        return false;
    }

    /**
     * Обрабатывает поисковый запрос
     */
    handleSearch(query) {
        // Очищаем предыдущий таймаут
        if (this.searchTimeout) {
            clearTimeout(this.searchTimeout);
        }

        // Устанавливаем новый таймаут для дебаунса
        this.searchTimeout = setTimeout(() => {
            this.performSearch(query.trim());
        }, 300);
    }

    /**
     * Выполняет поиск
     */
    performSearch(query) {
        if (!query) {
            this.clearSearch();
            return;
        }

        const searchTerm = query.toLowerCase();
        
        // Ищем в категориях
        this.searchInCategories(searchTerm);
        
        // Ищем в уроках без категории
        this.searchInUncategorized(searchTerm);
        
        // Ищем в словаре
        this.searchInDictionary(searchTerm);
    }

    /**
     * Поиск в категориях и их содержимом
     */
    searchInCategories(searchTerm) {
        const categoryBlocks = this.categoriesBlock.querySelectorAll('.category-block');
        let hasMatches = false;

        categoryBlocks.forEach(block => {
            const categoryTitle = block.querySelector('.category-title');
            const categoryName = categoryTitle ? categoryTitle.textContent.toLowerCase() : '';
            
            // Проверяем соответствие в названии категории
            const categoryMatches = categoryName.includes(searchTerm);
            
            // Ищем в уроках этой категории
            const lessonMatches = this.searchInLessons(block, searchTerm);
            
            // Ищем в подкатегориях
            const subcategoryMatches = this.searchInSubcategories(block, searchTerm);
            
            const hasAnyMatch = categoryMatches || lessonMatches || subcategoryMatches;
            
            if (hasAnyMatch) {
                hasMatches = true;
                this.showElement(block);
                this.expandElement(block);
                
                // Подсвечиваем совпадения
                this.highlightMatches(block, searchTerm);
            } else {
                this.hideElement(block);
            }
        });

        // Показываем/скрываем блок категорий
        this.categoriesBlock.style.display = hasMatches ? 'block' : 'none';
    }

    /**
     * Поиск в уроках категории
     */
    searchInLessons(categoryBlock, searchTerm) {
        const lessons = categoryBlock.querySelectorAll('.lesson-li');
        let hasMatches = false;

        lessons.forEach(lesson => {
            const lessonLink = lesson.querySelector('.lesson-link');
            const lessonTitle = lessonLink ? lessonLink.textContent.toLowerCase() : '';
            
            if (lessonTitle.includes(searchTerm)) {
                hasMatches = true;
                this.showElement(lesson);
                this.highlightMatches(lesson, searchTerm);
            } else {
                this.hideElement(lesson);
            }
        });

        return hasMatches;
    }

    /**
     * Рекурсивный поиск в подкатегориях
     */
    searchInSubcategories(categoryBlock, searchTerm) {
        const subcategoryList = categoryBlock.querySelector('.subcategory-list');
        if (!subcategoryList) return false;

        const subcategories = subcategoryList.querySelectorAll('.category-block');
        let hasMatches = false;

        subcategories.forEach(subcategory => {
            const subcategoryTitle = subcategory.querySelector('.category-title');
            const subcategoryName = subcategoryTitle ? subcategoryTitle.textContent.toLowerCase() : '';
            
            const subcategoryMatches = subcategoryName.includes(searchTerm);
            const lessonMatches = this.searchInLessons(subcategory, searchTerm);
            const nestedMatches = this.searchInSubcategories(subcategory, searchTerm);
            
            const hasAnyMatch = subcategoryMatches || lessonMatches || nestedMatches;
            
            if (hasAnyMatch) {
                hasMatches = true;
                this.showElement(subcategory);
                this.expandElement(subcategory);
                this.highlightMatches(subcategory, searchTerm);
            } else {
                this.hideElement(subcategory);
            }
        });

        return hasMatches;
    }

    /**
     * Поиск в уроках без категории
     */
    searchInUncategorized(searchTerm) {
        const uncategorizedLessons = this.uncategorizedBlock.querySelectorAll('.category-block');
        let hasMatches = false;

        uncategorizedLessons.forEach(lesson => {
            const lessonLink = lesson.querySelector('.lesson-link');
            const lessonTitle = lessonLink ? lessonLink.textContent.toLowerCase() : '';
            
            if (lessonTitle.includes(searchTerm)) {
                hasMatches = true;
                this.showElement(lesson);
                this.highlightMatches(lesson, searchTerm);
            } else {
                this.hideElement(lesson);
            }
        });

        this.uncategorizedBlock.style.display = hasMatches ? 'block' : 'none';
    }

    /**
     * Поиск в словаре
     */
    searchInDictionary(searchTerm) {
        const dictSections = this.dictBlock.querySelectorAll('.category-block');
        let hasMatches = false;

        dictSections.forEach(section => {
            const sectionLink = section.querySelector('.dict-section-link');
            const sectionName = sectionLink ? sectionLink.textContent.toLowerCase() : '';
            
            if (sectionName.includes(searchTerm)) {
                hasMatches = true;
                this.showElement(section);
                this.highlightMatches(section, searchTerm);
            } else {
                this.hideElement(section);
            }
        });

        this.dictBlock.style.display = hasMatches ? 'block' : 'none';
    }

    /**
     * Показывает элемент
     */
    showElement(element) {
        element.style.display = '';
        element.style.visibility = 'visible';
    }

    /**
     * Скрывает элемент
     */
    hideElement(element) {
        element.style.display = 'none';
    }

    /**
     * Разворачивает элемент (показывает дочерние элементы)
     */
    expandElement(element) {
        const subcategoryList = element.querySelector('.subcategory-list');
        const lessonList = element.querySelector('.lesson-list');
        
        if (subcategoryList) {
            subcategoryList.style.display = 'block';
        }
        if (lessonList) {
            lessonList.style.display = 'block';
        }
    }

    /**
     * Подсвечивает совпадения в тексте
     */
    highlightMatches(element, searchTerm) {
        // Убираем предыдущие подсветки
        this.removeHighlights(element);
        
        const textElements = element.querySelectorAll('.category-title, .lesson-link, .dict-section-link');
        
        textElements.forEach(textElement => {
            const originalText = textElement.textContent;
            const lowerText = originalText.toLowerCase();
            const index = lowerText.indexOf(searchTerm);
            
            if (index !== -1) {
                const before = originalText.substring(0, index);
                const match = originalText.substring(index, index + searchTerm.length);
                const after = originalText.substring(index + searchTerm.length);
                
                textElement.innerHTML = `${before}<mark class="search-highlight">${match}</mark>${after}`;
            }
        });
    }

    /**
     * Убирает подсветку совпадений
     */
    removeHighlights(element) {
        const highlights = element.querySelectorAll('.search-highlight');
        highlights.forEach(highlight => {
            const parent = highlight.parentNode;
            parent.replaceChild(document.createTextNode(highlight.textContent), highlight);
            parent.normalize();
        });
    }

    /**
     * Очищает поиск и восстанавливает исходное состояние
     */
    clearSearch() {
        this.searchInput.value = '';
        
        // Восстанавливаем исходное состояние всех элементов
        this.originalState.forEach((state, id) => {
            const element = document.querySelector(`[data-id="${id}"]`);
            if (element) {
                element.style.display = state.display;
                element.style.visibility = state.visibility;
                
                // Восстанавливаем состояние развернутости
                const subcategoryList = element.querySelector('.subcategory-list');
                const lessonList = element.querySelector('.lesson-list');
                
                if (subcategoryList) {
                    subcategoryList.style.display = state.expanded ? 'block' : 'none';
                }
                if (lessonList) {
                    lessonList.style.display = state.expanded ? 'block' : 'none';
                }
            }
        });

        // Убираем все подсветки
        const allHighlights = document.querySelectorAll('.search-highlight');
        allHighlights.forEach(highlight => {
            const parent = highlight.parentNode;
            parent.replaceChild(document.createTextNode(highlight.textContent), highlight);
            parent.normalize();
        });

        // Показываем все блоки
        this.categoriesBlock.style.display = 'block';
        this.uncategorizedBlock.style.display = 'none';
        this.dictBlock.style.display = 'none';
    }
}

// Инициализация поиска при загрузке DOM
document.addEventListener('DOMContentLoaded', () => {
    new KnowledgeBaseSearch();
});
