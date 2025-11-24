// API endpoints (определяются в шаблоне ipr_form.html)
// searchUsersUrl, getUsersByIdsUrl должны быть определены в шаблоне

// Элементы DOM для выбора пользователя
const modal = document.getElementById('userModal');
const userSelectField = document.getElementById('userSelectField');
const userModalClose = document.getElementById('userModalClose');
const userSearchInput = document.getElementById('userSearchInput');
const userList = document.getElementById('userList');
const userDisplayName = document.getElementById('userDisplayName');
const userInput = document.getElementById(userInputId);

// ========== ФУНКЦИИ ДЛЯ ВЫБОРА ПОЛЬЗОВАТЕЛЯ ==========

// Открытие модального окна для поля "Пользователь"
if (userSelectField) {
    userSelectField.addEventListener('click', function() {
        modal.style.display = 'block';
        loadUsers('');
        userSearchInput.focus();
    });
}

// Закрытие модального окна
if (userModalClose) {
    userModalClose.addEventListener('click', function() {
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
// Загрузка всех пользователей при фокусе на поле поиска
if (userSearchInput) {
    userSearchInput.addEventListener('focus', function() {
        // Если поле пустое, загружаем всех пользователей
        if (this.value.trim().length === 0) {
            loadUsers('');
        }
    });

    userSearchInput.addEventListener('input', function() {
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
}

// Загрузка списка пользователей
function loadUsers(query) {
    if (!userList) return;
    
    userList.innerHTML = '<div class="user-list-loading">Загрузка...</div>';
    
    // Формируем URL с параметрами
    let url = searchUsersUrl + '?q=' + encodeURIComponent(query);
    
    // Для формы создания ИПР исключаем пользователей с существующими ИПР
    // isCreatePage определяется в шаблоне
    if (typeof isCreatePage !== 'undefined' && isCreatePage) {
        url += '&exclude_existing_ipr=true';
    }
    
    fetch(url)
        .then(response => response.json())
        .then(data => {
            displayUsers(data.users);
        })
        .catch(error => {
            userList.innerHTML = '<div class="user-list-error">Ошибка загрузки данных</div>';
        });
}

// Отображение списка пользователей
function displayUsers(users) {
    if (!userList) return;
    
    if (users.length === 0) {
        userList.innerHTML = '<div class="user-list-empty">Пользователи не найдены</div>';
        return;
    }
    
    let html = '';
    users.forEach(function(user) {
        html += `
            <div class="user-list-item" data-user-id="${user.id}" data-user-name="${user.full_name}">
                <div class="user-list-item-name">${user.full_name}${user.role ? ' (' + user.role + ')' : ''}</div>
            </div>
        `;
    });
    
    userList.innerHTML = html;
    
    // Добавляем обработчики клика на каждого пользователя
    const userItems = userList.querySelectorAll('.user-list-item');
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
    if (userInput) {
        userInput.value = userId;
    }
    if (userDisplayName) {
        userDisplayName.textContent = userName;
        userDisplayName.classList.remove('user-display-placeholder');
    }
    modal.style.display = 'none';
}

// Инициализация поля пользователя при загрузке страницы
function initializeUserField() {
    // Проверяем, что элементы существуют
    if (!userInput || !userDisplayName) {
        return;
    }
    
    // Проверяем, есть ли значение в скрытом поле
    const userId = userInput.value;
    
    // Проверяем текст, который уже отображается из шаблона
    const templateValue = userDisplayName.textContent.trim();
    
    if (userId) {
        // Если есть значение в скрытом поле, но текст placeholder - загружаем информацию
        if (templateValue === 'Выберите пользователя...' || !templateValue) {
            // Используем api_get_users_by_ids для загрузки конкретного пользователя по ID
            const url = getUsersByIdsUrl + '?ids=' + encodeURIComponent(userId);
            fetch(url)
                .then(response => response.json())
                .then(data => {
                    const user = data.users.find(u => u.id === parseInt(userId));
                    if (user) {
                        userDisplayName.textContent = user.full_name;
                        userDisplayName.classList.remove('user-display-placeholder');
                    }
                })
                .catch(error => {
                    console.error('Ошибка загрузки пользователя:', error);
                });
        } else {
            // Если текст уже отображается из шаблона, просто убираем класс placeholder
            userDisplayName.classList.remove('user-display-placeholder');
        }
    } else {
        // Если пользователь не выбран, проверяем текст из шаблона
        if (templateValue && templateValue !== 'Выберите пользователя...') {
            // Если в шаблоне есть значение, но нет в скрытом поле - это странно, но оставляем как есть
            userDisplayName.classList.remove('user-display-placeholder');
        } else {
            // Добавляем класс placeholder
            userDisplayName.classList.add('user-display-placeholder');
        }
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    // Инициализация поля при загрузке страницы редактирования
    initializeUserField();
    
    // Устанавливаем курсор pointer для поля выбора пользователя
    if (userSelectField) {
        userSelectField.style.cursor = 'pointer';
    }
});

