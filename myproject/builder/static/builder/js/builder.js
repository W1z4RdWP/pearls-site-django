function saveCategoryState(categoryId, isOpen) {
    sessionStorage.setItem(`category_${categoryId}_state`, isOpen ? 'open' : 'closed');
}

function restoreCategoryStates() {
    document.querySelectorAll('.category-block').forEach(categoryBlock => {
        const categoryId = categoryBlock.dataset.id;
        const savedState = sessionStorage.getItem(`category_${categoryId}_state`);
        
        if (savedState === 'open') {
            const header = categoryBlock.querySelector('.category-header');
            if (!header.classList.contains('open')) {
                toggleSubcat(header);
            }
        }
    });
}

function toggleSubcat(header) {
    header.classList.toggle('open');
    const categoryBlock = header.closest('.category-block'); // самый близкий родитель с классом category-block

    if (!categoryBlock) return;

    const categoryId = categoryBlock.dataset.id;
    const subcatList = categoryBlock.querySelector('.subcategory-list');
    const lessonList = categoryBlock.querySelector('.lesson-list');
    const arrow = header.querySelector('.toggle-arrow');

    // Сохраняем состояние
    const isNowOpen = header.classList.contains('open');
    saveCategoryState(categoryId, isNowOpen);

    function toggleDisplay(element) {
        if (!element) return;
        const isVisible = element.style.display === 'block';
        element.style.display = isVisible ? 'none' : 'block';
    }

    toggleDisplay(subcatList);
    toggleDisplay(lessonList);

    if (arrow) {
        const anyOpen = (subcatList && subcatList.style.display === 'block') || (lessonList && lessonList.style.display === 'block');
        arrow.innerHTML = anyOpen ? '&#9660;' : '&#9654;'; // ▼ или ▶
    }
}

// Восстанавливаем состояния при загрузке страницы
document.addEventListener('DOMContentLoaded', restoreCategoryStates);

// --- Перемещение боковой панели ---
document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.getElementById('sidebar');
    const resizer = document.getElementById('sidebar-resizer');
    let isResizing = false;

    if (!sidebar || !resizer) return;

    resizer.addEventListener('mousedown', function(e) {
        isResizing = true;
        document.body.style.cursor = 'ew-resize';
        document.body.style.userSelect = 'none'; // Отключаем выделение текста
        e.preventDefault();
    });

    document.addEventListener('mousemove', function(e) {
        if (!isResizing) return;
        let newWidth = e.clientX - sidebar.getBoundingClientRect().left;
        newWidth = Math.max(180, Math.min(600, newWidth));
        sidebar.style.width = newWidth + 'px';
        e.preventDefault();
    });

    document.addEventListener('mouseup', function() {
        if (isResizing) {
            isResizing = false;
            document.body.style.cursor = '';
            document.body.style.userSelect = ''; // Включаем обратно выделение текста

        }
    });
});