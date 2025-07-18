

if (window._dictSectionData && document.getElementById('dict-hot-table')) {
    const container = document.getElementById('dict-hot-table');
    const hot = new Handsontable(container, {
        data: window._dictSectionData,
        colHeaders: ['№', 'Название', 'Сленг', 'Описание', 'Фото'],
        columns: [
            {data: 'order', type: 'numeric', width: 40, readOnly: true},
            {data: 'term', type: 'text'},
            {data: 'slang', type: 'text'},
            {data: 'definition', type: 'text'},
            {
                data: 'photo',
                renderer: function (instance, td, row, col, prop, value, cellProperties) {
                    if (!value) { td.innerHTML = ''; return td; }
                    td.innerHTML = `<a href="${value}" target="_blank" rel="noopener"><img src="${value}"></a>`;
                    return td;
                }
            }
        ],
        rowHeaders: true,
        stretchH: 'all',
        licenseKey: 'non-commercial-and-evaluation',
        contextMenu: true,
        manualRowMove: true,
        manualColumnMove: true,
        afterChange: function(changes, source) {
            // TODO: AJAX сохранение изменений
        }
    });
    // Сохраняем hot для дальнейшей работы
    window._dictHot = hot;
}

function initDictHotTable() {
    if (window._dictSectionData && document.getElementById('dict-hot-table') && window.Handsontable) {
        // Регистрируем русскую локализацию для Handsontable
        if (window.Handsontable.languages) {
            window.Handsontable.languages['ru-RU'] = {
                'contextMenu.items.insert_row_above': 'Вставить строку выше',
                'contextMenu.items.insert_row_below': 'Вставить строку ниже',
                'contextMenu.items.insert_column_left': 'Вставить столбец слева',
                'contextMenu.items.insert_column_right': 'Вставить столбец справа',
                'contextMenu.items.remove_row': 'Удалить строки',
                'contextMenu.items.remove_column': 'Удалить столбцы',
            };
        }
        const container = document.getElementById('dict-hot-table');
        const hot = new Handsontable(container, {
            data: window._dictSectionData,
            colHeaders: ['Название', 'Сленг', 'Описание', 'Фото'],
            columns: [
                {data: 'term', type: 'text', width: 160, className: 'ht-term-cell'},
                {data: 'slang', type: 'text', width: 190, className: 'ht-slang-cell'},
                {data: 'definition', type: 'text', width: 320, className: 'ht-definition-cell'},
                {
                    data: 'photo',
                    width: 180,
                    height: 80,
                    readOnly: true,
                    className: 'ht-photo-cell',
                    renderer: function (instance, td, row, col, prop, value, cellProperties) {
                        if (!value) { td.innerHTML = ''; return td; }
                        td.innerHTML = `<img src="${value}" alt="Фото" class="ht-photo-cell-img" onclick="openPhotoModal('${value}')">`;
                        return td;
                    }
                }
            ],
            rowHeaders: true,
            stretchH: 'all',
            licenseKey: 'non-commercial-and-evaluation',
            contextMenu: !window.IS_READONLY,
            manualRowMove: !window.IS_READONLY,
            manualColumnMove: !window.IS_READONLY,
            readOnly: window.IS_READONLY,
            autoWrapRow: true,
            autoWrapCol: true,
            height: 'auto',
            language: 'ru-RU',
            minSpareRows: 1,
            afterChange: function(changes, source) {
                if (source === 'loadData' || !changes || window.IS_READONLY) return;
                // Добавляем order = rowIndex+1 для каждой строки и фильтруем пустые строки
                const data = this.getSourceData()
                    .filter(row => row.term && row.term.trim() !== '') // убираем строки без названия
                    .map((row, idx) => ({
                        ...row, 
                        order: idx + 1,
                        definition: row.definition || '', // заполняем пустое definition пустой строкой
                        slang: row.slang || '' // заполняем пустое slang пустой строкой
                    }));
                fetch('/builder/dictionary/save_terms/', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': (document.querySelector('[name=csrfmiddlewaretoken]')||{}).value || '',
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        section_id: window._dictSectionId,
                        terms: data
                    })
                })
                .then(r => r.json())
                .then(resp => {
                    if (resp.error) alert('Ошибка сохранения: ' + resp.error);
                })
                .catch(() => alert('Ошибка сети при сохранении!'));
            },
            beforePaste: function(data, coords) {
                // Обработка вставки изображений
                if (coords && coords.length > 0) {
                    const row = coords[0].startRow;
                    const col = coords[0].startCol;
                    
                    // Если вставляем в столбец с фото (индекс 3)
                    if (col === 3) {
                        // Проверяем, есть ли изображения в буфере
                        if (navigator.clipboard && navigator.clipboard.read) {
                            navigator.clipboard.read().then(clipboardItems => {
                                for (let clipboardItem of clipboardItems) {
                                    for (let type of clipboardItem.types) {
                                        if (type.startsWith('image/')) {
                                            clipboardItem.getType(type).then(blob => {
                                                // Создаем URL для изображения
                                                const imageUrl = URL.createObjectURL(blob);
                                                // Вставляем URL в ячейку
                                                this.setDataAtRowProp(row, 'photo', imageUrl);
                                                // Сохраняем изменения
                                                this.render();
                                            });
                                            return;
                                        }
                                    }
                                }
                            }).catch(err => {
                                console.log('Ошибка чтения буфера обмена:', err);
                            });
                        }
                    }
                }
                return data;
            }
        });
        
        // Обработчик вставки изображений через Ctrl+V
        container.addEventListener('paste', function(e) {
            if (window.IS_READONLY) return;
            
            const items = e.clipboardData.items;
            for (let i = 0; i < items.length; i++) {
                if (items[i].type.startsWith('image/')) {
                    e.preventDefault();
                    const blob = items[i].getAsFile();
                    const imageUrl = URL.createObjectURL(blob);
                    
                    // Получаем текущую активную ячейку
                    const selected = hot.getSelected();
                    if (selected && selected.length > 0) {
                        const row = selected[0][0];
                        const col = selected[0][1];
                        
                        // Если выбрана ячейка в столбце с фото
                        if (col === 3) {
                            hot.setDataAtRowProp(row, 'photo', imageUrl);
                            hot.render();
                        }
                    }
                    break;
                }
            }
        });
        
        window._dictHot = hot;
    }
}

// Модальное окно для просмотра фото
function openPhotoModal(imageSrc) {
    // Создаем модальное окно
    const modal = document.createElement('div');
    modal.className = 'photo-modal-overlay';
    modal.innerHTML = `
        <div class="photo-modal">
            <div class="photo-modal-header">
                <button class="photo-modal-close" onclick="closePhotoModal()">&times;</button>
            </div>
            <div class="photo-modal-content">
                <img src="${imageSrc}" alt="Фото" class="photo-modal-image">
            </div>
        </div>
    `;
    
    // Добавляем обработчик клика по оверлею для закрытия
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            closePhotoModal();
        }
    });
    
    // Добавляем обработчик клавиши Escape
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closePhotoModal();
        }
    });
    
    document.body.appendChild(modal);
    
    // Показываем модальное окно с анимацией
    setTimeout(() => {
        modal.classList.add('show');
    }, 10);
}

function closePhotoModal() {
    const modal = document.querySelector('.photo-modal-overlay');
    if (modal) {
        modal.classList.remove('show');
        setTimeout(() => {
            modal.remove();
        }, 300);
    }
}