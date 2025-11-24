let selectedItems = new Set();

function toggleCategory(element) {
    const categoryItem = element.closest('.category-block');
    const subcategoryList = categoryItem.querySelector('.subcategory-list');
    const lessonList = categoryItem.querySelector('.lesson-list');
    const arrow = element.querySelector('.toggle-arrow');
    
    if (subcategoryList) {
        const isVisible = subcategoryList.style.display !== 'none';
        subcategoryList.style.display = isVisible ? 'none' : 'block';
        if (arrow) {
            arrow.classList.toggle('expanded', !isVisible);
            arrow.innerHTML = !isVisible ? '−' : '+'; // минус (открыто) или плюс (закрыто)
        }
    }
    
    if (lessonList) {
        const isVisible = lessonList.style.display !== 'none';
        lessonList.style.display = isVisible ? 'none' : 'block';
        if (arrow) {
            arrow.classList.toggle('expanded', !isVisible);
            arrow.innerHTML = !isVisible ? '−' : '+'; // минус (открыто) или плюс (закрыто)
        }
    }
}

// Переменная для хранения выбранной категории
let selectedCategoryId = null;

// Обработчик одиночного клика - только выделение
function selectItem(element, type, id, title) {
    const itemId = `${type}_${id}`;
    
    // Убираем выделение со всех элементов того же типа
    const allItems = document.querySelectorAll(`.category-block .category-header, .lesson-li`);
    allItems.forEach(item => {
        if (item !== element) {
            item.classList.remove('selected');
        }
    });
    
    // Всегда выделяем текущий элемент
    element.classList.add('selected');
    
    // Показываем кнопку "Листочек" в футере для категорий
    const createLessonBtn = document.getElementById('createLessonBtn');
    if (type === 'category') {
        selectedCategoryId = id;
        if (createLessonBtn) {
            createLessonBtn.style.display = 'inline-block';
        }
    } else {
        // Скрываем кнопку при выборе урока
        selectedCategoryId = null;
        if (createLessonBtn) {
            createLessonBtn.style.display = 'none';
        }
    }
}

// Обработчик двойного клика - добавление/удаление из выбранных
function handleDoubleClick(element, type, id, title) {
    const itemId = `${type}_${id}`;
    
    if (selectedItems.has(itemId)) {
        // Удаляем из выбранных
        selectedItems.delete(itemId);
        element.classList.remove('selected');
        removeSelectedItem(itemId);
    } else {
        // Добавляем в выбранные
        selectedItems.add(itemId);
        element.classList.add('selected');
        addSelectedItem(itemId, type, title);
    }
    
    updateForm();
}

function addSelectedItem(itemId, type, title) {
    const selectedItemsList = document.getElementById('selectedItems');
    const emptyState = selectedItemsList.querySelector('.empty-state');
    
    if (emptyState) {
        emptyState.remove();
    }
    
    const item = document.createElement('li');
    item.className = 'selected-item';
    item.dataset.itemId = itemId;
    
    const icon = type === 'category' ? '📁' : (type === 'quiz' ? '🧪' : '📄');
    const typeText = type === 'category' ? 'Категория' : (type === 'uncategorized' ? 'Урок (без категории)' : (type === 'quiz' ? 'Тест' : 'Урок'));
    
    item.innerHTML = `
        <span class="selected-item-icon">${icon}</span>
        <div class="selected-item-content">
            <div class="selected-item-title">${title}</div>
            <div class="selected-item-type">${typeText}</div>
        </div>
        <button type="button" class="remove-item" onclick="removeSelectedItem('${itemId}')">&times;</button>
    `;
    
    selectedItemsList.appendChild(item);
}

function removeSelectedItem(itemId) {
    const item = document.querySelector(`[data-item-id="${itemId}"]`);
    if (item) {
        item.remove();
    }
    
    // Если больше нет выбранных элементов, показываем пустое состояние
    const selectedItemsList = document.getElementById('selectedItems');
    if (selectedItemsList.children.length === 0) {
        const emptyState = document.createElement('li');
        emptyState.className = 'empty-state';
        emptyState.innerHTML = `
            <div class="empty-state-icon">📁</div>
            <div>Выберите материалы для добавления в курс</div>
        `;
        selectedItemsList.appendChild(emptyState);
    }
    
    // Убираем выделение с элемента в левой панели
    const [type, id] = itemId.split('_');
    if (type === 'category') {
        const leftPanelItem = document.querySelector(`[data-category-id="${id}"] .category-header`);
        if (leftPanelItem) {
            leftPanelItem.classList.remove('selected');
        }
    } else if (type === 'lesson') {
        const leftPanelItem = document.querySelector(`[data-lesson-id="${id}"]`);
        if (leftPanelItem) {
            leftPanelItem.classList.remove('selected');
        }
    } else if (type === 'uncategorized') {
        const leftPanelItem = document.querySelector(`#uncategorized-block [data-lesson-id="${id}"]`);
        if (leftPanelItem) {
            leftPanelItem.classList.remove('selected');
        }
    } else if (type === 'quiz') {
        const leftPanelItem = document.querySelector(`#tests-block [data-quiz-id="${id}"]`);
        if (leftPanelItem) {
            leftPanelItem.classList.remove('selected');
        }
    }
    
    selectedItems.delete(itemId);
    updateForm();
}

function updateForm() {
    const input = document.getElementById('selectedItemsInput');
    const button = document.getElementById('addButton');
    
    input.value = Array.from(selectedItems).join(',');
    button.disabled = selectedItems.size === 0;
}

// Функция для подсветки найденного текста
function highlightText(element, searchTerm) {
    if (!searchTerm) {
        // Убираем подсветку
        element.innerHTML = element.innerHTML.replace(/<mark class="search-highlight">(.*?)<\/mark>/g, '$1');
        return;
    }
    
    const text = element.textContent;
    const regex = new RegExp(`(${searchTerm.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
    element.innerHTML = text.replace(regex, '<mark class="search-highlight">$1</mark>');
}

// Функция поиска
function performSearch(searchTerm) {
    const searchTermLower = searchTerm.toLowerCase();
    const searchResults = document.getElementById('searchResults');
    const resultsCount = document.getElementById('resultsCount');
    
    // Определяем активную вкладку
    const categoriesBlock = document.getElementById('categories-block');
    const uncatBlock = document.getElementById('uncategorized-block');
    const testsBlock = document.getElementById('tests-block');
    
    const activeTab = categoriesBlock.style.display !== 'none' ? 'categories' :
                      uncatBlock.style.display !== 'none' ? 'uncategorized' : 'tests';
    
    if (activeTab === 'tests') {
        // Поиск по тестам
        const testItems = testsBlock.querySelectorAll('.lesson-li');
        
        testItems.forEach(item => {
            const title = item.querySelector('.lesson-link');
            if (title) highlightText(title, '');
        });
        
        if (!searchTerm) {
            testItems.forEach(item => item.style.display = 'block');
            searchResults.style.display = 'none';
            return;
        }
        
        let foundCount = 0;
        testItems.forEach(item => {
            const title = item.querySelector('.lesson-link');
            const titleText = title.textContent.toLowerCase();
            
            if (titleText.includes(searchTermLower)) {
                item.style.display = 'block';
                highlightText(title, searchTerm);
                foundCount++;
            } else {
                item.style.display = 'none';
            }
        });
        
        resultsCount.textContent = foundCount;
        searchResults.style.display = 'block';
        
    } else if (activeTab === 'uncategorized') {
        // Поиск по урокам без категории
        const lessonItems = uncatBlock.querySelectorAll('.lesson-li');
        
        lessonItems.forEach(item => {
            const title = item.querySelector('.lesson-link');
            if (title) highlightText(title, '');
        });
        
        if (!searchTerm) {
            lessonItems.forEach(item => item.style.display = 'block');
            searchResults.style.display = 'none';
            return;
        }
        
        let foundCount = 0;
        lessonItems.forEach(item => {
            const title = item.querySelector('.lesson-link');
            const titleText = title.textContent.toLowerCase();
            
            if (titleText.includes(searchTermLower)) {
                item.style.display = 'block';
                highlightText(title, searchTerm);
                foundCount++;
            } else {
                item.style.display = 'none';
            }
        });
        
        resultsCount.textContent = foundCount;
        searchResults.style.display = 'block';
        
    } else {
        // Поиск по категориям (оригинальная логика)
        const categoryItems = categoriesBlock.querySelectorAll('.category-block');
        const lessonItems = categoriesBlock.querySelectorAll('.lesson-li');
        
        // Скрываем все элементы по умолчанию и убираем подсветку
        categoryItems.forEach(item => {
            item.style.display = 'none';
            const title = item.querySelector('.category-title');
            if (title) highlightText(title, '');
        });
        lessonItems.forEach(item => {
            item.style.display = 'none';
            const title = item.querySelector('.lesson-link');
            if (title) highlightText(title, '');
        });
        
        if (!searchTerm) {
            // Если поиск пустой, показываем все и скрываем счетчик
            categoryItems.forEach(item => {
                item.style.display = 'block';
            });
            lessonItems.forEach(item => {
                item.style.display = 'block';
            });
            searchResults.style.display = 'none';
            return;
        }
        
        let foundCount = 0;
        
        // Ищем совпадения в категориях
        categoryItems.forEach(categoryItem => {
            const categoryTitle = categoryItem.querySelector('.category-title');
            const categoryTitleText = categoryTitle.textContent.toLowerCase();
            const hasMatchingCategory = categoryTitleText.includes(searchTermLower);
            
            // Ищем совпадения в уроках этой категории
            const lessonItemsInCategory = categoryItem.querySelectorAll('.lesson-li');
            let hasMatchingLessons = false;
            
            lessonItemsInCategory.forEach(lessonItem => {
                const lessonTitle = lessonItem.querySelector('.lesson-link');
                const lessonTitleText = lessonTitle.textContent.toLowerCase();
                if (lessonTitleText.includes(searchTermLower)) {
                    lessonItem.style.display = 'block';
                    highlightText(lessonTitle, searchTerm);
                    hasMatchingLessons = true;
                    foundCount++;
                    
                    // Показываем родительскую категорию
                    categoryItem.style.display = 'block';
                    
                    // Показываем все родительские категории
                    let parentCategory = categoryItem.parentElement.closest('.category-block');
                    while (parentCategory) {
                        parentCategory.style.display = 'block';
                        parentCategory = parentCategory.parentElement.closest('.category-block');
                    }
                }
            });
            
            // Если категория совпадает, показываем её и все её уроки
            if (hasMatchingCategory) {
                categoryItem.style.display = 'block';
                highlightText(categoryTitle, searchTerm);
                foundCount++;
                lessonItemsInCategory.forEach(lessonItem => {
                    lessonItem.style.display = 'block';
                });
                
                // Показываем все родительские категории
                let parentCategory = categoryItem.parentElement.closest('.category-block');
                while (parentCategory) {
                    parentCategory.style.display = 'block';
                    parentCategory = parentCategory.parentElement.closest('.category-block');
                }
            }
        });
        
        // Показываем счетчик результатов
        resultsCount.textContent = foundCount;
        searchResults.style.display = 'block';
    }
}

// Функция для переключения вкладок
function switchTab(tabName) {
    const categoriesTab = document.getElementById('tab-categories');
    const uncatTab = document.getElementById('tab-uncat');
    const testsTab = document.getElementById('tab-tests');
    const categoriesBlock = document.getElementById('categories-block');
    const uncatBlock = document.getElementById('uncategorized-block');
    const testsBlock = document.getElementById('tests-block');
    const panelTitle = document.getElementById('panel-title');
    const searchInput = document.getElementById('searchInput');
    
    // Убираем активный класс со всех вкладок
    categoriesTab.classList.remove('active');
    uncatTab.classList.remove('active');
    testsTab.classList.remove('active');
    
    // Скрываем все блоки
    categoriesBlock.style.display = 'none';
    uncatBlock.style.display = 'none';
    testsBlock.style.display = 'none';
    
    // Очищаем поиск при переключении вкладок
    if (searchInput) {
        searchInput.value = '';
    }
    
    if (tabName === 'categories') {
        categoriesTab.classList.add('active');
        categoriesBlock.style.display = 'block';
        panelTitle.textContent = 'Категории';
    } else if (tabName === 'uncategorized') {
        uncatTab.classList.add('active');
        uncatBlock.style.display = 'block';
        panelTitle.textContent = 'Без категории';
    } else if (tabName === 'tests') {
        testsTab.classList.add('active');
        testsBlock.style.display = 'block';
        panelTitle.textContent = 'Тесты';
    }
    
    // Сбрасываем результаты поиска для новой вкладки
    performSearch('');
}

// Функция для создания урока в категории (доступна глобально)
window.createLessonInCategory = function(categoryId) {
    // Получаем текущий URL для возврата
    const returnUrl = encodeURIComponent(window.location.href);
    // Перенаправляем на форму создания урока с категорией и параметром возврата
    window.location.href = `/builder/add/${categoryId}/?return_url=${returnUrl}`;
};

// Обработчик клика на кнопку создания урока в футере
window.handleCreateLessonClick = function() {
    if (selectedCategoryId) {
        createLessonInCategory(selectedCategoryId);
    }
};

// Инициализация
document.addEventListener('DOMContentLoaded', function() {
    // Показываем все категории по умолчанию
    const categoryHeaders = document.querySelectorAll('.category-header');
    categoryHeaders.forEach(header => {
        const arrow = header.querySelector('.toggle-arrow');
        if (arrow) {
            arrow.classList.remove('expanded');
            arrow.innerHTML = '+'; // плюс для закрытого состояния
        }
        
        const categoryItem = header.closest('.category-block');
        const subcategoryList = categoryItem.querySelector('.subcategory-list');
        const lessonList = categoryItem.querySelector('.lesson-list');
        
        if (subcategoryList) subcategoryList.style.display = 'none';
        if (lessonList) lessonList.style.display = 'none';
    });
    
    // Используем делегирование событий для обработки кликов
    const clickTimers = new Map();
    
    // Скрываем кнопку создания урока при клике вне категорий
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.category-header') && 
            !e.target.closest('#createLessonBtn') &&
            !e.target.closest('.category-block')) {
            const createLessonBtn = document.getElementById('createLessonBtn');
            if (createLessonBtn) {
                createLessonBtn.style.display = 'none';
            }
            selectedCategoryId = null;
        }
    });
    
    // Обработчик кликов для категорий (делегирование)
    const categoriesBlock = document.getElementById('categories-block');
    if (categoriesBlock) {
        categoriesBlock.addEventListener('click', function(e) {
            const categoryHeader = e.target.closest('.category-header');
            if (!categoryHeader) return;
            
            // Пропускаем клик, если кликнули на стрелочку
            if (e.target.classList.contains('toggle-arrow')) {
                return;
            }
            
            const categoryItem = categoryHeader.closest('.category-block');
            const categoryId = categoryItem.dataset.categoryId;
            const categoryTitle = categoryHeader.querySelector('.category-title').textContent;
            
            const timerKey = `category_${categoryId}`;
            const existingTimer = clickTimers.get(timerKey);
            
            if (existingTimer) {
                clearTimeout(existingTimer);
                clickTimers.delete(timerKey);
                // Двойной клик - добавление/удаление
                handleDoubleClick(categoryHeader, 'category', categoryId, categoryTitle);
            } else {
                const timer = setTimeout(() => {
                    clickTimers.delete(timerKey);
                    // Одиночный клик - только выделение
                    selectItem(categoryHeader, 'category', categoryId, categoryTitle);
                }, 300);
                clickTimers.set(timerKey, timer);
            }
        });
    }
    
    // Обработчик кликов для уроков (делегирование)
    const leftPanel = document.querySelector('.left-panel');
    if (leftPanel) {
        leftPanel.addEventListener('click', function(e) {
            const lessonItem = e.target.closest('.lesson-li');
            if (!lessonItem) return;
            
            const lessonId = lessonItem.dataset.lessonId || lessonItem.dataset.quizId;
            if (!lessonId) return;
            
            const lessonTitle = lessonItem.querySelector('.lesson-link').textContent;
            let type = 'lesson';
            if (lessonItem.dataset.quizId) {
                type = 'quiz';
            } else if (lessonItem.closest('#uncategorized-block')) {
                type = 'uncategorized';
            }
            
            const timerKey = `${type}_${lessonId}`;
            const existingTimer = clickTimers.get(timerKey);
            
            if (existingTimer) {
                clearTimeout(existingTimer);
                clickTimers.delete(timerKey);
                // Двойной клик - добавление/удаление
                handleDoubleClick(lessonItem, type, lessonId, lessonTitle);
            } else {
                const timer = setTimeout(() => {
                    clickTimers.delete(timerKey);
                    // Одиночный клик - только выделение
                    selectItem(lessonItem, type, lessonId, lessonTitle);
                }, 300);
                clickTimers.set(timerKey, timer);
            }
        });
    }
    
    // Добавляем обработчик поиска с задержкой
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                performSearch(this.value);
            }, 300); // Задержка 300мс
        });
        
        // Добавляем обработчик для очистки поиска при нажатии Escape
        searchInput.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                this.value = '';
                performSearch('');
                this.blur();
            }
        });
    }
    
    // Добавляем обработчики для вкладок
    const categoriesTab = document.getElementById('tab-categories');
    const uncatTab = document.getElementById('tab-uncat');
    const testsTab = document.getElementById('tab-tests');
    
    if (categoriesTab) {
        categoriesTab.addEventListener('click', function() {
            switchTab('categories');
        });
    }
    
    if (uncatTab) {
        uncatTab.addEventListener('click', function() {
            switchTab('uncategorized');
        });
    }
    
    if (testsTab) {
        testsTab.addEventListener('click', function() {
            switchTab('tests');
        });
    }
});