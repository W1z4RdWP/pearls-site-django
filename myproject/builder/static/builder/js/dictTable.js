
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
                    td.innerHTML = `<a href="${value}" target="_blank" rel="noopener"><img src="${value}" style="width:32px;height:32px;object-fit:cover;transition:.2s;cursor:pointer;"></a>`;
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
        const container = document.getElementById('dict-hot-table');
        const hot = new Handsontable(container, {
            data: window._dictSectionData,
            colHeaders: ['Название', 'Сленг', 'Описание', 'Фото'],
            columns: [
                {data: 'term', type: 'text', width: 160},
                {data: 'slang', type: 'text', width: 190},
                {data: 'definition', type: 'text', width: 320, className: 'ht-definition-cell'},
                {
                    data: 'photo',
                    readOnly: true,
                    renderer: function (instance, td, row, col, prop, value, cellProperties) {
                        td.innerHTML = value ? `<img src="${value}" style="width:32px;height:32px;object-fit:cover;transition:.2s;" onmouseover="this.style.transform='scale(3)';this.style.zIndex=10;this.style.position='relative'" onmouseout="this.style.transform='';this.style.zIndex='';this.style.position=''">` : '';
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
            // autoWrapRow: true,
            // autoWrapCol: true,
            height: 'auto',
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
            }
        });
        window._dictHot = hot;
    }
}

// Добавь в конец файла:
window._dictPhotoPopup = null;
function showDictPhotoPopup(e, img) {
    hideDictPhotoPopup();
    const popup = document.createElement('img');
    popup.src = img.src;
    popup.style.position = 'fixed';
    popup.style.left = (e.clientX + 20) + 'px';
    popup.style.top = (e.clientY - 20) + 'px';
    popup.style.width = '200px';
    popup.style.height = '200px';
    popup.style.objectFit = 'contain';
    popup.style.background = '#fff';
    popup.style.border = '2px solid #333';
    popup.style.boxShadow = '0 4px 24px #0008';
    popup.style.zIndex = 10000;
    popup.style.pointerEvents = 'none';
    popup.id = 'dict-photo-popup';
    document.body.appendChild(popup);
    window._dictPhotoPopup = popup;
}
function hideDictPhotoPopup() {
    if (window._dictPhotoPopup) {
        window._dictPhotoPopup.remove();
        window._dictPhotoPopup = null;
    }
}