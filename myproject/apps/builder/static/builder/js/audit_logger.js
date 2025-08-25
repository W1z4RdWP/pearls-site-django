/**
 * Клиентская часть для работы с audit логами
 */

class AuditLogger {
    constructor(csrfToken) {
        this.csrfToken = csrfToken;
        this.baseUrl = '/builder/api/audit/';
    }

    /**
     * Получить историю изменений объекта
     */
    async getObjectHistory(modelName, objectId, options = {}) {
        const params = new URLSearchParams({
            model_name: modelName,
            object_id: objectId,
            limit: options.limit || 50,
            offset: options.offset || 0
        });

        try {
            const response = await fetch(`${this.baseUrl}history/?${params}`, {
                method: 'GET',
                headers: {
                    'X-CSRFToken': this.csrfToken,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Ошибка получения истории:', error);
            throw error;
        }
    }

    /**
     * Поиск в audit логах
     */
    async searchAuditLogs(filters = {}) {
        const params = new URLSearchParams();
        
        if (filters.userId) params.append('user_id', filters.userId);
        if (filters.action) params.append('action', filters.action);
        if (filters.modelName) params.append('model_name', filters.modelName);
        if (filters.dateFrom) params.append('date_from', filters.dateFrom);
        if (filters.dateTo) params.append('date_to', filters.dateTo);
        if (filters.search) params.append('search', filters.search);
        if (filters.limit) params.append('limit', filters.limit);
        if (filters.offset) params.append('offset', filters.offset);

        try {
            const response = await fetch(`${this.baseUrl}search/?${params}`, {
                method: 'GET',
                headers: {
                    'X-CSRFToken': this.csrfToken,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Ошибка поиска в логах:', error);
            throw error;
        }
    }

    /**
     * Отобразить историю объекта в модальном окне
     */
    async showObjectHistoryModal(modelName, objectId, objectName) {
        try {
            const data = await this.getObjectHistory(modelName, objectId);
            this.renderHistoryModal(data, objectName);
        } catch (error) {
            alert('Ошибка загрузки истории: ' + error.message);
        }
    }

    /**
     * Создать HTML для модального окна с историей
     */
    renderHistoryModal(data, objectName) {
        const modalHtml = `
            <div class="modal fade" id="auditHistoryModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">История изменений: ${objectName}</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="table-responsive">
                                <table class="table table-sm">
                                    <thead>
                                        <tr>
                                            <th>Время</th>
                                            <th>Пользователь</th>
                                            <th>Действие</th>
                                            <th>Изменения</th>
                                            <th>Комментарий</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${this.renderHistoryRows(data.history)}
                                    </tbody>
                                </table>
                            </div>
                            ${data.has_more ? '<p class="text-muted">Показаны последние ' + data.history.length + ' записей из ' + data.total_count + '</p>' : ''}
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Закрыть</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Удаляем предыдущую модалку если есть
        const existingModal = document.getElementById('auditHistoryModal');
        if (existingModal) {
            existingModal.remove();
        }

        // Добавляем новую модалку
        document.body.insertAdjacentHTML('beforeend', modalHtml);

        // Показываем модалку
        const modal = new bootstrap.Modal(document.getElementById('auditHistoryModal'));
        modal.show();
    }

    /**
     * Создать HTML строки для таблицы истории
     */
    renderHistoryRows(history) {
        return history.map(item => {
            const date = new Date(item.timestamp);
            const formattedDate = date.toLocaleString('ru-RU');
            
            const actionClass = this.getActionClass(item.action_code);
            const changesSummary = item.changes_summary || '-';
            
            return `
                <tr>
                    <td><small>${formattedDate}</small></td>
                    <td><small>${item.user}</small></td>
                    <td><span class="badge ${actionClass}">${item.action}</span></td>
                    <td><small title="${changesSummary}">${this.truncateText(changesSummary, 50)}</small></td>
                    <td><small>${item.comment || '-'}</small></td>
                </tr>
            `;
        }).join('');
    }

    /**
     * Получить CSS класс для типа действия
     */
    getActionClass(actionCode) {
        const classes = {
            'create': 'bg-success',
            'update': 'bg-primary', 
            'delete': 'bg-danger',
            'copy': 'bg-info',
            'move': 'bg-warning text-dark',
            'mirror': 'bg-secondary',
            'reorder': 'bg-light text-dark',
            'actualize': 'bg-info'
        };
        return classes[actionCode] || 'bg-secondary';
    }

    /**
     * Обрезать текст до указанной длины
     */
    truncateText(text, maxLength) {
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    }

    /**
     * Добавить кнопку "История" к элементу
     */
    addHistoryButton(element, modelName, objectId, objectName) {
        const button = document.createElement('button');
        button.className = 'btn btn-sm btn-outline-secondary ms-1';
        button.innerHTML = '<i class="fas fa-history"></i> История';
        button.title = 'Показать историю изменений';
        
        button.addEventListener('click', (e) => {
            e.preventDefault();
            this.showObjectHistoryModal(modelName, objectId, objectName);
        });

        element.appendChild(button);
        return button;
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    // Получаем CSRF токен
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
                     document.querySelector('meta[name=csrf-token]')?.content;
    
    if (csrfToken) {
        window.auditLogger = new AuditLogger(csrfToken);
        
        // Автоматически добавляем кнопки истории к элементам с data-audit атрибутами
        document.querySelectorAll('[data-audit-model][data-audit-id][data-audit-name]').forEach(element => {
            const modelName = element.dataset.auditModel;
            const objectId = element.dataset.auditId;
            const objectName = element.dataset.auditName;
            
            window.auditLogger.addHistoryButton(element, modelName, objectId, objectName);
        });
    }
});

// Пример использования в HTML:
// <div data-audit-model="lesson" data-audit-id="123" data-audit-name="Урок по безопасности">
//     Содержимое урока
//     <!-- Кнопка истории будет добавлена автоматически -->
// </div>
