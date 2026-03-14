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

let currentActiveField = 'mentor';

// Открытие модального окна
if (userSelectField) {
    userSelectField.addEventListener('click', function() {
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
    });
}

// Обработчик закрытия модальных окон при клике вне их
window.addEventListener('click', function(event) {
    if (event.target == modal) {
        modal.style.display = 'none';
    }
    // quizModal будет определен после загрузки DOM
    if (typeof quizModal !== 'undefined' && event.target == quizModal) {
        quizModal.style.display = 'none';
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
    
    let url = searchUsersUrl + '?q=' + encodeURIComponent(query);

    // добавляем фильтр для наставников
    url += '&mentor_only=true';
    
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
            fetch(searchUsersUrl + '?q=&mentor_only=true')
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

// ========== ФУНКЦИИ ДЛЯ ВЫБОРА ТЕСТА ==========

// Элементы DOM для выбора теста (инициализируются после загрузки DOM)
let quizModal, quizSelectField, quizModalClose, quizSearchInput, quizList, quizDisplayName, quizInput;

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    // Инициализация элементов для выбора теста
    quizModal = document.getElementById('quizModal');
    quizSelectField = document.getElementById('quizSelectField');
    quizModalClose = document.getElementById('quizModalClose');
    quizSearchInput = document.getElementById('quizSearchInput');
    quizList = document.getElementById('quizList');
    quizDisplayName = document.getElementById('quizDisplayName');
    quizInput = document.getElementById(quizInputId);
    
    // Открытие модального окна выбора теста
    if (quizSelectField) {
        quizSelectField.addEventListener('click', function() {
            quizModal.style.display = 'block';
            loadQuizzes('');
            if (quizSearchInput) {
                quizSearchInput.focus();
            }
        });
    }

    // Закрытие модального окна выбора теста
    if (quizModalClose) {
        quizModalClose.addEventListener('click', function() {
            quizModal.style.display = 'none';
        });
    }
    
    // Поиск тестов с задержкой
    if (quizSearchInput) {
        // Загрузка всех тестов при фокусе на поле поиска
        quizSearchInput.addEventListener('focus', function() {
            // Если поле пустое, загружаем все тесты
            if (this.value.trim().length === 0) {
                loadQuizzes('');
            }
        });
        
        quizSearchInput.addEventListener('input', function() {
            clearTimeout(quizSearchTimeout);
            const query = this.value;
            // При пустом запросе показываем все тесты
            if (query.trim().length === 0) {
                loadQuizzes('');
                return;
            }
            quizSearchTimeout = setTimeout(function() {
                loadQuizzes(query);
            }, 300);
        });
    }
    
    initializeUserField();
    initializeQuizField();
    initializeTimeCounter();
});

// ========== ФУНКЦИИ ДЛЯ СЧЕТЧИКА ВРЕМЕНИ ПРОВЕРКИ ==========

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

// Поиск тестов с задержкой
let quizSearchTimeout;

// Загрузка списка тестов
function loadQuizzes(query) {
    if (!quizList) return;
    
    quizList.innerHTML = '<div class="user-list-loading">Загрузка...</div>';
    
    const url = searchQuizzesUrl + '?q=' + encodeURIComponent(query);
    
    fetch(url)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayQuizzes(data.results);
            } else {
                quizList.innerHTML = '<div class="user-list-error">Ошибка загрузки данных</div>';
            }
        })
        .catch(error => {
            quizList.innerHTML = '<div class="user-list-error">Ошибка загрузки данных</div>';
        });
}

// Отображение списка тестов
function displayQuizzes(quizzes) {
    if (!quizList) return;
    
    let html = '';
    
    // Добавляем опцию для сброса теста (пустое значение)
    html += `
        <div class="user-list-item user-list-item-clear" data-quiz-id="" data-quiz-name="">
            <div class="user-list-item-name" style="color: #6c757d; font-style: italic;">— Не назначать финальный тест —</div>
        </div>
    `;
    
    if (quizzes.length === 0) {
        quizList.innerHTML = html + '<div class="user-list-empty">Тесты не найдены</div>';
        // Добавляем обработчик для опции сброса
        const clearItem = quizList.querySelector('.user-list-item-clear');
        if (clearItem) {
            clearItem.addEventListener('click', function() {
                selectQuiz('', '');
            });
        }
        return;
    }
    
    quizzes.forEach(function(quiz) {
        const questionsText = quiz.questions_count === 1 ? 'вопрос' : 
                              quiz.questions_count < 5 ? 'вопроса' : 'вопросов';
        html += `
            <div class="user-list-item" data-quiz-id="${quiz.id}" data-quiz-name="${quiz.name}">
                <div class="user-list-item-name">${quiz.name}</div>
                <div class="user-list-item-username">${quiz.questions_count} ${questionsText}</div>
            </div>
        `;
    });
    
    quizList.innerHTML = html;
    
    // Добавляем обработчики клика на каждый тест и опцию сброса
    const quizItems = quizList.querySelectorAll('.user-list-item');
    quizItems.forEach(function(item) {
        item.addEventListener('click', function() {
            const quizId = this.getAttribute('data-quiz-id');
            const quizName = this.getAttribute('data-quiz-name');
            selectQuiz(quizId, quizName);
        });
    });
}

// Выбор теста
function selectQuiz(quizId, quizName) {
    if (quizInput) {
        quizInput.value = quizId || '';
    }
    if (quizDisplayName) {
        if (quizId && quizName) {
            quizDisplayName.textContent = quizName;
            quizDisplayName.classList.remove('user-display-placeholder');
        } else {
            // Сброс теста - показываем placeholder
            quizDisplayName.textContent = 'Выберите тест...';
            quizDisplayName.classList.add('user-display-placeholder');
        }
    }
    if (quizModal) {
        quizModal.style.display = 'none';
    }
}

// Инициализация поля теста при загрузке страницы
function initializeQuizField() {
    if (!quizInput || !quizDisplayName) {
        return;
    }
    
    const quizId = quizInput.value;
    const templateValue = quizDisplayName.textContent.trim();
    
    if (quizId) {
        if (templateValue === 'Выберите тест...' || !templateValue) {
            fetch(searchQuizzesUrl + '?q=')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        const quiz = data.results.find(q => q.id === parseInt(quizId));
                        if (quiz) {
                            quizDisplayName.textContent = quiz.name;
                            quizDisplayName.classList.remove('user-display-placeholder');
                        }
                    }
                })
                .catch(error => {
                    console.error('Ошибка загрузки теста:', error);
                });
        } else {
            quizDisplayName.classList.remove('user-display-placeholder');
        }
    } else {
        if (templateValue && templateValue !== 'Выберите тест...') {
            quizDisplayName.classList.remove('user-display-placeholder');
        } else {
            quizDisplayName.classList.add('user-display-placeholder');
        }
    }
}

        // Обработка иконок помощи
        document.addEventListener('DOMContentLoaded', function() {
            const helpIcons = document.querySelectorAll('.help-icon');
            
            helpIcons.forEach(function(icon) {
                // Обработка переносов строк в подсказке
                const tooltip = icon.getAttribute('data-tooltip');
                if (tooltip) {
                    // Заменяем &#10; на реальные переносы строк
                    const formattedTooltip = tooltip.replace(/&#10;/g, '\n');
                    icon.setAttribute('data-tooltip', formattedTooltip);
                }
                
                // Обработка клика для показа/скрытия подсказки
                icon.addEventListener('click', function(e) {
                    e.stopPropagation();
                    const isActive = icon.classList.contains('active');
                    
                    // Закрываем все другие подсказки
                    helpIcons.forEach(function(otherIcon) {
                        if (otherIcon !== icon) {
                            otherIcon.classList.remove('active');
                        }
                    });
                    
                    // Переключаем текущую подсказку
                    if (isActive) {
                        icon.classList.remove('active');
                    } else {
                        icon.classList.add('active');
                    }
                });
                
                // Обработка нажатия Enter/Space для доступности
                icon.addEventListener('keydown', function(e) {
                    if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        icon.click();
                    }
                });
            });
            
            // Закрытие подсказок при клике вне их
            document.addEventListener('click', function(e) {
                if (!e.target.closest('.help-icon')) {
                    helpIcons.forEach(function(icon) {
                        icon.classList.remove('active');
                    });
                }
            });
        });