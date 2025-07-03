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

document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.getElementById('sidebar');
    const detail = document.getElementById('detail');
    const toggleBtn = document.getElementById('toggle-sidebar-btn');
    const masterDetail = document.querySelector('.master-detail-container');

    function isMobile() {
        return window.innerWidth <= 900;
    }

    function setToggleBtnInDetail(show) {
        if (!detail || !toggleBtn) return;
        if (show) {
            detail.insertBefore(toggleBtn, detail.firstChild);
            toggleBtn.classList.add('sidebar-toggle-floating');
        } else {
            sidebar.insertBefore(toggleBtn, sidebar.firstChild);
            toggleBtn.classList.remove('sidebar-toggle-floating');
        }
    }

    if (toggleBtn && sidebar && detail && masterDetail) {
        toggleBtn.addEventListener('click', function() {
            if (isMobile()) {
                if (!masterDetail.classList.contains('sidebar-hidden')) {
                    masterDetail.classList.add('sidebar-hidden');
                    toggleBtn.innerHTML = '<span id="toggle-sidebar-icon">⮞</span> Показать меню';
                    setToggleBtnInDetail(true);
                } else {
                    masterDetail.classList.remove('sidebar-hidden');
                    toggleBtn.innerHTML = '<span id="toggle-sidebar-icon">⮜</span> Скрыть меню';
                    setToggleBtnInDetail(false);
                }
            } else {
                if (!masterDetail.classList.contains('sidebar-collapsed')) {
                    masterDetail.classList.add('sidebar-collapsed');
                    toggleBtn.innerHTML = '<span id="toggle-sidebar-icon">⮞</span> >';
                } else {
                    masterDetail.classList.remove('sidebar-collapsed');
                    toggleBtn.innerHTML = '<span id="toggle-sidebar-icon">⮜</span> <';
                }
            }
        });

        // При изменении размера окна возвращаем кнопку на место
        window.addEventListener('resize', function() {
            if (isMobile()) {
                if (masterDetail.classList.contains('sidebar-hidden')) {
                    setToggleBtnInDetail(true);
                } else {
                    setToggleBtnInDetail(false);
                }
            } else {
                setToggleBtnInDetail(false);
            }
        });
    }
});
