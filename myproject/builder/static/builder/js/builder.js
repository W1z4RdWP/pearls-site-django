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
