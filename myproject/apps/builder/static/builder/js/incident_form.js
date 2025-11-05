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

// Хранилище ответственных пользователей (отмеченные галочкой)
let responsibleUsers = new Set(); // Set of userId

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
        const isResponsible = responsibleUsers.has(userId);
        html += `
            <div class="selected-user-item" data-user-id="${userId}">
                <div class="selected-user-info">
                    <div class="selected-user-name">${user.full_name}</div>
                </div>
                <div class="selected-user-actions">
                    <label class="selected-user-checkbox" title="Ответственный">
                        <input type="checkbox" data-user-id="${userId}" ${isResponsible ? 'checked' : ''}>
                        <span class="checkbox-label">Ответственный</span>
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
                responsibleUsers.add(userId);
            } else {
                responsibleUsers.delete(userId);
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
            responsibleUsers.delete(userId); // Также удаляем из инициаторов
            displaySelectedUsers();
        });
    });
}

// Загрузка изначально выбранных пользователей (при редактировании)
function loadInitialAssignedUsers() {
    const assignedInputs = document.querySelectorAll('input[name="assigned_to"]');
    const initiatorInputs = document.querySelectorAll('input[name="initiator_users"]');
    
    // Собираем ID назначенных пользователей
    const assignedUserIds = [];
    assignedInputs.forEach(function(input) {
        if (input.value) {
            assignedUserIds.push(parseInt(input.value));
        }
    });
    
    // Собираем ID инициаторов инцидента
    const initiatorUserIds = [];
    initiatorInputs.forEach(function(input) {
        if (input.value) {
            initiatorUserIds.push(parseInt(input.value));
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
            
            // Добавляем инициаторов в Set
            initiatorUserIds.forEach(function(userId) {
                responsibleUsers.add(userId);
            });
            
            displaySelectedUsers();
        })
        .catch(error => {
            console.error('Ошибка загрузки пользователей:', error);
        });
}

// Применение выбора назначенных
function applyAssignedSelection() {
    // Удаляем все существующие скрытые поля для assigned_to
    const oldAssignedInputs = document.querySelectorAll('input[name="assigned_to"]');
    oldAssignedInputs.forEach(function(input) {
        input.remove();
    });
    
    // Удаляем все существующие скрытые поля для initiator_users
    const oldInitiatorInputs = document.querySelectorAll('input[name="initiator_users"]');
    oldInitiatorInputs.forEach(function(input) {
        input.remove();
    });
    
    // Находим форму и добавляем новые скрытые поля
    const form = document.querySelector('form');
    
    // Добавляем скрытые поля для назначенных пользователей
    selectedAssignedUsers.forEach(function(user, userId) {
        const hiddenInput = document.createElement('input');
        hiddenInput.type = 'hidden';
        hiddenInput.name = 'assigned_to';
        hiddenInput.value = userId;
        form.appendChild(hiddenInput);
    });
    
    // Добавляем скрытые поля для инициаторов инцидента
    responsibleUsers.forEach(function(userId) {
        const hiddenInput = document.createElement('input');
        hiddenInput.type = 'hidden';
        hiddenInput.name = 'initiator_users';
        hiddenInput.value = userId;
        form.appendChild(hiddenInput);
    });
    
    // Обновляем счетчик
    assignedCount.textContent = selectedAssignedUsers.size;
}

// Инициализация счетчика при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    const hiddenInputs = document.querySelectorAll('input[name="assigned_to"]');
    assignedCount.textContent = hiddenInputs.length;
});