let contextTarget = null;

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
    const IS_READONLY = window.IS_READONLY;
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

    // --- Переключение вкладок Категории/Без категории/Словарь ---
    document.getElementById('tab-categories')?.addEventListener('click', function() {
        this.classList.add('active');
        document.getElementById('tab-uncat').classList.remove('active');
        document.getElementById('tab-dict').classList.remove('active');
        document.getElementById('categories-block').style.display = '';
        document.getElementById('uncategorized-block').style.display = 'none';
        document.getElementById('dict-block').style.display = 'none';
    });
    document.getElementById('tab-uncat')?.addEventListener('click', function() {
        this.classList.add('active');
        document.getElementById('tab-categories').classList.remove('active');
        document.getElementById('tab-dict').classList.remove('active');
        document.getElementById('categories-block').style.display = 'none';
        document.getElementById('uncategorized-block').style.display = '';
        document.getElementById('dict-block').style.display = 'none';
    });
    document.getElementById('tab-dict')?.addEventListener('click', function() {
        this.classList.add('active');
        document.getElementById('tab-categories').classList.remove('active');
        document.getElementById('tab-uncat').classList.remove('active');
        document.getElementById('categories-block').style.display = 'none';
        document.getElementById('uncategorized-block').style.display = 'none';
        document.getElementById('dict-block').style.display = '';
    });
    // --- Клик по термину словаря ---
    document.querySelectorAll('#dict-block .category-block').forEach(li => {
        li.addEventListener('click', function(e) {
            // Не реагировать на клики по svg и иконкам
            if (e.target.closest('svg') || e.target.classList.contains('lesson-icon')) return;
            // Сброс выделения у категорий (оставляем выделенным только термин)
            document.querySelectorAll('.category-select').forEach(cb => cb.checked = false);
            document.querySelectorAll('.category-block').forEach(block => block.classList.remove('selected'));
            // Сброс выделения у уроков (оставляем выделенным только термин)
            document.querySelectorAll('.lesson-select').forEach(cb => cb.checked = false);
            document.querySelectorAll('.lesson-list li').forEach(li => li.classList.remove('selected'));
            // Сброс выделения у всех терминов словаря, выделяем только текущий
            document.querySelectorAll('#dict-block .category-block').forEach(el => el.classList.remove('selected'));
            li.classList.add('selected');
            const sectionId = li.dataset.id.replace(/^[^\d]+/, '');
            fetch(`/builder/dictionary/${sectionId}/?ajax=1`)
                .then(r => r.json())
                .then(resp => {
                    document.getElementById('detail').innerHTML = resp.html;
                    window._dictSectionData = resp.data;
                    window._dictSectionId = resp.section_id;
                    initVersionHistoryDropdown();
                    if (typeof initActualizationHistoryDropdown === 'function') initActualizationHistoryDropdown();
                    initDictHotTable();
                })
                .catch(e => {
                    alert('Ошибка загрузки урока: ' + e.message);
                });
        });
    });
    // --- Клик по отделу словаря ---
    document.querySelectorAll('#dict-block .dict-section-link').forEach(link => {
        link.addEventListener('click', function(e) {
            const li = this.closest('.category-block');
            // Сброс выделения у всех отделов
            document.querySelectorAll('#dict-block .category-block').forEach(el => el.classList.remove('selected'));
            li.classList.add('selected');
            const sectionId = li.dataset.id.split('-').pop();
            fetch(`/builder/dictionary/${sectionId}/?ajax=1`)
                .then(r => r.json())
                .then(resp => {
                    document.getElementById('detail').innerHTML = resp.html;
                    window._dictSectionData = resp.data;
                    window._dictSectionId = resp.section_id;
                    // тут потом инициализация таблицы
                    initDictHotTable();
                })
                .catch(e => alert('Ошибка загрузки отдела: ' + e.message));
        });
    });
    // === КНОПКИ ДЕЙСТВИЙ ДЛЯ КАТЕГОРИЙ/УРОКОВ ===
    if (IS_READONLY) {
        // Отключаем контекстное меню и действия copy/cut/paste/mirror
        // Не вешаем обработчики contextmenu, clipboard, custom-context-menu
        // Просто инициализируем выбор и раскрытие
        initCategoryCheckboxHandlers();
        initLessonCheckboxHandlers();
        // Сброс выделения при клике вне элементов
        document.addEventListener('click', function(e) {
            if (e.target.closest('.category-header') || 
                e.target.closest('.lesson-list li') || 
                e.target.closest('.category-block[data-id^="uncat-"]')) {
                return;
            }
            document.querySelectorAll('.category-select, .lesson-select').forEach(cb => cb.checked = false);
            document.querySelectorAll('.category-block').forEach(block => block.classList.remove('selected'));
            document.querySelectorAll('.lesson-list li').forEach(li => li.classList.remove('selected'));
        });
        // Делегируем клик по стрелке для раскрытия/сворачивания категорий
        document.addEventListener('click', function(e) {
            if (e.target.classList.contains('toggle-arrow')) {
                toggleSubcat(e.target.parentElement);
            }
        });
    } else {
        // Код для staff пользователей остается как есть
        function getSelectedCategoryId() {
            const checked = document.querySelector('.category-select:checked');
            return checked ? checked.value : null;
        }
        function getSelectedLessonId() {
            const checked = document.querySelector('.lesson-select:checked');
            return checked ? checked.value : null;
        }
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
                // Сохраняем id новой категории для автовыделения
                if (data.id) sessionStorage.setItem('new_category_id', data.id);
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
                // Сохраняем id новой подкатегории для автовыделения
                if (data.id) sessionStorage.setItem('new_category_id', data.id);
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
        let selectedLessonElem = null;
        if (lessonId) {
            // Найти выбранный элемент урока (оригинал или зеркало)
            selectedLessonElem = document.querySelector('.lesson-select:checked')?.closest('li');
        }
        if (catId && !lessonId) {
            if (confirm('Удалить категорию?')) {
                window.location.href = `/builder/categories/${catId}/delete/`;
            }
        } else if (lessonId && selectedLessonElem) {
            // Новая логика удаления экземпляра урока/зеркала
            const mirrorId = selectedLessonElem.getAttribute('data-mirror-id');
            const isMirror = selectedLessonElem.classList.contains('mirror');

            // Если это не зеркало (нет mirrorId, нет класса mirror) — обычное удаление через Django view
            if (!mirrorId && !isMirror) {
                window.location.href = `/builder/lesson/${lessonId}/delete/`;
                return;
            }
            // Иначе — AJAX-удаление экземпляра
            const categoryId = selectedLessonElem.getAttribute('data-category-id');
            if (confirm('Удалить этот экземпляр урока?')) {
                fetch('/builder/ajax_delete_lesson_instance/', {
                    method: 'POST',
                    headers: { 'X-CSRFToken': (document.querySelector('[name=csrfmiddlewaretoken]')||{}).value || '', },
                    body: new URLSearchParams({
                        lesson_id: lessonId,
                        mirror_id: mirrorId || '',
                        category_id: categoryId || '',
                    })
                })
                .then(r => r.json())
                .then(data => {
                    if (data.error) { alert('Ошибка: ' + data.error); return; }
                    window.location.reload();
                })
                .catch(() => { alert('Ошибка сети'); });
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
        if (window.IS_READONLY) {
            // Сбрасываем все категории (оставляем выделенной только выбранную)
            document.querySelectorAll('.category-select').forEach(other => {
                if (other !== radio) other.checked = false;
            });
            document.querySelectorAll('.category-block').forEach(block => {
                block.classList.remove('selected');
            });
            // Сбрасываем все уроки при выборе категории
            document.querySelectorAll('.lesson-select').forEach(lessonCb => lessonCb.checked = false);
            document.querySelectorAll('.lesson-list li').forEach(li => li.classList.remove('selected'));
            // Добавляем выделение к выбранной категории
            radio.closest('.category-block').classList.add('selected');
            // Сброс выделения у терминов словаря (оставляем выделенной только категорию)
            document.querySelectorAll('#dict-block .category-block').forEach(el => el.classList.remove('selected'));
            return;
        }
        // Сбрасываем все категории (оставляем выделенной только выбранную)
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
        // Сброс выделения у терминов словаря (оставляем выделенной только категорию)
        document.querySelectorAll('#dict-block .category-block').forEach(el => el.classList.remove('selected'));
        updateActionButtons();
    }
    
    function selectLesson(radio) {
        if (window.IS_READONLY) {
            // Сбрасываем все уроки (оставляем выделенным только выбранный)
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
            const lessonElement = radio.closest('li') || radio.closest('.category-block[data-id^="uncat-"]');
            if (lessonElement) {
                lessonElement.classList.add('selected');
            }
            // Сброс выделения у терминов словаря (оставляем выделенным только урок)
            document.querySelectorAll('#dict-block .category-block').forEach(el => el.classList.remove('selected'));
            // Только просмотр detail
            if (radio && radio.value) {
                fetch('/builder/lesson/' + radio.value + '/?ajax=1')
                .then(r => {
                    if (!r.ok) throw new Error('Ошибка загрузки');
                    return r.text();
                })
                            .then(html => {
                document.getElementById('detail').innerHTML = html;
                
                // Выполняем скрипты из загруженного HTML
                const scripts = document.getElementById('detail').querySelectorAll('script');
                scripts.forEach(script => {
                    if (script.textContent) {
                        try {
                            eval(script.textContent);
                        } catch (e) {
                            console.error('Ошибка выполнения скрипта:', e);
                        }
                    }
                });
                
                initVersionHistoryDropdown();
                if (typeof initActualizationHistoryDropdown === 'function') initActualizationHistoryDropdown();
            })
                .catch(e => {
                    alert('Ошибка загрузки урока: ' + e.message);
                });
            }
            return;
        }
        // Сбрасываем все уроки (оставляем выделенным только выбранный)
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
        // Сброс выделения у терминов словаря (оставляем выделенным только урок)
        document.querySelectorAll('#dict-block .category-block').forEach(el => el.classList.remove('selected'));
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
                
                // Выполняем скрипты из загруженного HTML
                const scripts = document.getElementById('detail').querySelectorAll('script');
                scripts.forEach(script => {
                    if (script.textContent) {
                        try {
                            eval(script.textContent);
                        } catch (e) {
                            console.error('Ошибка выполнения скрипта:', e);
                        }
                    }
                });
                
                initVersionHistoryDropdown();
                if (typeof initActualizationHistoryDropdown === 'function') initActualizationHistoryDropdown();
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
    // Удалён обработчик сброса выделения при клике вне элементов
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

 

    // === Кастомное контекстное меню для копирования/вырезания/вставки ===
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
        if (window.IS_READONLY) return; // не показываем контекстное меню обучающимся
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
            const showMirrorsItem = document.getElementById('show-all-mirrors-menu-item');
            const hideMirrorsItem = document.getElementById('hide-mirrors-menu-item');
            let show = false;
            if (li.classList.contains('lesson-li') || (li.dataset.id && li.dataset.id.startsWith('uncat-'))) {
                if (li.hasAttribute('data-has-mirrors')) show = true;
                if (li.hasAttribute('data-mirror-id')) show = true;
                if (li.classList.contains('mirror')) show = true;
            }
            if (window._mirrorsFilterActive) {
                showMirrorsItem.style.display = 'none';
                hideMirrorsItem.style.display = '';
            } else {
                if (show) {
                    showMirrorsItem.style.display = '';
                } else {
                    showMirrorsItem.style.display = 'none';
                }
                hideMirrorsItem.style.display = 'none';
            }
        } else if (ul && clipboardData) {
            document.getElementById('show-all-mirrors-menu-item').style.display = 'none';
            document.getElementById('hide-mirrors-menu-item').style.display = 'none';
        } else {
            document.getElementById('custom-context-menu').style.display = 'none';
            document.getElementById('show-all-mirrors-menu-item').style.display = 'none';
            document.getElementById('hide-mirrors-menu-item').style.display = 'none';
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
    let mirrorSourceLessonId = null;
    const mirrorHereMenuItem = document.getElementById('mirror-here-menu-item');

    document.getElementById('mirror-menu-item').addEventListener('click', function() {
        if (!contextTarget) return;
        // Сохраняем id урока, который хотим зеркалировать
        if (contextTarget.dataset.id && contextTarget.dataset.id.startsWith('uncat-')) {
            mirrorSourceLessonId = contextTarget.dataset.id.replace('uncat-', '');
        } else if (contextTarget.querySelector('.lesson-link')) {
            mirrorSourceLessonId = contextTarget.querySelector('.lesson-select')?.value;
        }
        // Активируем пункт 'Вставить зеркало'
        if (mirrorHereMenuItem) {
            mirrorHereMenuItem.style.opacity = '1';
            mirrorHereMenuItem.style.pointerEvents = '';
            mirrorHereMenuItem.style.cursor = 'pointer';
        }
        // Теперь пользователь должен кликнуть правой кнопкой по категории и выбрать "Вставить зеркало"
        alert('Теперь выберите категорию, куда вставить зеркало, через контекстное меню!');
    });

    // Деактивируем пункт 'Вставить зеркало' по умолчанию
    if (mirrorHereMenuItem) {
        mirrorHereMenuItem.style.opacity = '0.5';
        mirrorHereMenuItem.style.pointerEvents = 'none';
        mirrorHereMenuItem.style.cursor = 'not-allowed';
    }

    // При клике на 'Вставить зеркало' в меню категории
    mirrorHereMenuItem.addEventListener('click', function() {
        if (!contextTarget || !mirrorSourceLessonId) return;
        let targetCategoryId = null;
        if (contextTarget.classList.contains('category-block')) {
            targetCategoryId = contextTarget.dataset.id;
        }
        if (!targetCategoryId) {
            alert('Выберите категорию!');
            return;
        }
        fetch('/builder/mirror/', {
            method: 'POST',
            headers: { 'X-CSRFToken': (document.querySelector('[name=csrfmiddlewaretoken]')||{}).value || '', 'Content-Type': 'application/json' },
            body: JSON.stringify({ lesson_id: mirrorSourceLessonId, category_id: targetCategoryId })
        }).then(r => r.json()).then(data => {
            if (data.error) { alert('Ошибка: ' + data.error); return; }
            alert('Зеркало создано!');
            window.location.reload();
        }).catch(error => {
            alert('Ошибка сети: ' + error.message);
        });
        mirrorSourceLessonId = null; // сбрасываем после вставки
        // Деактивируем пункт снова
        if (mirrorHereMenuItem) {
            mirrorHereMenuItem.style.opacity = '0.5';
            mirrorHereMenuItem.style.pointerEvents = 'none';
            mirrorHereMenuItem.style.cursor = 'not-allowed';
        }
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

    // --- История версий ---
    function initVersionHistoryDropdown() {
        const versionBtn = document.getElementById('version-history-btn');
        const versionDropdown = document.getElementById('version-history-dropdown');
        if (!versionBtn || !versionDropdown) return;
    
        // Снимаем старые обработчики
        versionBtn.onclick = null;
        versionDropdown.onclick = null;
    
        // Открытие/закрытие дропдауна
        versionBtn.onclick = function(e) {
            e.stopPropagation();
            versionDropdown.style.display = versionDropdown.style.display === 'none' ? 'block' : 'none';
        };
        versionDropdown.onclick = function(e) {
            e.stopPropagation();
        };
    
        // Снимаем старый обработчик document (если был)
        document.removeEventListener('click', window._versionDropdownDocHandler);
    
        // Новый обработчик document
        window._versionDropdownDocHandler = function(e) {
            if (!versionBtn.contains(e.target) && !versionDropdown.contains(e.target)) {
                versionDropdown.style.display = 'none';
            }
        };
        document.addEventListener('click', window._versionDropdownDocHandler);
    
        // Обработчики на элементы версий
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

    initVersionHistoryDropdown();

    // --- История актуализаций ---
    function initActualizationHistoryDropdown() {
        const actualBtn = document.getElementById('actualization-history-btn');
        const actualDropdown = document.getElementById('actualization-history-dropdown');
        if (!actualBtn || !actualDropdown) return;

        actualBtn.onclick = function(e) {
            e.stopPropagation();
            actualDropdown.style.display = actualDropdown.style.display === 'none' ? 'block' : 'none';
        };
        actualDropdown.onclick = function(e) { e.stopPropagation(); };
        document.removeEventListener('click', window._actualDropdownDocHandler);
        window._actualDropdownDocHandler = function(e) {
            if (!actualBtn.contains(e.target) && !actualDropdown.contains(e.target)) {
                actualDropdown.style.display = 'none';
            }
        };
        document.addEventListener('click', window._actualDropdownDocHandler);

        
        actualDropdown.querySelectorAll('td.version-cell').forEach(function(cell) {
            cell.style.cursor = 'pointer';
            cell.style.textDecoration = 'underline';
            cell.onclick = function(e) {
                e.stopPropagation();
                
                const version = cell.getAttribute('data-version');
                
                // Ищем версию в массиве
                const v = (window._lessonVersions||[]).find(x => String(x.version) === String(version));
                                
                
                // Обновляем содержимое урока
                const titleElement = document.querySelector('h2');
                const contentElement = document.getElementById('lesson-content-block');
                const videoElement = document.getElementById('lesson-video-block');
                                
                if (titleElement) {
                    titleElement.textContent = v.title;
                }
                if (contentElement) {
                    contentElement.innerHTML = v.content;
                }
                
                if (v.video_id && videoElement) {
                    videoElement.innerHTML = `<h5>Видео урок:</h5><iframe width="560" height="315" src="https://rutube.ru/play/embed/${v.video_id}" frameborder="0" allowfullscreen></iframe>`;
                } else if (videoElement) {
                    videoElement.innerHTML = '';
                }
                
                actualDropdown.style.display = 'none';
            };
        });

        // Кнопка "Актуализировать" (теперь одна)
        const mainActualizeBtn = document.getElementById('actualize-main-btn');
        if (mainActualizeBtn) {
            mainActualizeBtn.onclick = function(e) {
                e.preventDefault();
                e.stopPropagation();
                const id = document.getElementById('actualize-lesson-id')?.value;
                if (!id) {
                    alert('Не удалось определить ID урока');
                    return;
                }
                mainActualizeBtn.disabled = true;
                fetch('/builder/actualize_version/', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': (document.querySelector('[name=csrfmiddlewaretoken]')||{}).value || '',
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ lesson_id: id })
                })
                .then(r => r.json())
                .then(data => {
                    if (data.error) {
                        alert('Ошибка: ' + data.error);
                        mainActualizeBtn.disabled = false;
                        return;
                    }
                    // Обновляем detail-блок (AJAX reload)
                    if (window.location.href.match(/lesson\/(\d+)/)) {
                        const lessonId = window.location.href.match(/lesson\/(\d+)/)[1];
                        fetch(`/builder/lesson/${lessonId}/?ajax=1`)
                            .then(r => r.text())
                            .then(html => {
                                document.getElementById('detail').innerHTML = html;
                                // initVersionHistoryDropdown();
                                initActualizationHistoryDropdown();
                                initDictHotTable(); // <--- добавлено
                            });
                    } else {
                        window.location.reload();
                    }
                })
                .catch(() => {
                    alert('Ошибка сети');
                    mainActualizeBtn.disabled = false;
                });
            };
        }
    }
    initActualizationHistoryDropdown();

    // === АВТОВЫДЕЛЕНИЕ только что созданной категории ===
    const newCatId = sessionStorage.getItem('new_category_id');
    if (newCatId) {
        setTimeout(() => {
            const radio = document.querySelector(`.category-select[value='${newCatId}']`);
            const li = document.querySelector(`.category-block[data-id='${newCatId}']`);
            if (radio) radio.checked = true;
            if (li) li.classList.add('selected');
            // --- раскрываем всех родителей ---
            let parent = li && li.parentElement;
            while (parent && !parent.classList.contains('category-list')) {
                if (parent.classList.contains('subcategory-list') || parent.classList.contains('lesson-list')) {
                    parent.style.display = 'block';
                }
                if (parent.classList.contains('category-block')) {
                    const header = parent.querySelector('.category-header');
                    if (header && !header.classList.contains('open')) {
                        header.classList.add('open');
                        // Меняем стрелку
                        const arrow = header.querySelector('.toggle-arrow');
                        if (arrow) arrow.innerHTML = '&#9660;';
                    }
                }
                parent = parent.parentElement;
            }
            sessionStorage.removeItem('new_category_id');
            // Прокручиваем к новой категории
            if (li) li.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }, 100);
    }
    // === АВТОВЫДЕЛЕНИЕ только что созданного урока ===
    const newLessonId = sessionStorage.getItem('new_lesson_id');
    if (newLessonId) {
        setTimeout(() => {
            // Сначала ищем среди уроков без категории
            const uncatLi = document.querySelector(`.category-block[data-id='uncat-${newLessonId}']`);
            if (uncatLi) {
                // Активируем вкладку 'Без категории'
                const tabUncat = document.getElementById('tab-uncat');
                const tabCat = document.getElementById('tab-categories');
                if (tabUncat) tabUncat.classList.add('active');
                if (tabCat) tabCat.classList.remove('active');
                const blockUncat = document.getElementById('uncategorized-block');
                const blockCat = document.getElementById('categories-block');
                if (blockUncat) blockUncat.style.display = '';
                if (blockCat) blockCat.style.display = 'none';
                uncatLi.classList.add('selected');
                uncatLi.scrollIntoView({ behavior: 'smooth', block: 'center' });
                sessionStorage.removeItem('new_lesson_id');
                // Удаляем ?new_lesson=... из адресной строки
                if (window.history.replaceState) {
                    const url = new URL(window.location);
                    url.searchParams.delete('new_lesson');
                    window.history.replaceState({}, document.title, url.pathname + url.search);
                }
                return;
            }
            // Обычный урок в категории
            const li = document.querySelector(`.lesson-li[data-lesson-id='${newLessonId}']`);
            if (li) li.classList.add('selected');
            // раскрываем всех родителей
            let parent = li && li.parentElement;
            while (parent && !parent.classList.contains('category-list')) {
                if (parent.classList.contains('subcategory-list') || parent.classList.contains('lesson-list')) {
                    parent.style.display = 'block';
                }
                if (parent.classList.contains('category-block')) {
                    const header = parent.querySelector('.category-header');
                    if (header && !header.classList.contains('open')) {
                        header.classList.add('open');
                        const arrow = header.querySelector('.toggle-arrow');
                        if (arrow) arrow.innerHTML = '&#9660;';
                    }
                }
                parent = parent.parentElement;
            }
            sessionStorage.removeItem('new_lesson_id');
            if (li) li.scrollIntoView({ behavior: 'smooth', block: 'center' });
            // Удаляем ?new_lesson=... из адресной строки
            if (window.history.replaceState) {
                const url = new URL(window.location);
                url.searchParams.delete('new_lesson');
                window.history.replaceState({}, document.title, url.pathname + url.search);
            }
        }, 100);
    }
    // === АВТОВЫДЕЛЕНИЕ только что отредактированного урока ===
    const editedLessonId = sessionStorage.getItem('edited_lesson_id');
    if (editedLessonId) {
        setTimeout(() => {
            // Сначала ищем среди уроков без категории
            const uncatLi = document.querySelector(`.category-block[data-id='uncat-${editedLessonId}']`);
            if (uncatLi) {
                // Активируем вкладку 'Без категории'
                const tabUncat = document.getElementById('tab-uncat');
                const tabCat = document.getElementById('tab-categories');
                if (tabUncat) tabUncat.classList.add('active');
                if (tabCat) tabCat.classList.remove('active');
                const blockUncat = document.getElementById('uncategorized-block');
                const blockCat = document.getElementById('categories-block');
                if (blockUncat) blockUncat.style.display = '';
                if (blockCat) blockCat.style.display = 'none';
                uncatLi.classList.add('selected');
                uncatLi.scrollIntoView({ behavior: 'smooth', block: 'center' });
                sessionStorage.removeItem('edited_lesson_id');
                // Удаляем ?edited_lesson=... из адресной строки
                if (window.history.replaceState) {
                    const url = new URL(window.location);
                    url.searchParams.delete('edited_lesson');
                    window.history.replaceState({}, document.title, url.pathname + url.search);
                }
                return;
            }
            // Обычный урок в категории
            const li = document.querySelector(`.lesson-li[data-lesson-id='${editedLessonId}']`);
            if (li) li.classList.add('selected');
            // раскрываем всех родителей
            let parent = li && li.parentElement;
            while (parent && !parent.classList.contains('category-list')) {
                if (parent.classList.contains('subcategory-list') || parent.classList.contains('lesson-list')) {
                    parent.style.display = 'block';
                }
                if (parent.classList.contains('category-block')) {
                    const header = parent.querySelector('.category-header');
                    if (header && !header.classList.contains('open')) {
                        header.classList.add('open');
                        const arrow = header.querySelector('.toggle-arrow');
                        if (arrow) arrow.innerHTML = '&#9660;';
                    }
                }
                parent = parent.parentElement;
            }
            sessionStorage.removeItem('edited_lesson_id');
            if (li) li.scrollIntoView({ behavior: 'smooth', block: 'center' });
            // Удаляем ?edited_lesson=... из адресной строки
            if (window.history.replaceState) {
                const url = new URL(window.location);
                url.searchParams.delete('edited_lesson');
                window.history.replaceState({}, document.title, url.pathname + url.search);
            }
        }, 100);
    }
    
    // === АВТОВЫДЕЛЕНИЕ выбранного урока из URL ===
    const selectedLessonId = sessionStorage.getItem('selected_lesson_id');
    if (selectedLessonId) {
        setTimeout(() => {
            // Сначала ищем среди уроков без категории
            const uncatLi = document.querySelector(`.category-block[data-id='uncat-${selectedLessonId}']`);
            if (uncatLi) {
                // Активируем вкладку 'Без категории'
                const tabUncat = document.getElementById('tab-uncat');
                const tabCat = document.getElementById('tab-categories');
                if (tabUncat) tabUncat.classList.add('active');
                if (tabCat) tabCat.classList.remove('active');
                const blockUncat = document.getElementById('uncategorized-block');
                const blockCat = document.getElementById('categories-block');
                if (blockUncat) blockUncat.style.display = '';
                if (blockCat) blockCat.style.display = 'none';
                uncatLi.classList.add('selected');
                uncatLi.scrollIntoView({ behavior: 'smooth', block: 'center' });
                sessionStorage.removeItem('selected_lesson_id');
                return;
            }
            // Обычный урок в категории
            const li = document.querySelector(`.lesson-li[data-lesson-id='${selectedLessonId}']`);
            if (li) li.classList.add('selected');
            // раскрываем всех родителей (категории любого уровня)
            let parent = li && li.parentElement;
            while (parent) {
                if (parent.classList.contains('subcategory-list') || parent.classList.contains('lesson-list')) {
                    parent.style.display = 'block';
                }
                if (parent.classList.contains('category-block')) {
                    const header = parent.querySelector('.category-header');
                    if (header && !header.classList.contains('open')) {
                        header.classList.add('open');
                        const arrow = header.querySelector('.toggle-arrow');
                        if (arrow) arrow.innerHTML = '&#9660;';
                    }
                }
                parent = parent.parentElement;
            }
            sessionStorage.removeItem('selected_lesson_id');
            if (li) li.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }, 100);
    }
});

// === Drag&Drop сортировка для уроков без категории ===
(function() {
    if (window.IS_READONLY) return;
    const uncatList = document.querySelector('#uncategorized-block .category-list');
    if (!uncatList) return;
    let draggedEl = null;
    let dragOverEl = null;

    function handleDragStart(e) {
        draggedEl = this;
        this.classList.add('dragging');
        e.dataTransfer.effectAllowed = 'move';
    }
    function handleDragEnd(e) {
        this.classList.remove('dragging');
        draggedEl = null;
        dragOverEl = null;
        uncatList.querySelectorAll('.drag-over').forEach(el => el.classList.remove('drag-over'));
    }
    function handleDragOver(e) {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
        if (this === draggedEl) return;
        uncatList.querySelectorAll('.drag-over').forEach(el => el.classList.remove('drag-over'));
        this.classList.add('drag-over');
        dragOverEl = this;
    }
    function handleDrop(e) {
        e.preventDefault();
        if (!draggedEl || this === draggedEl) return;
        this.classList.remove('drag-over');
        // Вставляем draggedEl перед/после this
        const rect = this.getBoundingClientRect();
        const offset = e.clientY - rect.top;
        if (offset < rect.height / 2) {
            uncatList.insertBefore(draggedEl, this);
        } else {
            uncatList.insertBefore(draggedEl, this.nextSibling);
        }
        // Отправляем новый порядок на сервер (ids только числа)
        const ids = Array.from(uncatList.querySelectorAll('li.category-block[data-id^="uncat-"]'))
            .map(li => li.dataset.id.replace('uncat-', ''));
        fetch('/builder/lessons/reorder_uncat/', {
            method: 'POST',
            headers: { 'X-CSRFToken': (document.querySelector('[name=csrfmiddlewaretoken]')||{}).value || '', 'Content-Type': 'application/json' },
            body: JSON.stringify({ ids })
        }).then(r => r.json()).then(data => {
            if (data.error) alert('Ошибка сортировки: ' + data.error);
        }).catch(() => alert('Ошибка сети при сортировке!'));
    }
    // Навешиваем dnd на все li без категории
    uncatList.querySelectorAll('li.category-block[data-id^="uncat-"]').forEach(li => {
        li.setAttribute('draggable', 'true');
        li.addEventListener('dragstart', handleDragStart);
        li.addEventListener('dragend', handleDragEnd);
        li.addEventListener('dragover', handleDragOver);
        li.addEventListener('drop', handleDrop);
    });
})();

// === Drag&Drop сортировка для терминов словаря ===
(function() {
    if (window.IS_READONLY) return;
    const dictList = document.querySelector('ul.dict-list');
    if (!dictList) return;
    let draggedEl = null;
    let dragOverEl = null;

    function handleDragStart(e) {
        draggedEl = this;
        this.classList.add('dragging');
        e.dataTransfer.effectAllowed = 'move';
    }
    function handleDragEnd(e) {
        this.classList.remove('dragging');
        draggedEl = null;
        dragOverEl = null;
        dictList.querySelectorAll('.drag-over').forEach(el => el.classList.remove('drag-over'));
    }
    function handleDragOver(e) {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
        if (this === draggedEl) return;
        dictList.querySelectorAll('.drag-over').forEach(el => el.classList.remove('drag-over'));
        this.classList.add('drag-over');
        dragOverEl = this;
    }
    function handleDrop(e) {
        e.preventDefault();
        if (!draggedEl || this === draggedEl) return;
        this.classList.remove('drag-over');
        // Вставляем draggedEl перед/после this
        const rect = this.getBoundingClientRect();
        const offset = e.clientY - rect.top;
        if (offset < rect.height / 2) {
            dictList.insertBefore(draggedEl, this);
        } else {
            dictList.insertBefore(draggedEl, this.nextSibling);
        }
        // Отправляем новый порядок на сервер (ids только числа)
        const ids = Array.from(dictList.querySelectorAll('li.category-block[data-id^="dict-"]'))
            .map(li => li.dataset.id.replace('dict-', ''));
        fetch('/builder/dictionary/reorder/', {
            method: 'POST',
            headers: { 'X-CSRFToken': (document.querySelector('[name=csrfmiddlewaretoken]')||{}).value || '', 'Content-Type': 'application/json' },
            body: JSON.stringify({ ids })
        }).then(r => r.json()).then(data => {
            if (data.error) alert('Ошибка сортировки: ' + data.error);
        }).catch(() => alert('Ошибка сети при сортировке!'));
    }
    // Навешиваем dnd на все li словаря
    dictList.querySelectorAll('li.category-block[data-id^="dict-"]').forEach(li => {
        li.setAttribute('draggable', 'true');
        li.addEventListener('dragstart', handleDragStart);
        li.addEventListener('dragend', handleDragEnd);
        li.addEventListener('dragover', handleDragOver);
        li.addEventListener('drop', handleDrop);
    });
})();

// === Drag&Drop сортировка для уроков внутри категорий ===
(function() {
    if (window.IS_READONLY) return;
    document.querySelectorAll('ul.lesson-list').forEach(lessonList => {
        let draggedEl = null;
        let dragOverEl = null;
        const categoryId = lessonList.closest('.category-block')?.dataset.id;
        if (!categoryId) return;
        function handleDragStart(e) {
            draggedEl = this;
            this.classList.add('dragging');
            e.dataTransfer.effectAllowed = 'move';
        }
        function handleDragEnd(e) {
            this.classList.remove('dragging');
            draggedEl = null;
            dragOverEl = null;
            lessonList.querySelectorAll('.drag-over').forEach(el => el.classList.remove('drag-over'));
        }
        function handleDragOver(e) {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'move';
            if (this === draggedEl) return;
            lessonList.querySelectorAll('.drag-over').forEach(el => el.classList.remove('drag-over'));
            this.classList.add('drag-over');
            dragOverEl = this;
        }
        function handleDrop(e) {
            e.preventDefault();
            if (!draggedEl || this === draggedEl) return;
            this.classList.remove('drag-over');
            // Вставляем draggedEl перед/после this
            const rect = this.getBoundingClientRect();
            const offset = e.clientY - rect.top;
            if (offset < rect.height / 2) {
                lessonList.insertBefore(draggedEl, this);
            } else {
                lessonList.insertBefore(draggedEl, this.nextSibling);
            }
            // Отправляем новый порядок на сервер
            const ids = Array.from(lessonList.querySelectorAll('li.lesson-li[data-lesson-id]'))
                .map(li => li.dataset.lessonId);
            fetch('/builder/lessons/reorder_in_category/', {
                method: 'POST',
                headers: { 'X-CSRFToken': (document.querySelector('[name=csrfmiddlewaretoken]')||{}).value || '', 'Content-Type': 'application/json' },
                body: JSON.stringify({ category_id: categoryId, ids })
            }).then(r => r.json()).then(data => {
                if (data.error) alert('Ошибка сортировки: ' + data.error);
            }).catch(() => alert('Ошибка сети при сортировке!'));
        }
        lessonList.querySelectorAll('li.lesson-li[data-lesson-id]').forEach(li => {
            li.setAttribute('draggable', 'true');
            li.addEventListener('dragstart', handleDragStart);
            li.addEventListener('dragend', handleDragEnd);
            li.addEventListener('dragover', handleDragOver);
            li.addEventListener('drop', handleDrop);
        });
    });
})();

// === Drag&Drop сортировка для категорий и подкатегорий ===
(function() {
    if (window.IS_READONLY) return;
    document.querySelectorAll('ul.category-list').forEach(catList => {
        // Отключаем dnd для словаря
        if (catList.classList.contains('dict-list')) return;
        // Отключаем dnd для блока без категории
        if (catList.closest('#uncategorized-block')) return;
        let draggedEl = null;
        let dragOverEl = null;
        // parent_id: если это подкатегории — id родителя, если корень — ''
        const parentBlock = catList.closest('.category-block');
        const parentId = parentBlock ? parentBlock.dataset.id : '';
        function handleDragStart(e) {
            draggedEl = this;
            this.classList.add('dragging');
            e.dataTransfer.effectAllowed = 'move';
        }
        function handleDragEnd(e) {
            this.classList.remove('dragging');
            draggedEl = null;
            dragOverEl = null;
            catList.querySelectorAll('.drag-over').forEach(el => el.classList.remove('drag-over'));
        }
        function handleDragOver(e) {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'move';
            if (this === draggedEl) return;
            catList.querySelectorAll('.drag-over').forEach(el => el.classList.remove('drag-over'));
            this.classList.add('drag-over');
            dragOverEl = this;
        }
        function handleDrop(e) {
            e.preventDefault();
            if (!draggedEl || this === draggedEl) return;
            // Проверяем, что оба элемента в одном списке
            if (draggedEl.parentNode !== catList || this.parentNode !== catList) return;
            this.classList.remove('drag-over');
            // Вставляем draggedEl перед/после this
            const rect = this.getBoundingClientRect();
            const offset = e.clientY - rect.top;
            if (offset < rect.height / 2) {
                catList.insertBefore(draggedEl, this);
            } else {
                catList.insertBefore(draggedEl, this.nextSibling);
            }
            // --- Обновляем порядковые номера ---
            function updateSubcategoryOrderNumbers(subUl) {
                const items = subUl.querySelectorAll('.category-header .category-title');
                items.forEach((title, idx) => {
                    title.textContent = title.textContent.replace(/^\d+\.\s*/, '');
                    title.textContent = (idx + 1) + '. ' + title.textContent;
                });
            }
            updateSubcategoryOrderNumbers(catList);
            // ---
            // Отправляем новый порядок на сервер
            const ids = Array.from(catList.querySelectorAll('li.category-block[data-id]'))
                .map(li => li.dataset.id);
            fetch('/builder/categories/reorder/', {
                method: 'POST',
                headers: { 'X-CSRFToken': (document.querySelector('[name=csrfmiddlewaretoken]')||{}).value || '', 'Content-Type': 'application/json' },
                body: JSON.stringify({ parent_id: parentId, ids })
            }).then(r => r.json()).then(data => {
                if (data.error) alert('Ошибка сортировки: ' + data.error);
            }).catch(() => alert('Ошибка сети при сортировке!'));
        }
        catList.querySelectorAll('li.category-block[data-id]').forEach(li => {
            li.setAttribute('draggable', 'true');
            li.addEventListener('dragstart', handleDragStart);
            li.addEventListener('dragend', handleDragEnd);
            li.addEventListener('dragover', handleDragOver);
            li.addEventListener('drop', handleDrop);
        });
    });
})();

// === Показать все зеркала ===
document.getElementById('show-all-mirrors-menu-item').addEventListener('click', function() {
    if (!contextTarget) return;
    let lessonId = null;
    if (contextTarget.dataset && contextTarget.dataset.id && contextTarget.dataset.id.startsWith('uncat-')) {
        lessonId = contextTarget.dataset.id.replace('uncat-', '');
    } else if (contextTarget.classList.contains('lesson-li')) {
        lessonId = contextTarget.dataset.lessonId;
    } else if (contextTarget.querySelector('.lesson-link')) {
        const radio = contextTarget.querySelector('.lesson-select');
        if (radio) lessonId = radio.value;
    }
    if (!lessonId) return;

    // Скрываем все категории и все уроки
    document.querySelectorAll('.category-block').forEach(el => el.style.display = 'none');
    document.querySelectorAll('.lesson-list li').forEach(el => el.style.display = 'none');

    // Находим все экземпляры этого урока (оригинал и зеркала)
    const allInstances = document.querySelectorAll(`.lesson-li[data-lesson-id='${lessonId}'], .category-block[data-id='uncat-${lessonId}']`);
    allInstances.forEach(li => {
        li.style.display = '';
        li.classList.add('selected');
        let parent = li.parentElement;
        while (parent && !parent.classList.contains('category-list')) {
            if (parent.classList.contains('subcategory-list') || parent.classList.contains('lesson-list')) {
                parent.style.display = 'block';
            }
            if (parent.classList.contains('category-block')) {
                parent.style.display = '';
                const header = parent.querySelector('.category-header');
                if (header && !header.classList.contains('open')) {
                    header.classList.add('open');
                    const arrow = header.querySelector('.toggle-arrow');
                    if (arrow) arrow.innerHTML = '&#9660;';
                }
            }
            parent = parent.parentElement;
        }
    });
    // Скрываем контекстное меню
    document.getElementById('custom-context-menu').style.display = 'none';
    // Показываем пункт 'Скрыть', скрываем 'Показать все зеркала'
    document.getElementById('show-all-mirrors-menu-item').style.display = 'none';
    document.getElementById('hide-mirrors-menu-item').style.display = '';
    window._mirrorsFilterActive = true;
});

// === Скрыть (сбросить фильтр зеркал) ===
document.getElementById('hide-mirrors-menu-item').addEventListener('click', function() {
    // Показываем все категории и уроки
    document.querySelectorAll('.category-block').forEach(el => el.style.display = '');
    document.querySelectorAll('.lesson-list li').forEach(el => el.style.display = '');
    // Снимаем выделения
    document.querySelectorAll('.selected').forEach(el => el.classList.remove('selected'));
    // Скрываем пункт 'Скрыть', показываем 'Показать все зеркала' (если надо)
    document.getElementById('hide-mirrors-menu-item').style.display = 'none';
    document.getElementById('show-all-mirrors-menu-item').style.display = '';
    window._mirrorsFilterActive = false;
    document.getElementById('custom-context-menu').style.display = 'none';
});


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