// API endpoints (определяются в шаблоне ipr_module_form.html)
// searchUsersUrl, getUsersByIdsUrl, mentorInputId, supervisorInputId, departmentHeadInputId должны быть определены в шаблоне

// Элементы DOM для выбора пользователей
const modal = document.getElementById('userModal');
const userModalTitle = document.getElementById('userModalTitle');
const mentorSelectField = document.getElementById('mentorSelectField');
const supervisorSelectField = document.getElementById('supervisorSelectField');
const departmentHeadSelectField = document.getElementById('departmentHeadSelectField');
const userModalClose = document.getElementById('userModalClose');
const userSearchInput = document.getElementById('userSearchInput');
const userList = document.getElementById('userList');
const mentorDisplayName = document.getElementById('mentorDisplayName');
const supervisorDisplayName = document.getElementById('supervisorDisplayName');
const departmentHeadDisplayName = document.getElementById('departmentHeadDisplayName');
const mentorInput = document.getElementById(mentorInputId);
const supervisorInput = document.getElementById(supervisorInputId);
const departmentHeadInput = document.getElementById(departmentHeadInputId);

// Переменная для отслеживания, какое поле открыто
let currentActiveField = null;

// ========== ФУНКЦИИ ДЛЯ ВЫБОРА ПОЛЬЗОВАТЕЛЕЙ ==========

// Открытие модального окна для поля "Наставник"
if (mentorSelectField) {
    mentorSelectField.addEventListener('click', function() {
        currentActiveField = 'mentor';
        if (userModalTitle) {
            userModalTitle.textContent = 'Выберите наставника';
        }
        modal.style.display = 'block';
        loadUsers('');
        if (userSearchInput) {
            userSearchInput.focus();
        }
    });
}

// Открытие модального окна для поля "Руководитель"
if (supervisorSelectField) {
    supervisorSelectField.addEventListener('click', function() {
        currentActiveField = 'supervisor';
        if (userModalTitle) {
            userModalTitle.textContent = 'Выберите руководителя';
        }
        modal.style.display = 'block';
        loadUsers('');
        if (userSearchInput) {
            userSearchInput.focus();
        }
    });
}

// Открытие модального окна для поля "Зав отделением"
if (departmentHeadSelectField) {
    departmentHeadSelectField.addEventListener('click', function() {
        currentActiveField = 'department_head';
        if (userModalTitle) {
            userModalTitle.textContent = 'Выберите зав отделением';
        }
        modal.style.display = 'block';
        loadUsers('');
        if (userSearchInput) {
            userSearchInput.focus();
        }
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
    if (!userList) {
        return;
    }
    
    userList.innerHTML = '<div class="user-list-loading">Загрузка...</div>';
    
    // Формируем URL с параметрами
    let url = searchUsersUrl + '?q=' + encodeURIComponent(query);
    
    // Для поля "Наставник" добавляем фильтр для наставников
    if (currentActiveField === 'mentor') {
        url += '&mentor_only=true';
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
    if (!userList) {
        return;
    }
    
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
    if (currentActiveField === 'mentor') {
        // Обновляем поле "Наставник"
        if (mentorInput) {
            mentorInput.value = userId;
        }
        if (mentorDisplayName) {
            mentorDisplayName.textContent = userName;
            mentorDisplayName.classList.remove('user-display-placeholder');
        }
    } else if (currentActiveField === 'supervisor') {
        // Обновляем поле "Руководитель"
        if (supervisorInput) {
            supervisorInput.value = userId;
        }
        if (supervisorDisplayName) {
            supervisorDisplayName.textContent = userName;
            supervisorDisplayName.classList.remove('user-display-placeholder');
        }
    } else if (currentActiveField === 'department_head') {
        // Обновляем поле "Зав отделением"
        if (departmentHeadInput) {
            departmentHeadInput.value = userId;
        }
        if (departmentHeadDisplayName) {
            departmentHeadDisplayName.textContent = userName;
            departmentHeadDisplayName.classList.remove('user-display-placeholder');
        }
    }
    if (modal) {
        modal.style.display = 'none';
    }
    if (userSearchInput) {
        userSearchInput.value = '';
    }
    currentActiveField = null;
}

// Инициализация поля пользователя при загрузке страницы
function initializeUserField(input, displayName, fieldName) {
    // Проверяем, что элементы существуют
    if (!input || !displayName) {
        return;
    }
    
    // Проверяем, есть ли значение в скрытом поле
    const userId = input.value;
    
    // Проверяем текст, который уже отображается из шаблона
    const templateValue = displayName.textContent.trim();
    
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
                        displayName.textContent = user.full_name;
                        displayName.classList.remove('user-display-placeholder');
                    }
                })
                .catch(error => {
                    console.error('Ошибка загрузки пользователя (' + fieldName + '):', error);
                });
        } else {
            // Если текст уже отображается из шаблона, просто убираем класс placeholder
            displayName.classList.remove('user-display-placeholder');
        }
    } else {
        // Если пользователь не выбран, проверяем текст из шаблона
        if (templateValue && templateValue !== 'Выберите пользователя...') {
            // Если в шаблоне есть значение, но нет в скрытом поле - это странно, но оставляем как есть
            displayName.classList.remove('user-display-placeholder');
        } else {
            // Добавляем класс placeholder
            displayName.classList.add('user-display-placeholder');
        }
    }
}

// Инициализация поля наставника при загрузке страницы
function initializeMentorField() {
    initializeUserField(mentorInput, mentorDisplayName, 'mentor');
}

// Инициализация поля руководителя при загрузке страницы
function initializeSupervisorField() {
    initializeUserField(supervisorInput, supervisorDisplayName, 'supervisor');
}

// Инициализация поля зав отделением при загрузке страницы
function initializeDepartmentHeadField() {
    initializeUserField(departmentHeadInput, departmentHeadDisplayName, 'department_head');
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    // Инициализация всех полей при загрузке страницы
    initializeMentorField();
    initializeSupervisorField();
    initializeDepartmentHeadField();
});


