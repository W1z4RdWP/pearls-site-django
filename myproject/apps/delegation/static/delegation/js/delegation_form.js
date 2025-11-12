// API endpoints (определяются в шаблоне delegation_create.html)
// searchUsersUrl, getUsersByIdsUrl должны быть определены в шаблоне

// Элементы DOM для выбора принимающего (delegate)
const modal = document.getElementById('delegateModal');
const delegateSelectField = document.getElementById('delegateSelectField');
const delegateModalClose = document.getElementById('delegateModalClose');
const delegateSearchInput = document.getElementById('delegateSearchInput');
const delegateList = document.getElementById('delegateList');
const delegateDisplayName = document.getElementById('delegateDisplayName');
const delegateInput = document.getElementById(delegateInputId);

// Открытие модального окна для поля "Принимающий"
if (delegateSelectField) {
    delegateSelectField.addEventListener('click', function() {
        modal.style.display = 'block';
        loadUsers('');
        delegateSearchInput.focus();
    });
}

// Закрытие модального окна
if (delegateModalClose) {
    delegateModalClose.addEventListener('click', function() {
        modal.style.display = 'none';
    });
}

window.addEventListener('click', function(event) {
    if (event.target == modal) {
        modal.style.display = 'none';
    }
});

// Поиск пользователей с задержкой
let searchTimeout;

delegateSearchInput.addEventListener('input', function() {
    clearTimeout(searchTimeout);
    const query = this.value;
    // При пустом запросе показываем всех пользователей
    if (query.trim().length === 0) {
        loadUsers('');
        return;
    }
    searchTimeout = setTimeout(function() {
        loadUsers(query);
    }, 300);
});

// Загрузка списка пользователей
function loadUsers(query) {
    delegateList.innerHTML = '<div class="user-list-loading">Загрузка...</div>';
    
    // Формируем URL с параметрами
    let url = searchUsersUrl + '?q=' + encodeURIComponent(query);
    
    fetch(url)
        .then(response => response.json())
        .then(data => {
            displayUsers(data.users);
        })
        .catch(error => {
            console.error('Ошибка загрузки пользователей:', error);
            delegateList.innerHTML = '<div class="user-list-error">Ошибка загрузки данных</div>';
        });
}

// Отображение списка пользователей
function displayUsers(users) {
    if (users.length === 0) {
        delegateList.innerHTML = '<div class="user-list-empty">Пользователи не найдены</div>';
        return;
    }
    
    let html = '';
    users.forEach(function(user) {
        html += `
            <div class="user-list-item" data-user-id="${user.id}" data-user-name="${user.full_name}">
                <div class="user-list-item-name">${user.full_name}</div>
                <div class="user-list-item-username">@${user.username}</div>
            </div>
        `;
    });
    
    delegateList.innerHTML = html;
    
    // Добавляем обработчики клика на каждого пользователя
    const userItems = delegateList.querySelectorAll('.user-list-item');
    userItems.forEach(function(item) {
        item.addEventListener('click', function() {
            const userId = this.getAttribute('data-user-id');
            const userName = this.getAttribute('data-user-name');
            selectUser(userId, userName);
        });
    });
}

// Выбор пользователя
function selectUser(userId, userName) {
    // Обновляем поле "Принимающий"
    if (delegateInput) {
        delegateInput.value = userId;
    }
    if (delegateDisplayName) {
        delegateDisplayName.textContent = userName;
        delegateDisplayName.classList.remove('user-display-placeholder');
    }
    modal.style.display = 'none';
}

// Инициализация поля пользователя при загрузке страницы
function initializeDelegateField() {
    // Проверяем, что элементы существуют
    if (!delegateInput || !delegateDisplayName) {
        return;
    }
    
    // Проверяем, есть ли значение в скрытом поле
    const userId = delegateInput.value;
    
    // Проверяем текст, который уже отображается из шаблона
    const templateValue = delegateDisplayName.textContent.trim();
    
    if (userId) {
        // Если есть значение в скрытом поле, но текст placeholder - загружаем информацию
        if (templateValue === 'Выберите пользователя...' || !templateValue) {
            fetch(getUsersByIdsUrl + '?ids=' + userId)
                .then(response => response.json())
                .then(data => {
                    if (data.users && data.users.length > 0) {
                        const user = data.users[0];
                        delegateDisplayName.textContent = user.full_name;
                        delegateDisplayName.classList.remove('user-display-placeholder');
                    }
                })
                .catch(error => {
                    console.error('Ошибка загрузки пользователя:', error);
                });
        } else {
            // Если текст уже отображается из шаблона, просто убираем класс placeholder
            delegateDisplayName.classList.remove('user-display-placeholder');
        }
    } else {
        // Если пользователь не выбран, проверяем текст из шаблона
        if (templateValue && templateValue !== 'Выберите пользователя...') {
            // Если в шаблоне есть значение, но нет в скрытом поле - это странно, но оставляем как есть
            delegateDisplayName.classList.remove('user-display-placeholder');
        } else {
            // Добавляем класс placeholder
            delegateDisplayName.classList.add('user-display-placeholder');
        }
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    initializeDelegateField();
});

