let selectedItems = new Set();

function toggleCategory(element) {
    const categoryItem = element.closest('.category-item');
    const subcategoryList = categoryItem.querySelector('.subcategory-list');
    const lessonList = categoryItem.querySelector('.lesson-list');
    const arrow = element.querySelector('.toggle-arrow');
    
    if (subcategoryList) {
        const isVisible = subcategoryList.style.display !== 'none';
        subcategoryList.style.display = isVisible ? 'none' : 'block';
        if (arrow) arrow.classList.toggle('expanded', !isVisible);
    }
    
    if (lessonList) {
        const isVisible = lessonList.style.display !== 'none';
        lessonList.style.display = isVisible ? 'none' : 'block';
        if (arrow) arrow.classList.toggle('expanded', !isVisible);
    }
}

function selectItem(element, type, id, title) {
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
    const categoryItems = document.querySelectorAll('.category-item');
    const lessonItems = document.querySelectorAll('.lesson-item');
    const searchResults = document.getElementById('searchResults');
    const resultsCount = document.getElementById('resultsCount');
    
    // Скрываем все элементы по умолчанию и убираем подсветку
    categoryItems.forEach(item => {
        item.style.display = 'none';
        const title = item.querySelector('.category-title');
        if (title) highlightText(title, '');
    });
    lessonItems.forEach(item => {
        item.style.display = 'none';
        const title = item.querySelector('.lesson-title');
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
        const lessonItemsInCategory = categoryItem.querySelectorAll('.lesson-item');
        let hasMatchingLessons = false;
        
        lessonItemsInCategory.forEach(lessonItem => {
            const lessonTitle = lessonItem.querySelector('.lesson-title');
            const lessonTitleText = lessonTitle.textContent.toLowerCase();
            if (lessonTitleText.includes(searchTermLower)) {
                lessonItem.style.display = 'block';
                highlightText(lessonTitle, searchTerm);
                hasMatchingLessons = true;
                foundCount++;
                
                // Показываем родительскую категорию
                categoryItem.style.display = 'block';
                
                // Показываем все родительские категории
                let parentCategory = categoryItem.parentElement.closest('.category-item');
                while (parentCategory) {
                    parentCategory.style.display = 'block';
                    parentCategory = parentCategory.parentElement.closest('.category-item');
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
            let parentCategory = categoryItem.parentElement.closest('.category-item');
            while (parentCategory) {
                parentCategory.style.display = 'block';
                parentCategory = parentCategory.parentElement.closest('.category-item');
            }
        }
    });
    
    // Показываем счетчик результатов
    resultsCount.textContent = foundCount;
    searchResults.style.display = 'block';
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
    
    // Убираем активный класс со всех вкладок
    categoriesTab.classList.remove('active');
    uncatTab.classList.remove('active');
    testsTab.classList.remove('active');
    
    // Скрываем все блоки
    categoriesBlock.style.display = 'none';
    uncatBlock.style.display = 'none';
    testsBlock.style.display = 'none';
    
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
}

// Инициализация
document.addEventListener('DOMContentLoaded', function() {
    // Показываем все категории по умолчанию
    const categoryHeaders = document.querySelectorAll('.category-header');
    categoryHeaders.forEach(header => {
        const arrow = header.querySelector('.toggle-arrow');
        if (arrow) {
            arrow.classList.remove('expanded');
        }
        
        const categoryItem = header.closest('.category-item');
        const subcategoryList = categoryItem.querySelector('.subcategory-list');
        const lessonList = categoryItem.querySelector('.lesson-list');
        
        if (subcategoryList) subcategoryList.style.display = 'none';
        if (lessonList) lessonList.style.display = 'none';
    });
    
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