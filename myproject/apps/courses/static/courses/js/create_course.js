// Сохранение состояния чекбоксов при ошибках валидации
document.addEventListener('DOMContentLoaded', function() {
    const checkboxes = document.querySelectorAll('input[name="allowed_groups"]');
    
    // Сохранение состояния при изменении
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const checkedGroups = Array.from(checkboxes)
                .filter(cb => cb.checked)
                .map(cb => cb.value);
            localStorage.setItem('course_form_groups', JSON.stringify(checkedGroups));
        });
    });
    
    // Очистка localStorage при успешной отправке
    const form = document.querySelector('.user-form');
    form.addEventListener('submit', function() {
        setTimeout(() => {
            localStorage.removeItem('course_form_groups');
        }, 100);
    });
});




// Элементы DOM для выбора пользователя
const modal = document.getElementById('userModal');
const userSelectField = document.getElementById('userSelectField');
const userModalClose = document.getElementById('userModalClose');
const userSearchInput = document.getElementById('userSearchInput');
const userList = document.getElementById('userList');
const userDisplayName = document.getElementById('userDisplayName');
const userInput = document.getElementById(userInputId);

// Открытие модального окна
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
if (userSearchInput) {
    userSearchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        const query = this.value;
        searchTimeout = setTimeout(function() {
            loadUsers(query);
        }, 300);
    });
}

// Загрузка списка пользователей
function loadUsers(query) {
    if (!userList) return;
    
    userList.innerHTML = '<div class="user-list-loading">Загрузка...</div>';
    
    const url = searchUsersUrl + '?q=' + encodeURIComponent(query);
    
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
                <div class="user-list-item-name">${user.full_name}</div>
                <div class="user-list-item-username">@${user.username}</div>
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
    if (modal) {
        modal.style.display = 'none';
    }
}

// Инициализация поля пользователя при загрузке страницы
function initializeUserField() {
    if (!userInput || !userDisplayName) {
        return;
    }
    
    const userId = userInput.value;
    const templateValue = userDisplayName.textContent.trim();
    
    if (userId) {
        if (templateValue === 'Выберите пользователя...' || !templateValue) {
            fetch(searchUsersUrl + '?q=')
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
            userDisplayName.classList.remove('user-display-placeholder');
        }
    } else {
        if (templateValue && templateValue !== 'Выберите пользователя...') {
            userDisplayName.classList.remove('user-display-placeholder');
        } else {
            userDisplayName.classList.add('user-display-placeholder');
        }
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    initializeUserField();
});