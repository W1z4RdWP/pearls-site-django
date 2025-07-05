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

    // v — редактировать выделенную категорию или урок
    document.getElementById('edit-category')?.addEventListener('click', function() {
        const catId = getSelectedCategoryId();
        const lessonId = getSelectedLessonId();
        if (lessonId) {
            window.location.href = `/builder/lesson/${lessonId}/edit/`;
            return;
        }
        if (!catId) { alert('Выделите категорию или урок!'); return; }
        // Inline-редактирование названия категории
        const block = document.querySelector(`.category-block[data-id='${catId}']`);
        if (!block) return;
        const header = block.querySelector('.category-header');
        const titleSpan = header.querySelector('.category-title');
        if (!titleSpan) return;
        // Если уже редактируется — не дублируем
        if (header.querySelector('.inline-cat-rename')) return;
        const oldName = titleSpan.textContent.replace(/^\d+\.\s*/, '');
        const order = titleSpan.textContent.match(/^\d+/)?.[0] || '';
        // Скрыть span, вставить input
        titleSpan.style.display = 'none';
        const input = document.createElement('input');
        input.type = 'text';
        input.value = oldName;
        input.className = 'inline-cat-rename';
        input.style = 'flex:1; min-width:80px; font-size:1.1em; padding:2px 8px; border-radius:4px; border:1px solid #4d7cff; outline:none; margin-left:0;';
        header.insertBefore(input, titleSpan.nextSibling);
        input.focus();
        function finish(save) {
            if (!save) {
                input.remove();
                titleSpan.style.display = '';
                return;
            }
            const newName = input.value.trim();
            if (!newName || newName === oldName) {
                input.remove();
                titleSpan.style.display = '';
                return;
            }
            input.disabled = true;
            fetch('/builder/categories/ajax_rename/', {
                method: 'POST',
                headers: { 'X-CSRFToken': (document.querySelector('[name=csrfmiddlewaretoken]')||{}).value || '', },
                body: new URLSearchParams({ id: catId, name: newName })
            })
            .then(r => r.json())
            .then(data => {
                if (data.error) { alert('Ошибка: ' + data.error); input.remove(); titleSpan.style.display = ''; return; }
                titleSpan.textContent = order ? `${order}. ${data.name}` : data.name;
                input.remove();
                titleSpan.style.display = '';
            })
            .catch(() => { alert('Ошибка сети'); input.remove(); titleSpan.style.display = ''; });
        }
        input.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') finish(true);
            if (e.key === 'Escape') finish(false);
        });
        input.addEventListener('blur', function() { setTimeout(() => finish(true), 200); });
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

    // 📄 — добавить урок (теперь всегда активна)
    document.getElementById('add-lesson')?.addEventListener('click', function() {
        const catId = getSelectedCategoryId();
        if (catId) {
            window.location.href = `/builder/add/${catId}/`;
        } else {
            window.location.href = '/builder/add/';
        }
    });

    // --- Логика одиночного выбора и подсветки ---
    function initCategoryCheckboxHandlers(root=document) {
        // Одиночный выбор категории
        root.querySelectorAll('.category-select').forEach(cb => {
            if (cb._inited) return; cb._inited = true;
            cb.addEventListener('change', function() {
                // Сбрасываем все категории
                document.querySelectorAll('.category-select').forEach(other => {
                    if (other !== cb) other.checked = false;
                });
                document.querySelectorAll('.category-block').forEach(block => {
                    block.classList.remove('selected');
                });
                
                // Сбрасываем все уроки при выборе категории
                document.querySelectorAll('.lesson-select').forEach(lessonCb => {
                    lessonCb.checked = false;
                });
                document.querySelectorAll('.lesson-list li').forEach(li => {
                    li.classList.remove('selected');
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
                // Сбрасываем все уроки
                document.querySelectorAll('.lesson-select').forEach(other => {
                    if (other !== cb) other.checked = false;
                });
                document.querySelectorAll('.lesson-list li').forEach(li => {
                    li.classList.remove('selected');
                });
                
                // Сбрасываем все категории при выборе урока
                document.querySelectorAll('.category-select').forEach(catCb => {
                    catCb.checked = false;
                });
                document.querySelectorAll('.category-block').forEach(block => {
                    block.classList.remove('selected');
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
    
    // Инициализация: сбрасываем все выделения при загрузке
    document.querySelectorAll('.category-select, .lesson-select').forEach(cb => cb.checked = false);
    document.querySelectorAll('.category-block').forEach(block => block.classList.remove('selected'));
    document.querySelectorAll('.lesson-list li').forEach(li => li.classList.remove('selected'));

    // Сброс выделения при клике вне чекбоксов
    document.addEventListener('click', function(e) {
        if (!e.target.classList.contains('category-select') && !e.target.classList.contains('lesson-select')) {
            // Сбрасываем все чекбоксы
            document.querySelectorAll('.category-select, .lesson-select').forEach(cb => cb.checked = false);
            // Сбрасываем все выделения
            document.querySelectorAll('.category-block').forEach(block => block.classList.remove('selected'));
            document.querySelectorAll('.lesson-list li').forEach(li => li.classList.remove('selected'));
            updateActionButtons();
        }
    });
    // Кнопки активны только при выборе
    function updateActionButtons() {
        const catId = document.querySelector('.category-select:checked');
        const lessonId = document.querySelector('.lesson-select:checked');
        
        // Обновляем состояние кнопок
        const addSubBtn = document.getElementById('add-subcategory');
        const editBtn = document.getElementById('edit-category');
        const deleteBtn = document.getElementById('delete-category');
        const addLessonBtn = document.getElementById('add-lesson');
        
        if (addSubBtn) addSubBtn.disabled = !catId;
        if (editBtn) {
            editBtn.disabled = !(catId || lessonId);
            // Обновляем подсказку в зависимости от выбранного элемента
            if (lessonId) {
                editBtn.title = 'Редактировать урок';
            } else if (catId) {
                editBtn.title = 'Переименовать категорию';
            } else {
                editBtn.title = 'Изменить название';
            }
        }
        if (deleteBtn) {
            deleteBtn.disabled = !(catId || lessonId);
            // Обновляем подсказку в зависимости от выбранного элемента
            if (lessonId) {
                deleteBtn.title = 'Удалить урок';
            } else if (catId) {
                deleteBtn.title = 'Удалить категорию';
            } else {
                deleteBtn.title = 'Удалить';
            }
        }
        if (addLessonBtn) addLessonBtn.disabled = false;
    }
    updateActionButtons();

    // --- Поиск по дереву категорий и уроков ---
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
            .then(r => r.json())
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
                    const li = document.querySelector(`.lesson-select[value='${id}']`);
                    if (li) {
                        const lessonLi = li.closest('li');
                        if (lessonLi) lessonLi.style.display = '';
                        // Показать родителей
                        let parent = lessonLi?.parentElement;
                        while (parent && !parent.classList.contains('category-list')) {
                            if (parent.classList.contains('category-block')) parent.style.display = '';
                            parent = parent.parentElement;
                        }
                    }
                    // В корне
                    const rootLi = document.querySelector(`.category-block[data-id='uncat-${id}']`);
                    if (rootLi) rootLi.style.display = '';
                });
            });
    });

    // === Кастомное контекстное меню для копирования/вырезания/вставки ===
    let contextTarget = null;
    let clipboardData = null;
    
    // Проверяем буфер обмена при загрузке
    function checkClipboard() {
        fetch('/builder/clipboard/')
            .then(r => r.json())
            .then(data => {
                clipboardData = data.empty ? null : data;
                updatePasteButton();
            })
            .catch(error => {
                console.log('Ошибка при проверке буфера обмена:', error);
                clipboardData = null;
                updatePasteButton();
            });
    }
    
    function updatePasteButton() {
        const pasteBtn = document.getElementById('paste-menu-item');
        const copyBtn = document.getElementById('copy-menu-item');
        const cutBtn = document.getElementById('cut-menu-item');
        
        if (pasteBtn) {
            pasteBtn.style.opacity = clipboardData ? '1' : '0.5';
            pasteBtn.style.cursor = clipboardData ? 'pointer' : 'not-allowed';
        }
        
        // Скрываем кнопки копирования/вырезания если контекстное меню открыто на корневом списке
        if (contextTarget && contextTarget.classList.contains('category-list')) {
            if (copyBtn) copyBtn.style.display = 'none';
            if (cutBtn) cutBtn.style.display = 'none';
        } else {
            if (copyBtn) copyBtn.style.display = '';
            if (cutBtn) cutBtn.style.display = '';
        }
    }
    
    document.addEventListener('contextmenu', function(e) {
        let li = e.target.closest('li');
        let ul = e.target.closest('ul.category-list');
        
        if (li && (li.classList.contains('category-block') || li.querySelector('.lesson-link') || (li.dataset.id && li.dataset.id.startsWith('uncat-')))) {
            e.preventDefault();
            contextTarget = li;
            const menu = document.getElementById('custom-context-menu');
            menu.style.display = 'block';
            menu.style.left = e.pageX + 'px';
            menu.style.top = e.pageY + 'px';
            updatePasteButton();
        } else if (ul && clipboardData) {
            // Показываем меню только если есть что вставлять
            e.preventDefault();
            contextTarget = ul;
            const menu = document.getElementById('custom-context-menu');
            menu.style.display = 'block';
            menu.style.left = e.pageX + 'px';
            menu.style.top = e.pageY + 'px';
            updatePasteButton();
        } else {
            document.getElementById('custom-context-menu').style.display = 'none';
        }
    });
    
    document.addEventListener('click', function(e) {
        if (!e.target.closest('#custom-context-menu')) {
            document.getElementById('custom-context-menu').style.display = 'none';
        }
    });
    
    // Копировать
    document.getElementById('copy-menu-item').addEventListener('click', function() {
        if (!contextTarget) return;
        
        let itemId, itemType;
        if (contextTarget.classList.contains('category-block')) {
            // Если это блок категории, то это категория
            itemType = 'category';
            itemId = contextTarget.dataset.id;
        } else if (contextTarget.querySelector('.lesson-link')) {
            // Если это урок (не категория)
            itemType = 'lesson';
            itemId = contextTarget.querySelector('.lesson-select')?.value;
        } else if (contextTarget.dataset.id && contextTarget.dataset.id.startsWith('uncat-')) {
            // Урок без категории
            itemType = 'lesson';
            itemId = contextTarget.dataset.id.replace('uncat-', '');
        }
        
        if (!itemId || !itemType) return;
        
        fetch('/builder/copy/', {
            method: 'POST',
            headers: { 'X-CSRFToken': (document.querySelector('[name=csrfmiddlewaretoken]')||{}).value || '', 'Content-Type': 'application/json' },
            body: JSON.stringify({ id: itemId, type: itemType })
        }).then(r => r.json()).then(data => {
            if (data.error) { alert('Ошибка: ' + data.error); return; }
            clipboardData = { id: itemId, type: itemType, action: 'copy' };
            updatePasteButton();
            document.getElementById('custom-context-menu').style.display = 'none';
        }).catch(error => {
            alert('Ошибка сети: ' + error.message);
        });
    });
    
    // Вырезать
    document.getElementById('cut-menu-item').addEventListener('click', function() {
        if (!contextTarget) return;
        
        let itemId, itemType;
        if (contextTarget.classList.contains('category-block')) {
            // Если это блок категории, то это категория
            itemType = 'category';
            itemId = contextTarget.dataset.id;
        } else if (contextTarget.querySelector('.lesson-link')) {
            // Если это урок (не категория)
            itemType = 'lesson';
            itemId = contextTarget.querySelector('.lesson-select')?.value;
        } else if (contextTarget.dataset.id && contextTarget.dataset.id.startsWith('uncat-')) {
            // Урок без категории
            itemType = 'lesson';
            itemId = contextTarget.dataset.id.replace('uncat-', '');
        }
        
        if (!itemId || !itemType) return;
        
        fetch('/builder/cut/', {
            method: 'POST',
            headers: { 'X-CSRFToken': (document.querySelector('[name=csrfmiddlewaretoken]')||{}).value || '', 'Content-Type': 'application/json' },
            body: JSON.stringify({ id: itemId, type: itemType })
        }).then(r => r.json()).then(data => {
            if (data.error) { alert('Ошибка: ' + data.error); return; }
            clipboardData = { id: itemId, type: itemType, action: 'cut' };
            updatePasteButton();
            document.getElementById('custom-context-menu').style.display = 'none';
        }).catch(error => {
            alert('Ошибка сети: ' + error.message);
        });
    });
    
    // Вставить
    document.getElementById('paste-menu-item').addEventListener('click', function() {
        if (!clipboardData || !contextTarget) return;
        
        // Определяем целевую категорию
        let targetCategory = '';
        if (contextTarget.classList.contains('category-list')) {
            // Если кликнули на корневой список категорий, вставляем в корень
            targetCategory = '';
        } else if (contextTarget.classList.contains('category-block')) {
            targetCategory = contextTarget.dataset.id;
        } else if (contextTarget.dataset.id && contextTarget.dataset.id.startsWith('uncat-')) {
            // Если кликнули на урок без категории, вставляем в корень
            targetCategory = '';
        } else {
            // Если кликнули на урок, берем его родительскую категорию
            const parentCategory = contextTarget.closest('.category-block');
            targetCategory = parentCategory ? parentCategory.dataset.id : '';
        }
        
        fetch('/builder/paste/', {
            method: 'POST',
            headers: { 'X-CSRFToken': (document.querySelector('[name=csrfmiddlewaretoken]')||{}).value || '', 'Content-Type': 'application/json' },
            body: JSON.stringify({ target_category: targetCategory })
        }).then(r => r.json()).then(data => {
            if (data.error) { alert('Ошибка: ' + data.error); return; }
            
            // Обновляем DOM
            if (data.result) {
                if (clipboardData.action === 'cut') {
                    // Удаляем оригинальный элемент при вырезании
                    let originalElement = null;
                    if (clipboardData.type === 'lesson') {
                        // Ищем урок в категориях или в корне
                        originalElement = document.querySelector(`.lesson-select[value="${clipboardData.id}"]`)?.closest('li');
                        if (!originalElement) {
                            originalElement = document.querySelector(`[data-id="uncat-${clipboardData.id}"]`);
                        }
                    } else if (clipboardData.type === 'category') {
                        // Для категорий удаляем весь блок категории со всем содержимым
                        originalElement = document.querySelector(`[data-id="${clipboardData.id}"]`);
                        if (originalElement) {
                            // Удаляем весь li с категорией и всем её содержимым
                            originalElement.remove();
                        }
                    }
                }
                
                // Перезагружаем страницу для отображения изменений
                window.location.reload();
            }
            
            clipboardData = null;
            updatePasteButton();
            document.getElementById('custom-context-menu').style.display = 'none';
        }).catch(error => {
            alert('Ошибка сети: ' + error.message);
        });
    });
    
    // Инициализация буфера обмена
    checkClipboard();
});
