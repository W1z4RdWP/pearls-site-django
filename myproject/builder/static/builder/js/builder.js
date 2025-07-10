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

    // === МОДАЛКА ПОДТВЕРЖДЕНИЯ СОЗДАНИЯ КАТЕГОРИИ ===
    function showCategoryCreateConfirm({onYes, onNo}) {
        let modal = document.getElementById('category-create-confirm-modal');
        if (!modal) {
            modal = document.createElement('div');
            modal.id = 'category-create-confirm-modal';
            modal.innerHTML = `
            <div style="position:fixed;z-index:99999;left:0;top:0;width:100vw;height:100vh;background:rgba(0,0,0,0.35);display:flex;align-items:center;justify-content:center;">
                <div style="background:#232a3a;color:#fff;padding:32px 32px 24px 32px;border-radius:12px;box-shadow:0 2px 16px #0007;min-width:320px;max-width:90vw;text-align:center;">
                    <div style="font-size:1.15em;margin-bottom:18px;">Вы хотите создать категорию?</div>
                    <div style="display:flex;gap:18px;justify-content:center;">
                        <button id="cat-create-yes" style="padding:8px 24px;font-size:1em;border-radius:6px;border:none;background:#4d7cff;color:#fff;cursor:pointer;">Да</button>
                        <button id="cat-create-no" style="padding:8px 24px;font-size:1em;border-radius:6px;border:none;background:#444;color:#fff;cursor:pointer;">Нет</button>
                    </div>
                </div>
            </div>`;
            document.body.appendChild(modal);
        } else {
            modal.style.display = '';
        }
        function cleanup() {
            modal.style.display = 'none';
        }
        modal.querySelector('#cat-create-yes').onclick = function() { cleanup(); onYes && onYes(); };
        modal.querySelector('#cat-create-no').onclick = function() { cleanup(); onNo && onNo(); };
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
        let enterPressed = false;
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
                window.location.reload();
            })
            .catch(() => { alert('Ошибка сети'); li.remove(); });
        }
        input.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                enterPressed = true;
                submit();
            }
            if (e.key === 'Escape') li.remove();
        });
        input.addEventListener('blur', function() {
            if (!input.value.trim()) { li && li.remove(); return; }
            if (enterPressed) return;
            showCategoryCreateConfirm({
                onYes: submit,
                onNo: function() { li && li.remove(); }
            });
        });
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
        let enterPressed = false;
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
                window.location.reload();
            })
            .catch(() => { alert('Ошибка сети'); li.remove(); });
        }
        input.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                enterPressed = true;
                submit();
            }
            if (e.key === 'Escape') li.remove();
        });
        input.addEventListener('blur', function() {
            if (!input.value.trim()) { li && li.remove(); return; }
            if (enterPressed) return;
            showCategoryCreateConfirm({
                onYes: submit,
                onNo: function() { li && li.remove(); }
            });
        });
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
                selectCategory(cb);
            });
        });
        
        // Обработчики кликов по заголовкам категорий
        root.querySelectorAll('.category-header').forEach(header => {
            if (header._inited) return; header._inited = true;
            header.addEventListener('click', function(e) {
                // Не обрабатываем клики по стрелке
                if (e.target.classList.contains('toggle-arrow') || 
                    e.target.closest('.toggle-arrow')) {
                    return;
                }
                
                const categoryBlock = this.closest('.category-block');
                const radio = categoryBlock.querySelector('.category-select');
                if (radio) {
                    radio.checked = true;
                    selectCategory(radio);
                }
            });
        });
    }
    
    function initLessonCheckboxHandlers(root=document) {
        root.querySelectorAll('.lesson-select').forEach(cb => {
            if (cb._inited) return; cb._inited = true;
            cb.addEventListener('change', function() {
                selectLesson(cb);
            });
        });
        
        // Обработчики кликов по элементам уроков
        root.querySelectorAll('.lesson-list li').forEach(li => {
            if (li._inited) return; li._inited = true;
            li.addEventListener('click', function(e) {
                // Не обрабатываем клики по svg и иконкам
                if (e.target.closest('svg') || e.target.classList.contains('lesson-icon')) {
                    return;
                }
                
                const radio = this.querySelector('.lesson-select');
                if (radio) {
                    radio.checked = true;
                    selectLesson(radio);
                }
            });
        });
        
        // Обработчики кликов по урокам без категории
        root.querySelectorAll('.category-block[data-id^="uncat-"]').forEach(block => {
            if (block._inited) return; block._inited = true;
            block.addEventListener('click', function(e) {
                // Не обрабатываем клики по svg и иконкам
                if (e.target.closest('svg') || e.target.classList.contains('lesson-icon')) {
                    return;
                }
                
                const radio = this.querySelector('.lesson-select');
                if (radio) {
                    radio.checked = true;
                    selectLesson(radio);
                }
            });
        });
    }
    
    function selectCategory(radio) {
        // Сбрасываем все категории
        document.querySelectorAll('.category-select').forEach(other => {
            if (other !== radio) other.checked = false;
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
        
        // Добавляем выделение к выбранной категории
        radio.closest('.category-block').classList.add('selected');
        updateActionButtons();
    }
    
    function selectLesson(radio) {
        // Сбрасываем все уроки
        document.querySelectorAll('.lesson-select').forEach(other => {
            if (other !== radio) other.checked = false;
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
        
        // Добавляем выделение к выбранному уроку
        const lessonElement = radio.closest('li') || radio.closest('.category-block[data-id^="uncat-"]');
        if (lessonElement) {
            lessonElement.classList.add('selected');
        }
        updateActionButtons();

        // Переход к detail view выбранного урока
        if (radio && radio.value) {
            fetch('/builder/lesson/' + radio.value + '/?ajax=1')
            .then(r => {
                if (!r.ok) throw new Error('Ошибка загрузки');
                return r.text();
            })
            .then(html => {
                document.getElementById('detail').innerHTML = html;
                initVersionHistoryDropdown(); // <-- добавлено!
            })
            .catch(e => {
                alert('Ошибка загрузки урока: ' + e.message);
            });
        }
    }
    
    initCategoryCheckboxHandlers();
    initLessonCheckboxHandlers();
    
    // Инициализация: сбрасываем все выделения при загрузке
    document.querySelectorAll('.category-select, .lesson-select').forEach(cb => cb.checked = false);
    document.querySelectorAll('.category-block').forEach(block => block.classList.remove('selected'));
    document.querySelectorAll('.lesson-list li').forEach(li => li.classList.remove('selected'));

    // Сброс выделения при клике вне элементов
    document.addEventListener('click', function(e) {
        // Не сбрасываем если кликнули на элементы, которые должны активировать выделение
        if (e.target.closest('.category-header') || 
            e.target.closest('.lesson-list li') || 
            e.target.closest('.category-block[data-id^="uncat-"]') ||
            e.target.closest('#custom-context-menu') ||
            e.target.closest('.toggle-arrow')) {
            return;
        }
        
        // Сбрасываем все чекбоксы
        document.querySelectorAll('.category-select, .lesson-select').forEach(cb => cb.checked = false);
        // Сбрасываем все выделения
        document.querySelectorAll('.category-block').forEach(block => block.classList.remove('selected'));
        document.querySelectorAll('.lesson-list li').forEach(li => li.classList.remove('selected'));
        updateActionButtons();
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
        if (addLessonBtn) addLessonBtn.disabled = !!lessonId;
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
        const mirrorBtn = document.getElementById('mirror-menu-item');

        if (pasteBtn) {
            pasteBtn.style.opacity = clipboardData ? '1' : '0.5';
            pasteBtn.style.cursor = clipboardData ? 'pointer' : 'not-allowed';
            pasteBtn.style.pointerEvents = clipboardData ? '' : 'none';
        }

        // Mirror: только если contextTarget — урок
        let mirrorActive = false;
        if (contextTarget) {
            if (contextTarget.dataset && contextTarget.dataset.id && contextTarget.dataset.id.startsWith('uncat-')) {
                mirrorActive = true;
            } else if (
                contextTarget.classList.contains('.lesson-li') || 
                (contextTarget.classList.contains('category-block') && contextTarget.querySelector('.lesson-link') && !contextTarget.classList.contains('category-block'))
             ) { mirrorActive = true;
            } else if (
                contextTarget.classList.contains('lesson-li') || 
                (contextTarget.classList.contains('category-block') && contextTarget.querySelector('.lesson-link') && !contextTarget.classList.contains('category-block'))
            ) {
                mirrorActive = true;
            }

        }
        if (mirrorBtn) {
            mirrorBtn.style.opacity = mirrorActive ? '1' : '0.5';
            mirrorBtn.style.cursor = mirrorActive ? 'pointer' : 'not-allowed';
            mirrorBtn.style.pointerEvents = mirrorActive ? '' : 'none';
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
        if (contextTarget.dataset.id && contextTarget.dataset.id.startsWith('uncat-')) {
            // Урок без категории
            itemType = 'lesson';
            itemId = contextTarget.dataset.id.replace('uncat-', '');
        } else if (contextTarget.classList.contains('category-block')) {
            // Категория
            itemType = 'category';
            itemId = contextTarget.dataset.id;
        } else if (contextTarget.querySelector('.lesson-link')) {
            // Обычный урок
            itemType = 'lesson';
            itemId = contextTarget.querySelector('.lesson-select')?.value;
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
        if (contextTarget.dataset.id && contextTarget.dataset.id.startsWith('uncat-')) {
            // Урок без категории
            itemType = 'lesson';
            itemId = contextTarget.dataset.id.replace('uncat-', '');
        } else if (contextTarget.classList.contains('category-block')) {
            // Категория
            itemType = 'category';
            itemId = contextTarget.dataset.id;
        } else if (contextTarget.querySelector('.lesson-link')) {
            // Обычный урок
            itemType = 'lesson';
            itemId = contextTarget.querySelector('.lesson-select')?.value;
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
    
    // Зеркало
    document.getElementById('mirror-menu-item').addEventListener('click', function() {
        if (this.style.pointerEvents === 'none') return;
        if (!contextTarget) return;
        
        let itemId, itemType;
        if (contextTarget.dataset.id && contextTarget.dataset.id.startsWith('uncat-')) {
            itemType = 'lesson';
            itemId = contextTarget.dataset.id.replace('uncat-', '');
        } else if (contextTarget.classList.contains('category-block')) {
            // Категории зеркалировать не надо
            return;
        } else if (contextTarget.querySelector('.lesson-link')) {
            itemType = 'lesson';
            itemId = contextTarget.querySelector('.lesson-select')?.value;
        }
    
        if (!itemId || itemType !== 'lesson') return;
    
        // Показываем модалку выбора категории
        function doMirror(targetCategory) {
            fetch('/builder/mirror/', {
                method: 'POST',
                headers: { 'X-CSRFToken': (document.querySelector('[name=csrfmiddlewaretoken]')||{}).value || '', 'Content-Type': 'application/json' },
                body: JSON.stringify({ lesson_id: itemId, category_id: targetCategory })
            }).then(r => r.json()).then(data => {
                if (data.error) { alert('Ошибка: ' + data.error); return; }
                alert('Зеркало создано!');
                window.location.reload();
            }).catch(error => {
                alert('Ошибка сети: ' + error.message);
            });
        }
        // Если дерево уже загружено — сразу показываем
        if (window.categoryTreeData) {
            showMirrorCategorySelect({
                onSelect: doMirror,
                onCancel: null,
                categories: window.categoryTreeData
            });
        } else {
            fetchCategoryTreeForMirror().then(() => {
                showMirrorCategorySelect({
                    onSelect: doMirror,
                    onCancel: null,
                    categories: window.categoryTreeData
                });
            });
        }
    });


    // --- Контекстное меню на вкладках ---
    document.getElementById('tab-categories')?.addEventListener('contextmenu', function(e) {
        e.preventDefault();
        contextTarget = { tab: 'categories' };
        const menu = document.getElementById('custom-context-menu');
        menu.style.display = 'block';
        menu.style.left = e.pageX + 'px';
        menu.style.top = e.pageY + 'px';
        updatePasteButton();
    });
    document.getElementById('tab-uncat')?.addEventListener('contextmenu', function(e) {
        e.preventDefault();
        contextTarget = { tab: 'uncat' };
        const menu = document.getElementById('custom-context-menu');
        menu.style.display = 'block';
        menu.style.left = e.pageX + 'px';
        menu.style.top = e.pageY + 'px';
        updatePasteButton();
    });
    
    // Вставить
    document.getElementById('paste-menu-item').addEventListener('click', function() {
        if (!clipboardData || !contextTarget) return;

        let targetCategory = '';
        let isCategory = clipboardData.type === 'category';
        let isUncatLesson = contextTarget.dataset && contextTarget.dataset.id && contextTarget.dataset.id.startsWith('uncat-');
        let isLesson = (contextTarget.classList && contextTarget.classList.contains('lesson-li')) || (contextTarget.dataset && contextTarget.dataset.id && contextTarget.dataset.id.startsWith('uncat-'));

        // Контекстное меню на вкладках
        if (contextTarget.tab === 'categories') {
            targetCategory = '';
        } else if (contextTarget.tab === 'uncat') {
            targetCategory = '';
        } else if (isUncatLesson) {
            targetCategory = '';
        } else if (contextTarget.classList && contextTarget.classList.contains('category-list')) {
            targetCategory = '';
        } else if (contextTarget.classList && contextTarget.classList.contains('category-block')) {
            targetCategory = contextTarget.dataset.id;
        } else {
            const parentCategory = contextTarget.closest && contextTarget.closest('.category-block');
            targetCategory = parentCategory ? parentCategory.dataset.id : '';
        }

        // Если вставляем категорию в урок или в "Без категории" — предупреждение
        if (isCategory && (isUncatLesson || isLesson || contextTarget.tab === 'uncat')) {
            showCategoryPasteWarning({
                onYes: () => {
                    // Проверка: если категория уже в корне, ничего не делать
                    const catElem = document.querySelector(`[data-id='${clipboardData.id}']`);
                    if (catElem && (!catElem.dataset.parent || catElem.dataset.parent === '')) {
                        // Уже в корне — просто закрыть окно
                        return;
                    }
                    doPaste('');
                },
                onNo: () => {}
            });
            return;
        }

        doPaste(targetCategory);

        function doPaste(targetCategory) {
            fetch('/builder/paste/', {
                method: 'POST',
                headers: { 'X-CSRFToken': (document.querySelector('[name=csrfmiddlewaretoken]')||{}).value || '', 'Content-Type': 'application/json' },
                body: JSON.stringify({ target_category: targetCategory })
            }).then(r => r.json()).then(data => {
                if (data.error) { alert('Ошибка: ' + data.error); return; }
                if (data.result) {
                    if (clipboardData.action === 'cut') {
                        let originalElement = null;
                        if (clipboardData.type === 'lesson') {
                            originalElement = document.querySelector(`.lesson-select[value="${clipboardData.id}"]`)?.closest('li');
                            if (!originalElement) {
                                originalElement = document.querySelector(`[data-id="uncat-${clipboardData.id}"]`);
                            }
                        } else if (clipboardData.type === 'category') {
                            originalElement = document.querySelector(`[data-id="${clipboardData.id}"]`);
                            if (originalElement) originalElement.remove();
                        }
                    }
                    window.location.reload();
                }
                clipboardData = null;
                updatePasteButton();
                document.getElementById('custom-context-menu').style.display = 'none';
            }).catch(error => {
                alert('Ошибка сети: ' + error.message);
            });
        }
    });
    
    // Инициализация буфера обмена
    checkClipboard();

    // --- Переключение вкладок Категории/Без категории ---
    document.getElementById('tab-categories')?.addEventListener('click', function() {
        this.classList.add('active');
        document.getElementById('tab-uncat').classList.remove('active');
        document.getElementById('categories-block').style.display = '';
        document.getElementById('uncategorized-block').style.display = 'none';
    });
    document.getElementById('tab-uncat')?.addEventListener('click', function() {
        this.classList.add('active');
        document.getElementById('tab-categories').classList.remove('active');
        document.getElementById('categories-block').style.display = 'none';
        document.getElementById('uncategorized-block').style.display = '';
    });

    // --- История версий ---
    const versionBtn = document.getElementById('version-history-btn');
    const versionDropdown = document.getElementById('version-history-dropdown');
    if (versionBtn && versionDropdown) {
        versionBtn.addEventListener('click', function(e) {
            versionDropdown.style.display = versionDropdown.style.display === 'none' ? 'block' : 'none';
        });
        document.addEventListener('click', function(e) {
            if (!versionBtn.contains(e.target) && !versionDropdown.contains(e.target)) {
                versionDropdown.style.display = 'none';
            }
        });
        versionDropdown.querySelectorAll('.version-item').forEach(function(item) {
            item.addEventListener('click', function() {
                // Показываем детали выбранной версии
                document.querySelector('h2').textContent = item.dataset.title;
                document.getElementById('lesson-content-block').innerHTML = item.dataset.content;
                if (item.dataset.video) {
                    document.getElementById('lesson-video-block').innerHTML = `<h5>Видео урок:</h5><iframe width=\"560\" height=\"315\" src=\"https://rutube.ru/play/embed/${item.dataset.video}\" frameborder=\"0\" allowfullscreen></iframe>`;
                } else {
                    const vblock = document.getElementById('lesson-video-block');
                    if (vblock) vblock.innerHTML = '';
                }
                versionDropdown.style.display = 'none';
            });
        });
    }

    // --- Кнопка Контроль обновлений ---
    const updateControlBtn = document.getElementById('update-control-btn');
    function getSelectedLessonIdForUpdateBtn() {
        // Просто ищем выбранный radio .lesson-select
        const checked = document.querySelector('.lesson-select:checked');
        return checked ? checked.value : null;
    }
    function updateUpdateControlBtnState() {
        if (!updateControlBtn) return;
        const lessonId = getSelectedLessonIdForUpdateBtn();
        updateControlBtn.disabled = !lessonId;
        if (lessonId) {
            updateControlBtn.onclick = function() {
                window.location.href = `/builder/lesson/${lessonId}/update_control/new/`;
            };
        } else {
            updateControlBtn.onclick = null;
        }
    }
    if (updateControlBtn) {
        updateUpdateControlBtnState();
        document.addEventListener('click', function(e) {
            setTimeout(updateUpdateControlBtnState, 100); // после клика по дереву
        });
    }
});

function initVersionHistoryDropdown() {
    const versionBtn = document.getElementById('version-history-btn');
    const versionDropdown = document.getElementById('version-history-dropdown');
    if (versionBtn && versionDropdown) {
        versionBtn.onclick = function(e) {
            versionDropdown.style.display = versionDropdown.style.display === 'none' ? 'block' : 'none';
        };
        document.addEventListener('click', function handler(e) {
            if (!versionBtn.contains(e.target) && !versionDropdown.contains(e.target)) {
                versionDropdown.style.display = 'none';
                document.removeEventListener('click', handler);
            }
        });
        versionDropdown.querySelectorAll('.version-item').forEach(function(item) {
            item.onclick = function() {
                document.querySelector('h2').textContent = item.dataset.title;
                document.getElementById('lesson-content-block').innerHTML = item.dataset.content;
                if (item.dataset.video) {
                    document.getElementById('lesson-video-block').innerHTML = `<h5>Видео урок:</h5><iframe width="560" height="315" src="https://rutube.ru/play/embed/${item.dataset.video}" frameborder="0" allowfullscreen></iframe>`;
                } else {
                    const vblock = document.getElementById('lesson-video-block');
                    if (vblock) vblock.innerHTML = '';
                }
                versionDropdown.style.display = 'none';
            };
        });
    }
}

function showCategoryPasteWarning({onYes, onNo}) {
    let modal = document.getElementById('category-paste-warning-modal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'category-paste-warning-modal';
        modal.innerHTML = `
        <div style="position:fixed;z-index:99999;left:0;top:0;width:100vw;height:100vh;background:rgba(0,0,0,0.35);display:flex;align-items:center;justify-content:center;">
            <div style="background:#232a3a;color:#fff;padding:32px 32px 24px 32px;border-radius:12px;box-shadow:0 2px 16px #0007;min-width:320px;max-width:90vw;text-align:center;">
                <div style="font-size:1.15em;margin-bottom:18px;">Категория будет создана в корне дерева. Продолжить?</div>
                <div style="display:flex;gap:18px;justify-content:center;">
                    <button id="cat-paste-yes" style="padding:8px 24px;font-size:1em;border-radius:6px;border:none;background:#4d7cff;color:#fff;cursor:pointer;">Да</button>
                    <button id="cat-paste-no" style="padding:8px 24px;font-size:1em;border-radius:6px;border:none;background:#444;color:#fff;cursor:pointer;">Нет</button>
                </div>
            </div>
        </div>`;
        document.body.appendChild(modal);
    } else {
        modal.style.display = '';
    }
    function cleanup() {
        modal.style.display = 'none';
    }
    modal.querySelector('#cat-paste-yes').onclick = function() { cleanup(); onYes && onYes(); };
    modal.querySelector('#cat-paste-no').onclick = function() { cleanup(); onNo && onNo(); };
}

// --- Модалка выбора категории для зеркала ---
function showMirrorCategorySelect({onSelect, onCancel, categories}) {
    // Удаляем старую модалку если есть
    let modal = document.getElementById('mirror-category-select-modal');
    if (modal) modal.remove();
    // Рекурсивная функция для отрисовки дерева
    function renderTree(cats, level=0) {
        let html = '<ul style="list-style:none;padding-left:'+(level*18)+'px;">';
        for (const cat of cats) {
            html += `<li style="margin-bottom:4px;">
                <label style="cursor:pointer;">
                    <input type="radio" name="mirror-cat-radio" value="${cat.id}" style="margin-right:8px;">${cat.name}
                </label>`;
            if (cat.subcategories && cat.subcategories.length) {
                html += renderTree(cat.subcategories, level+1);
            }
            html += '</li>';
        }
        html += '</ul>';
        return html;
    }
    // Получаем дерево категорий из window.categoryTreeData (или передать через параметр)
    let cats = window.categoryTreeData || categories || [];
    let html = `
    <div style="position:fixed;z-index:99999;left:0;top:0;width:100vw;height:100vh;background:rgba(0,0,0,0.35);display:flex;align-items:center;justify-content:center;">
        <div style="background:#232a3a;color:#fff;padding:32px 32px 24px 32px;border-radius:12px;box-shadow:0 2px 16px #0007;min-width:320px;max-width:90vw;text-align:center;">
            <style>#mirror-category-select-modal * { color: #fff !important; }</style>
            <div style="font-size:1.15em;margin-bottom:18px;">Выберите категорию для зеркала</div>
            <div style="max-height:320px;overflow-y:auto;text-align:left;margin-bottom:18px;">${renderTree(cats)}</div>
            <div style="display:flex;gap:18px;justify-content:center;">
                <button id="mirror-cat-yes" style="padding:8px 24px;font-size:1em;border-radius:6px;border:none;background:#4d7cff;color:#fff;cursor:pointer;">Продолжить</button>
                <button id="mirror-cat-no" style="padding:8px 24px;font-size:1em;border-radius:6px;border:none;background:#444;color:#fff;cursor:pointer;">Отмена</button>
            </div>
        </div>
    </div>`;
    modal = document.createElement('div');
    modal.id = 'mirror-category-select-modal';
    modal.innerHTML = html;
    document.body.appendChild(modal);
    modal.querySelector('#mirror-cat-yes').onclick = function() {
        const val = modal.querySelector('input[name="mirror-cat-radio"]:checked');
        if (!val) { alert('Выберите категорию!'); return; }
        modal.remove();
        onSelect && onSelect(val.value);
    };
    modal.querySelector('#mirror-cat-no').onclick = function() {
        modal.remove();
        onCancel && onCancel();
    };
}

// --- Получение дерева категорий для модалки (один раз при загрузке) ---
function fetchCategoryTreeForMirror() {
    // Можно использовать существующий endpoint или сделать отдельный ajax
    // Здесь предполагаем, что get_category_tree_data(0) отдаёт всё дерево
    return fetch('/builder/category_tree_json/')
        .then(r => r.json())
        .then(data => {
            window.categoryTreeData = data.categories || [];
        });
}
