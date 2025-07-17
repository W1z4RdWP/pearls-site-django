// --- Поиск по дереву категорий и уроков (универсальный) ---
document.getElementById('tree-search-input')?.addEventListener('input', function() {
    const q = this.value.trim();
    const allCatBlocks = document.querySelectorAll('.category-block');
    const allLessonLis = document.querySelectorAll('.lesson-list li, .category-list > .category-block');
    if (!q) {
        // Показать всё
        allCatBlocks.forEach(el => el.style.display = '');
        document.querySelectorAll('.lesson-list li').forEach(el => el.style.display = '');
        return;
    }
    console.log('Поиск:', q); // Отладка
    fetch('/builder/search/?query=' + encodeURIComponent(q))
        .then(r => {
            if (!r.ok) {
                throw new Error(`HTTP ${r.status}: ${r.statusText}`);
            }
            return r.json();
        })
        .then(data => {
            console.log('Результат поиска:', data); // Отладка
            const catIds = new Set((data.categories||[]).map(String));
            const lessonIds = new Set((data.lessons||[]).map(String));
            console.log('ID категорий:', Array.from(catIds)); // Отладка
            console.log('ID уроков:', Array.from(lessonIds)); // Отладка
            // Скрыть всё
            allCatBlocks.forEach(el => el.style.display = 'none');
            document.querySelectorAll('.lesson-list li').forEach(el => el.style.display = 'none');
            // Показать совпавшие категории
            catIds.forEach(id => {
                const el = document.querySelector(`.category-block[data-id='${id}']`);
                console.log(`Ищем категорию ${id}:`, el); // Отладка
                if (el) {
                    el.style.display = '';
                    // Показать родителей
                    let parent = el.parentElement;
                    while (parent && !parent.classList.contains('category-list')) {
                        if (parent.classList.contains('category-block')) parent.style.display = '';
                        parent = parent.parentElement;
                    }
                }
            });
            // Показать совпавшие уроки
            lessonIds.forEach(id => {
                // В категориях
                let lessonLi = null;
                const lessonSelect = document.querySelector(`.lesson-select[value='${id}']`);
                if (lessonSelect) {
                    lessonLi = lessonSelect.closest('li');
                } else {
                    lessonLi = document.querySelector(`.lesson-li[data-lesson-id='${id}']`);
                }
                console.log(`Ищем урок ${id}:`, lessonLi); // Отладка
                if (lessonLi) {
                    lessonLi.style.display = '';
                    // Показать родительский список уроков
                    const lessonList = lessonLi.closest('.lesson-list');
                    if (lessonList) {
                        lessonList.style.display = 'block';
                    }
                    // Показать родителей (категории)
                    let parent = lessonLi.parentElement;
                    while (parent && !parent.classList.contains('category-list')) {
                        if (parent.classList.contains('category-block')) {
                            parent.style.display = '';
                        }
                        parent = parent.parentElement;
                    }
                }
                // В корне (уроки без категории)
                const rootLi = document.querySelector(`.category-block[data-id='uncat-${id}']`);
                console.log(`Ищем урок без категории ${id}:`, rootLi); // Отладка
                if (rootLi) rootLi.style.display = '';
            });
        })
        .catch(error => {
            console.error('Ошибка поиска:', error);
            // При ошибке показываем все элементы
            allCatBlocks.forEach(el => el.style.display = '');
            document.querySelectorAll('.lesson-list li').forEach(el => el.style.display = '');
        });
});

