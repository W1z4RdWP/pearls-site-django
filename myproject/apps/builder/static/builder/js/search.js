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
    fetch('/builder/search/?query=' + encodeURIComponent(q))
        .then(r => {
            if (!r.ok) {
                throw new Error(`HTTP ${r.status}: ${r.statusText}`);
            }
            return r.json();
        })
        .then(data => {
            const catIds = new Set((data.categories||[]).map(String));
            const lessonIds = new Set((data.lessons||[]).map(String));
            // Скрыть всё
            allCatBlocks.forEach(el => el.style.display = 'none');
            document.querySelectorAll('.lesson-list li').forEach(el => el.style.display = 'none');
            // Показать совпавшие категории
            catIds.forEach(id => {
                const el = document.querySelector(`.category-block[data-id='${id}']`);
                if (el) {
                    el.style.display = '';
                    // Показать все уроки внутри найденной категории
                    el.querySelectorAll('.lesson-list li').forEach(li => li.style.display = '');
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

