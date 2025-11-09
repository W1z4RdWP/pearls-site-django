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

// Элементы DOM для выбора наставника (проверяющий наставник)
const mentorSelectField = document.getElementById('mentorSelectField');
const mentorDisplayName = document.getElementById('mentorDisplayName');
const mentorInput = document.getElementById(mentorInputId);

// Переменная для отслеживания, какое поле открыто (user или mentor)
let currentActiveField = null;

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

// Флаг, указывающий, были ли загружены начальные данные из формы
let initialDataLoaded = false;

// Кэш последних результатов поиска
let lastSearchResults = [];

// ========== ФУНКЦИИ ДЛЯ ВЫБОРА ПОЛЬЗОВАТЕЛЯ (КТО ЗАФИКСИРОВАЛ) ==========

// Открытие модального окна для поля "Кто зафиксировал"
if (userSelectField) {
    userSelectField.addEventListener('click', function() {
        currentActiveField = 'user';
        modal.style.display = 'block';
        loadUsers('');
        userSearchInput.focus();
    });
}

// Открытие модального окна для поля "Проверяющий наставник"
if (mentorSelectField) {
    mentorSelectField.addEventListener('click', function() {
        currentActiveField = 'mentor';
        modal.style.display = 'block';
        loadUsers('');
        userSearchInput.focus();
    });
}

// Закрытие модального окна
if (userModalClose) {
    userModalClose.addEventListener('click', function() {
        modal.style.display = 'none';
        currentActiveField = null;
    });
}

window.addEventListener('click', function(event) {
    if (event.target == modal) {
        modal.style.display = 'none';
        currentActiveField = null;
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
    if (currentActiveField === 'user') {
        // Обновляем поле "Кто зафиксировал"
        if (userInput) {
            userInput.value = userId;
        }
        if (userDisplayName) {
            userDisplayName.textContent = userName;
            userDisplayName.classList.remove('user-display-placeholder');
        }
    } else if (currentActiveField === 'mentor') {
        // Обновляем поле "Проверяющий наставник"
        if (mentorInput) {
            mentorInput.value = userId;
        }
        if (mentorDisplayName) {
            mentorDisplayName.textContent = userName;
            mentorDisplayName.classList.remove('user-display-placeholder');
        }
    }
    modal.style.display = 'none';
    currentActiveField = null;
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

// Инициализация поля наставника при загрузке страницы
function initializeMentorField() {
    // Проверяем, что элементы существуют
    if (!mentorInput || !mentorDisplayName) {
        return;
    }
    
    // Проверяем, есть ли значение в скрытом поле
    const userId = mentorInput.value;
    
    // Проверяем текст, который уже отображается из шаблона
    const templateValue = mentorDisplayName.textContent.trim();
    
    if (userId) {
        // Если есть значение в скрытом поле, но текст placeholder - загружаем информацию
        if (templateValue === 'Выберите пользователя...' || !templateValue) {
            fetch(searchUsersUrl + '?q=')
                .then(response => response.json())
                .then(data => {
                    const user = data.users.find(u => u.id === parseInt(userId));
                    if (user) {
                        mentorDisplayName.textContent = user.full_name;
                        mentorDisplayName.classList.remove('user-display-placeholder');
                    }
                })
                .catch(error => {
                    console.error('Ошибка загрузки наставника:', error);
                });
        } else {
            // Если текст уже отображается из шаблона, просто убираем класс placeholder
            mentorDisplayName.classList.remove('user-display-placeholder');
        }
    } else {
        // Если наставник не выбран, проверяем текст из шаблона
        if (templateValue && templateValue !== 'Выберите пользователя...') {
            // Если в шаблоне есть значение, но нет в скрытом поле - это странно, но оставляем как есть
            mentorDisplayName.classList.remove('user-display-placeholder');
        } else {
            // Добавляем класс placeholder
            mentorDisplayName.classList.add('user-display-placeholder');
        }
    }
}

// Инициализация счетчика времени проверки
function initializeTimeCounter() {
    const decreaseBtn = document.getElementById('timeCounterDecrease');
    const increaseBtn = document.getElementById('timeCounterIncrease');
    const timeInput = document.getElementById('id_mentors_time_to_check');
    
    if (!decreaseBtn || !increaseBtn || !timeInput) {
        return;
    }
    
    // Установка минимального значения
    const minValue = parseInt(timeInput.getAttribute('min')) || 1;
    
    // Обработчик для кнопки уменьшения
    decreaseBtn.addEventListener('click', function() {
        let currentValue = parseInt(timeInput.value) || minValue;
        if (currentValue > minValue) {
            currentValue--;
            timeInput.value = currentValue;
        }
    });
    
    // Обработчик для кнопки увеличения
    increaseBtn.addEventListener('click', function() {
        let currentValue = parseInt(timeInput.value) || minValue;
        currentValue++;
        timeInput.value = currentValue;
    });
}

// Инициализация поля дедлайна при загрузке страницы
function initializeDeadlineField() {
    const deadlineInput = document.getElementById('id_deadline');
    if (!deadlineInput) {
        return;
    }
    
    // Проверяем значение из атрибута value (если установлено в форме) или из value
    let deadlineValue = deadlineInput.value || deadlineInput.getAttribute('value') || '';
    
    if (!deadlineValue || deadlineValue.trim() === '') {
        return;
    }
    
    deadlineValue = deadlineValue.trim();
    
    // Если значение уже в правильном формате (YYYY-MM-DDTHH:MM), используем его
    const datetimeLocalRegex = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/;
    if (datetimeLocalRegex.test(deadlineValue)) {
        deadlineInput.value = deadlineValue;
        return;
    }
    
    // Пытаемся преобразовать значение в формат datetime-local
    try {
        // Если значение содержит пробел, заменяем на 'T'
        if (deadlineValue.includes(' ')) {
            deadlineValue = deadlineValue.replace(' ', 'T');
        }
        
        // Парсим дату
        let dateObj;
        if (deadlineValue.includes('T')) {
            const parts = deadlineValue.split('T');
            if (parts.length === 2) {
                const datePart = parts[0];
                let timePart = parts[1];
                
                // Удаляем секунды и миллисекунды из части времени
                if (timePart.includes(':')) {
                    const timeParts = timePart.split(':');
                    if (timeParts.length >= 2) {
                        // Берем только часы и минуты
                        timePart = timeParts[0] + ':' + timeParts[1];
                    }
                }
                
                deadlineValue = datePart + 'T' + timePart;
                dateObj = new Date(deadlineValue);
            } else {
                dateObj = new Date(deadlineValue);
            }
        } else {
            dateObj = new Date(deadlineValue);
        }
        
        // Проверяем, что дата валидна
        if (isNaN(dateObj.getTime())) {
            // Если не удалось распарсить через Date, попробуем другой способ
            // Формат может быть YYYY-MM-DD HH:MM:SS или YYYY-MM-DD HH:MM
            const spaceMatch = deadlineValue.match(/^(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2})/);
            if (spaceMatch) {
                deadlineValue = spaceMatch[1] + 'T' + spaceMatch[2];
                deadlineInput.value = deadlineValue;
                return;
            }
            return;
        }
        
        // Форматируем в формат datetime-local (YYYY-MM-DDTHH:MM)
        const year = dateObj.getFullYear();
        const month = String(dateObj.getMonth() + 1).padStart(2, '0');
        const day = String(dateObj.getDate()).padStart(2, '0');
        const hours = String(dateObj.getHours()).padStart(2, '0');
        const minutes = String(dateObj.getMinutes()).padStart(2, '0');
        
        const formattedValue = `${year}-${month}-${day}T${hours}:${minutes}`;
        
        // Устанавливаем значение
        deadlineInput.value = formattedValue;
    } catch (error) {
        // Ошибка при инициализации поля deadline
    }
}

// ========== ФУНКЦИИ ДЛЯ ВЫБОРА НАЗНАЧЕННЫХ ==========

// Открытие модального окна выбора назначенных
assignedSelectField.addEventListener('click', function() {
    assignedModal.style.display = 'block';
    loadGroups();
    // Загружаем начальные данные только если они еще не были загружены
    if (!initialDataLoaded) {
        loadInitialAssignedUsers();
    } else {
        // Если данные уже загружены, просто обновляем отображение
        displaySelectedUsers();
    }
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
            const userId = parseInt(input.value);
            if (userId && !assignedUserIds.includes(userId)) {
                assignedUserIds.push(userId);
            }
        }
    });
    
    // Собираем ID нарушителей
    const violatorUserIds = [];
    violatorInputs.forEach(function(input) {
        if (input.value) {
            const userId = parseInt(input.value);
            if (userId && !violatorUserIds.includes(userId)) {
                violatorUserIds.push(userId);
            }
        }
    });
    
    
    // Если нет ни назначенных, ни нарушителей, но данные уже были загружены ранее, ничего не делаем
    if (assignedUserIds.length === 0 && violatorUserIds.length === 0) {
        if (initialDataLoaded) {
            return;
        }
        // Если данных нет и они еще не загружены, помечаем как загруженные
        initialDataLoaded = true;
        return;
    }
    
    // Объединяем все ID пользователей (назначенные + нарушители)
    const allUserIds = [...new Set([...assignedUserIds, ...violatorUserIds])];
    
    // Загружаем информацию о пользователях по их ID
    // Используем новый endpoint, который принимает список ID
    const idsParam = allUserIds.join(',');
    const url = getUsersByIdsUrl + '?ids=' + encodeURIComponent(idsParam);
    
    fetch(url)
        .then(response => response.json())
        .then(data => {
            // Добавляем назначенных пользователей (только если их еще нет)
            assignedUserIds.forEach(function(userId) {
                if (!selectedAssignedUsers.has(userId)) {
                    const user = data.users.find(u => u.id === userId);
                    if (user) {
                        selectedAssignedUsers.set(userId, user);
                    } else {
                        // Если пользователь не найден в ответе API, это может означать,
                        // что он был деактивирован или удален. Логируем для отладки.
                        console.warn('Пользователь с ID ' + userId + ' не найден при загрузке начальных данных');
                    }
                }
            });
            
            // Добавляем нарушителей в Set (даже если они уже есть, это безопасно)
            violatorUserIds.forEach(function(userId) {
                violatorsSet.add(userId);
            });
            
            
            // Обновляем отображение, если есть назначенные пользователи
            if (selectedAssignedUsers.size > 0) {
                displaySelectedUsers();
            }
            
            // Обновляем счетчик
            assignedCount.textContent = selectedAssignedUsers.size;
            
            // Помечаем, что начальные данные загружены
            initialDataLoaded = true;
        })
        .catch(error => {
            console.error('Ошибка загрузки пользователей:', error);
            initialDataLoaded = true; // Помечаем даже при ошибке, чтобы не пытаться загрузить снова
        });
}

// Применение выбора назначенных
function applyAssignedSelection() {
    // Обновляем скрытые поля перед применением
    updateHiddenFields();
    // Обновляем счетчик
    assignedCount.textContent = selectedAssignedUsers.size;
    // Помечаем, что данные были изменены и должны быть сохранены
    initialDataLoaded = true;
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
    
    // Инициализация полей при загрузке страницы редактирования
    initializeUserField();
    initializeMentorField();
    initializeDeadlineField();
    initializeTimeCounter();
    
    // Загружаем изначально выбранных пользователей и нарушителей при редактировании
    // Это нужно делать сразу при загрузке страницы, чтобы нарушители загрузились
    loadInitialAssignedUsers();
});