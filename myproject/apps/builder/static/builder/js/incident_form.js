// API endpoints (определяются в шаблоне incident_form.html)
// searchUsersUrl, getGroupsUrl, getGroupUsersUrlTemplate должны быть определены в шаблоне
const getGroupUsersUrl = getGroupUsersUrlTemplate.replace('/0/', '/{id}/');

// Элементы DOM для выбора пользователя (кто зафиксировал)
const modal = document.getElementById('userModal');
const userSelectField = document.getElementById('userSelectField');
const userModalClose = document.getElementById('userModalClose');
const userSearchInput = document.getElementById('userSearchInput');
const userList = document.getElementById('userList');
const userDisplayName = document.getElementById('userDisplayName');
const userInput = document.getElementById(userInputId);

// Элементы DOM для выбора назначенных
const assignedModal = document.getElementById('assignedModal');
const assignedSelectField = document.getElementById('assignedSelectField');
const assignedModalClose = document.getElementById('assignedModalClose');
const assignedSearchInput = document.getElementById('assignedSearchInput');
const searchResultsDropdown = document.getElementById('searchResultsDropdown');
const groupList = document.getElementById('groupList');
const selectedUsersList = document.getElementById('selectedUsersList');
const confirmAssignedBtn = document.getElementById('confirmAssignedBtn');
const cancelAssignedBtn = document.getElementById('cancelAssignedBtn');
const assignedCount = document.getElementById('assignedCount');

// Хранилище выбранных назначенных пользователей
let selectedAssignedUsers = new Map(); // userId -> {id, full_name, username}

// Хранилище нарушителей (отмеченные галочкой)
let violatorsSet = new Set(); // Set of userId

// Кэш последних результатов поиска
let lastSearchResults = [];

// ========== ФУНКЦИИ ДЛЯ ВЫБОРА ПОЛЬЗОВАТЕЛЯ (КТО ЗАФИКСИРОВАЛ) ==========

// Открытие модального окна
userSelectField.addEventListener('click', function() {
    modal.style.display = 'block';
    loadUsers('');
    userSearchInput.focus();
});

// Закрытие модального окна
userModalClose.addEventListener('click', function() {
    modal.style.display = 'none';
});

window.addEventListener('click', function(event) {
    if (event.target == modal) {
        modal.style.display = 'none';
    }
    if (event.target == assignedModal) {
        assignedModal.style.display = 'none';
        hideSearchResults();
    }
});

// Поиск пользователей с задержкой
let searchTimeout;
userSearchInput.addEventListener('input', function() {
    clearTimeout(searchTimeout);
    const query = this.value;
    searchTimeout = setTimeout(function() {
        loadUsers(query);
    }, 300);
});

// Загрузка списка пользователей
function loadUsers(query) {
    userList.innerHTML = '<div class="user-list-loading">Загрузка...</div>';
    
    const url = searchUsersUrl + '?q=' + encodeURIComponent(query);
    
    fetch(url)
        .then(response => response.json())
        .then(data => {
            displayUsers(data.users);
        })
        .catch(error => {
            console.error('Ошибка загрузки пользователей:', error);
            userList.innerHTML = '<div class="user-list-error">Ошибка загрузки данных</div>';
        });
}

// Отображение списка пользователей
function displayUsers(users) {
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
    userInput.value = userId;
    userDisplayName.textContent = userName;
    userDisplayName.classList.remove('user-display-placeholder');
    modal.style.display = 'none';
}

// Если пользователь не выбран, добавляем класс placeholder
if (!userInput.value) {
    userDisplayName.classList.add('user-display-placeholder');
}

// ========== ФУНКЦИИ ДЛЯ ВЫБОРА НАЗНАЧЕННЫХ ==========

// Открытие модального окна выбора назначенных
assignedSelectField.addEventListener('click', function() {
    assignedModal.style.display = 'block';
    loadGroups();
    loadInitialAssignedUsers();
});

// Закрытие модального окна
assignedModalClose.addEventListener('click', function() {
    assignedModal.style.display = 'none';
    hideSearchResults();
});

cancelAssignedBtn.addEventListener('click', function() {
    assignedModal.style.display = 'none';
    hideSearchResults();
});

// Применение выбора
confirmAssignedBtn.addEventListener('click', function() {
    applyAssignedSelection();
    assignedModal.style.display = 'none';
    hideSearchResults();
});

// Загрузка списка групп
function loadGroups() {
    groupList.innerHTML = '<div class="group-list-loading">Загрузка групп...</div>';
    
    fetch(getGroupsUrl)
        .then(response => response.json())
        .then(data => {
            displayGroups(data.groups);
        })
        .catch(error => {
            console.error('Ошибка загрузки групп:', error);
            groupList.innerHTML = '<div class="group-list-error">Ошибка загрузки групп</div>';
        });
}

// Отображение списка групп
function displayGroups(groups) {
    if (groups.length === 0) {
        groupList.innerHTML = '<div class="group-list-empty">Группы не найдены</div>';
        return;
    }
    
    let html = '';
    groups.forEach(function(group) {
        html += `
            <div class="group-item" data-group-id="${group.id}">
                <div class="group-item-name">${group.name}</div>
                <div class="group-item-count">${group.user_count} пользователей</div>
            </div>
        `;
    });
    
    groupList.innerHTML = html;
    
    // Добавляем обработчики клика на каждую группу
    const groupItems = groupList.querySelectorAll('.group-item');
    groupItems.forEach(function(item) {
        item.addEventListener('click', function() {
            const groupId = this.getAttribute('data-group-id');
            addGroupUsers(groupId);
        });
    });
}

// Добавление всех пользователей группы
function addGroupUsers(groupId) {
    const url = getGroupUsersUrl.replace('{id}', groupId);
    
    fetch(url)
        .then(response => response.json())
        .then(data => {
            data.users.forEach(function(user) {
                if (!selectedAssignedUsers.has(user.id)) {
                    selectedAssignedUsers.set(user.id, user);
                }
            });
            displaySelectedUsers();
        })
        .catch(error => {
            console.error('Ошибка загрузки пользователей группы:', error);
        });
}

// Поиск пользователей для добавления в назначенные
let assignedSearchTimeout;
assignedSearchInput.addEventListener('input', function() {
    clearTimeout(assignedSearchTimeout);
    const query = this.value.trim();
    
    if (query.length === 0) {
        hideSearchResults();
        return;
    }
    
    assignedSearchTimeout = setTimeout(function() {
        searchUsers(query);
    }, 300);
});

// Обработка клавиши Escape для закрытия выпадающего списка
assignedSearchInput.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        hideSearchResults();
        this.blur();
    }
});

// Закрытие выпадающего списка при клике вне его
document.addEventListener('click', function(event) {
    if (!assignedSearchInput.contains(event.target) && !searchResultsDropdown.contains(event.target)) {
        hideSearchResults();
    }
});

// Поиск пользователей и отображение результатов
function searchUsers(query) {
    searchResultsDropdown.innerHTML = '<div class="search-results-loading">Поиск...</div>';
    searchResultsDropdown.style.display = 'block';
    
    const url = searchUsersUrl + '?q=' + encodeURIComponent(query);
    
    fetch(url)
        .then(response => response.json())
        .then(data => {
            lastSearchResults = data.users; // Сохраняем результаты
            displaySearchResults(data.users);
        })
        .catch(error => {
            console.error('Ошибка поиска пользователей:', error);
            searchResultsDropdown.innerHTML = '<div class="search-results-empty">Ошибка поиска</div>';
        });
}

// Отображение результатов поиска
function displaySearchResults(users) {
    if (users.length === 0) {
        searchResultsDropdown.innerHTML = '<div class="search-results-empty">Пользователи не найдены</div>';
        return;
    }
    
    let html = '';
    users.forEach(function(user) {
        // Пропускаем уже выбранных пользователей
        if (selectedAssignedUsers.has(user.id)) {
            return;
        }
        
        html += `
            <div class="search-result-item" data-user-id="${user.id}">
                <div class="search-result-name">${user.full_name}</div>
                <div class="search-result-username">@${user.username}</div>
            </div>
        `;
    });
    
    if (html === '') {
        searchResultsDropdown.innerHTML = '<div class="search-results-empty">Все найденные пользователи уже выбраны</div>';
        return;
    }
    
    searchResultsDropdown.innerHTML = html;
    
    // Добавляем обработчики клика на результаты
    const resultItems = searchResultsDropdown.querySelectorAll('.search-result-item');
    resultItems.forEach(function(item) {
        item.addEventListener('click', function() {
            const userId = parseInt(this.getAttribute('data-user-id'));
            addUserFromSearch(userId);
        });
    });
}

// Добавление пользователя из результатов поиска
function addUserFromSearch(userId) {
    // Находим пользователя в сохраненных результатах поиска
    const user = lastSearchResults.find(u => u.id === userId);
    
    if (user && !selectedAssignedUsers.has(userId)) {
        selectedAssignedUsers.set(userId, user);
        displaySelectedUsers();
        assignedSearchInput.value = '';
        hideSearchResults();
    }
}

// Скрытие выпадающего списка результатов
function hideSearchResults() {
    searchResultsDropdown.style.display = 'none';
    searchResultsDropdown.innerHTML = '';
}

// Отображение выбранных пользователей
function displaySelectedUsers() {
    if (selectedAssignedUsers.size === 0) {
        selectedUsersList.innerHTML = '<div class="selected-users-empty">Пользователи не выбраны</div>';
        return;
    }
    
    let html = '';
    selectedAssignedUsers.forEach(function(user, userId) {
        const isViolator = violatorsSet.has(userId);
        html += `
            <div class="selected-user-item" data-user-id="${userId}">
                <div class="selected-user-info">
                    <div class="selected-user-name">${user.full_name}</div>
                </div>
                <div class="selected-user-actions">
                    <label class="selected-user-checkbox" title="Нарушитель">
                        <input type="checkbox" data-user-id="${userId}" ${isViolator ? 'checked' : ''}>
                        <span class="checkbox-label">Нарушитель</span>
                    </label>
                    <span class="selected-user-remove" data-user-id="${userId}" title="Удалить">&times;</span>
                </div>
            </div>
        `;
    });
    
    selectedUsersList.innerHTML = html;
    
    // Добавляем обработчики для галочек
    const checkboxes = selectedUsersList.querySelectorAll('input[type="checkbox"]');
    checkboxes.forEach(function(checkbox) {
        checkbox.addEventListener('change', function() {
            const userId = parseInt(this.getAttribute('data-user-id'));
            if (this.checked) {
                violatorsSet.add(userId);
            } else {
                violatorsSet.delete(userId);
            }
        });
    });
    
    // Добавляем обработчики для удаления пользователей
    const removeButtons = selectedUsersList.querySelectorAll('.selected-user-remove');
    removeButtons.forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            const userId = parseInt(this.getAttribute('data-user-id'));
            selectedAssignedUsers.delete(userId);
            violatorsSet.delete(userId); // Также удаляем из нарушителей
            displaySelectedUsers();
        });
    });
}

// Загрузка изначально выбранных пользователей (при редактировании)
function loadInitialAssignedUsers() {
    const assignedInputs = document.querySelectorAll('input[name="assigned_to"]');
    const violatorInputs = document.querySelectorAll('input[name="violators"]');
    
    // Собираем ID назначенных пользователей
    const assignedUserIds = [];
    assignedInputs.forEach(function(input) {
        if (input.value) {
            assignedUserIds.push(parseInt(input.value));
        }
    });
    
    // Собираем ID нарушителей
    const violatorUserIds = [];
    violatorInputs.forEach(function(input) {
        if (input.value) {
            violatorUserIds.push(parseInt(input.value));
        }
    });
    
    if (assignedUserIds.length === 0) {
        return;
    }
    
    // Загружаем информацию о пользователях
    fetch(searchUsersUrl + '?q=')
        .then(response => response.json())
        .then(data => {
            assignedUserIds.forEach(function(userId) {
                const user = data.users.find(u => u.id === userId);
                if (user) {
                    selectedAssignedUsers.set(userId, user);
                }
            });
            
            // Добавляем нарушителей в Set
            violatorUserIds.forEach(function(userId) {
                violatorsSet.add(userId);
            });
            
            displaySelectedUsers();
        })
        .catch(error => {
            console.error('Ошибка загрузки пользователей:', error);
        });
}

// Применение выбора назначенных
function applyAssignedSelection() {
    updateHiddenFields();
    // Обновляем счетчик
    assignedCount.textContent = selectedAssignedUsers.size;
}

// Функция для обновления скрытых полей в форме
function updateHiddenFields() {
    const form = document.querySelector('form');
    if (!form) {
        console.error('Форма не найдена');
        return;
    }
    
    // Контейнер для assigned_to (если есть)
    const assignedToContainer = document.getElementById('assignedToContainer');
    const container = assignedToContainer || form;
    
    // Удаляем все существующие скрытые поля для assigned_to
    const oldAssignedInputs = form.querySelectorAll('input[name="assigned_to"]');
    oldAssignedInputs.forEach(function(input) {
        input.remove();
    });
    
    // Удаляем все существующие скрытые поля для violators
    const oldViolatorInputs = form.querySelectorAll('input[name="violators"]');
    oldViolatorInputs.forEach(function(input) {
        input.remove();
    });
    
    // Добавляем скрытые поля для назначенных пользователей
    // В Map.forEach первый параметр - значение, второй - ключ
    selectedAssignedUsers.forEach(function(user, userId) {
        const hiddenInput = document.createElement('input');
        hiddenInput.type = 'hidden';
        hiddenInput.name = 'assigned_to';
        hiddenInput.value = String(userId); // Убеждаемся, что значение - строка
        container.appendChild(hiddenInput);
    });
    
    // Добавляем скрытые поля для нарушителей
    violatorsSet.forEach(function(userId) {
        const hiddenInput = document.createElement('input');
        hiddenInput.type = 'hidden';
        hiddenInput.name = 'violators';
        hiddenInput.value = String(userId); // Убеждаемся, что значение - строка
        container.appendChild(hiddenInput);
    });
    
    // Отладочная информация
    console.log('Обновлены скрытые поля:', {
        assigned_to: Array.from(selectedAssignedUsers.keys()),
        violators: Array.from(violatorsSet),
        total_assigned_inputs: form.querySelectorAll('input[name="assigned_to"]').length,
        total_violator_inputs: form.querySelectorAll('input[name="violators"]').length
    });
}

// Обработчик отправки формы - гарантируем, что скрытые поля обновлены
document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('form');
    if (form) {
        form.addEventListener('submit', function(e) {
            // Обновляем скрытые поля перед отправкой формы
            updateHiddenFields();
        });
    }
    
    // Инициализация счетчика при загрузке страницы
    const hiddenInputs = document.querySelectorAll('input[name="assigned_to"]');
    assignedCount.textContent = hiddenInputs.length;
});