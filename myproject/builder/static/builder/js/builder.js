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

    // === КНОПКИ ДЕЙСТВИЙ ДЛЯ КАТЕГОРИЙ/УРОКОВ ===
    function getSelectedCategoryId() {
        const checked = document.querySelector('.category-select:checked');
        return checked ? checked.value : null;
    }
    function getSelectedLessonId() {
        const checked = document.querySelector('.lesson-select:checked');
        return checked ? checked.value : null;
    }

    // --- Inline-добавление корневой категории ---
    document.getElementById('add-root-category')?.addEventListener('click', function() {
        // Если уже есть инпут — не дублируем
        if (document.getElementById('inline-root-cat-input')) return;
        const ul = document.querySelector('.category-list');
        if (!ul) return;
        // Создаём li с инпутом
        const li = document.createElement('li');
        li.className = 'category-block';
        li.style.background = '#232a3a';
        li.style.padding = '8px 32px';
        li.style.borderRadius = '6px';
        li.style.marginBottom = '6px';
        li.innerHTML = `<div class="category-header"><input id="inline-root-cat-input" type="text" placeholder="Название категории..." style="flex:1; min-width:120px; font-size:1.1em; padding:4px 8px; border-radius:4px; border:1px solid #4d7cff; outline:none;"></div>`;
        ul.prepend(li);
        const input = li.querySelector('#inline-root-cat-input');
        input.focus();
        // Обработчик подтверждения
        function submit() {
            const name = input.value.trim();
            if (!name) { li.remove(); return; }
            input.disabled = true;
            fetch('/builder/categories/ajax_add_root/', {
                method: 'POST',
                headers: { 'X-CSRFToken': (document.querySelector('[name=csrfmiddlewaretoken]')||{}).value || '', },
                body: new URLSearchParams({ name })
            })
            .then(r => r.json())
            .then(data => {
                if (data.error) { alert('Ошибка: ' + data.error); li.remove(); return; }
                // Вставляем новую категорию в DOM
                const newLi = document.createElement('li');
                newLi.className = 'category-block';
                newLi.setAttribute('data-id', data.id);
                newLi.innerHTML = `<div class='category-header'><input type='checkbox' class='category-select' value='${data.id}' style='margin-right:8px;'><span class='category-title'>${data.order}. ${data.name}</span></div>`;
                ul.insertBefore(newLi, li.nextSibling);
                initCategoryCheckboxHandlers(newLi); // навесить обработчик на новый чекбокс
                li.remove();
            })
            .catch(() => { alert('Ошибка сети'); li.remove(); });
        }
        input.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') submit();
            if (e.key === 'Escape') li.remove();
        });
        input.addEventListener('blur', function() { setTimeout(() => li && li.remove(), 200); });
    });

    // --- Inline-добавление подкатегории ---
    document.getElementById('add-subcategory')?.addEventListener('click', function() {
        const catId = getSelectedCategoryId();
        if (!catId) { alert('Выделите категорию!'); return; }
        // Найти блок выбранной категории
        const parentBlock = document.querySelector(`.category-block[data-id='${catId}']`);
        if (!parentBlock) return;
        // Найти или создать ul.subcategory-list
        let subUl = parentBlock.querySelector('.subcategory-list');
        if (!subUl) {
            subUl = document.createElement('ul');
            subUl.className = 'subcategory-list';
            subUl.style.display = 'block';
            parentBlock.appendChild(subUl);
        } else {
            subUl.style.display = 'block';
        }
        // Если уже есть инпут — не дублируем
        if (subUl.querySelector('#inline-subcat-input')) return;
        // Создаём li с инпутом
        const li = document.createElement('li');
        li.className = 'category-block';
        li.style.background = '#232a3a';
        li.style.padding = '8px 32px';
        li.style.borderRadius = '6px';
        li.style.marginBottom = '6px';
        li.innerHTML = `<div class=\"category-header\"><input id=\"inline-subcat-input\" type=\"text\" placeholder=\"Название подкатегории...\" style=\"flex:1; min-width:120px; font-size:1.1em; padding:4px 8px; border-radius:4px; border:1px solid #4d7cff; outline:none;\"></div>`;
        subUl.appendChild(li);
        const input = li.querySelector('#inline-subcat-input');
        input.focus();
        // Обработчик подтверждения
        function submit() {
            const name = input.value.trim();
            if (!name) { li.remove(); return; }
            input.disabled = true;
            fetch('/builder/categories/ajax_add_sub/', {
                method: 'POST',
                headers: { 'X-CSRFToken': (document.querySelector('[name=csrfmiddlewaretoken]')||{}).value || '', },
                body: new URLSearchParams({ name, parent_id: catId })
            })
            .then(r => r.json())
            .then(data => {
                if (data.error) { alert('Ошибка: ' + data.error); li.remove(); return; }
                // Вставляем новую подкатегорию в DOM
                const newLi = document.createElement('li');
                newLi.className = 'category-block';
                newLi.setAttribute('data-id', data.id);
                newLi.innerHTML = `<div class='category-header'><input type='checkbox' class='category-select' value='${data.id}' style='margin-right:8px;'><span class='category-title'>${data.order}. ${data.name}</span></div>`;
                subUl.insertBefore(newLi, li.nextSibling);
                initCategoryCheckboxHandlers(newLi); // навесить обработчик на новый чекбокс
                li.remove();
            })
            .catch(() => { alert('Ошибка сети'); li.remove(); });
        }
        input.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') submit();
            if (e.key === 'Escape') li.remove();
        });
        input.addEventListener('blur', function() { setTimeout(() => li && li.remove(), 200); });
    });

    // v — редактировать выделенную категорию
    document.getElementById('edit-category')?.addEventListener('click', function() {
        const catId = getSelectedCategoryId();
        if (!catId) { alert('Выделите категорию!'); return; }
        window.location.href = `/builder/categories/${catId}/edit/`;
    });

    // x — удалить выделенную категорию или урок
    document.getElementById('delete-category')?.addEventListener('click', function() {
        const catId = getSelectedCategoryId();
        const lessonId = getSelectedLessonId();
        if (catId) {
            if (confirm('Удалить категорию?')) {
                window.location.href = `/builder/categories/${catId}/delete/`;
            }
        } else if (lessonId) {
            if (confirm('Удалить урок?')) {
                window.location.href = `/builder/lesson/${lessonId}/delete/`;
            }
        } else {
            alert('Выделите категорию или урок!');
        }
    });

    // 📄 — добавить урок в выделенную категорию
    document.getElementById('add-lesson')?.addEventListener('click', function() {
        const catId = getSelectedCategoryId();
        if (!catId) { alert('Выделите категорию!'); return; }
        window.location.href = `/builder/add/${catId}/`;
    });

    // --- Логика одиночного выбора и подсветки ---
    function initCategoryCheckboxHandlers(root=document) {
        // Одиночный выбор категории
        root.querySelectorAll('.category-select').forEach(cb => {
            if (cb._inited) return; cb._inited = true;
            cb.addEventListener('change', function() {
                document.querySelectorAll('.category-select').forEach(other => {
                    if (other !== cb) other.checked = false;
                });
                document.querySelectorAll('.category-block').forEach(block => {
                    block.classList.remove('selected');
                });
                if (cb.checked) {
                    cb.closest('.category-block').classList.add('selected');
                }
                updateActionButtons();
            });
        });
    }
    function initLessonCheckboxHandlers(root=document) {
        root.querySelectorAll('.lesson-select').forEach(cb => {
            if (cb._inited) return; cb._inited = true;
            cb.addEventListener('change', function() {
                document.querySelectorAll('.lesson-select').forEach(other => {
                    if (other !== cb) other.checked = false;
                });
                document.querySelectorAll('.lesson-list li').forEach(li => {
                    li.classList.remove('selected');
                });
                if (cb.checked) {
                    cb.closest('li').classList.add('selected');
                }
                updateActionButtons();
            });
        });
    }
    initCategoryCheckboxHandlers();
    initLessonCheckboxHandlers();

    // Сброс выделения при клике вне чекбоксов
    document.addEventListener('click', function(e) {
        if (!e.target.classList.contains('category-select') && !e.target.classList.contains('lesson-select')) {
            document.querySelectorAll('.category-select, .lesson-select').forEach(cb => cb.checked = false);
            document.querySelectorAll('.category-block').forEach(block => block.classList.remove('selected'));
            document.querySelectorAll('.lesson-list li').forEach(li => li.classList.remove('selected'));
            updateActionButtons();
        }
    });
    // Кнопки активны только при выборе
    function updateActionButtons() {
        const catId = document.querySelector('.category-select:checked');
        const lessonId = document.querySelector('.lesson-select:checked');
        document.getElementById('add-subcategory').disabled = !catId;
        document.getElementById('edit-category').disabled = !catId;
        document.getElementById('delete-category').disabled = !(catId || lessonId);
        document.getElementById('add-lesson').disabled = !catId;
    }
    updateActionButtons();
});
