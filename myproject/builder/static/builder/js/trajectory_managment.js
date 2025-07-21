/**
 * JavaScript для страниц управления траекториями
 */

// Функции для модальных окон
function showCreateCourseModal() {
    var modal = new bootstrap.Modal(document.getElementById('createCourseModal'));
    modal.show();
}

function showCreateTrajectoryModal() {
    var modal = new bootstrap.Modal(document.getElementById('createTrajectoryModal'));
    modal.show();
}

function showCreateQuizModal() {
    var modal = new bootstrap.Modal(document.getElementById('createQuizModal'));
    modal.show();
}

// Функции для работы с траекториями
function viewTrajectory(trajectoryId) {
    
    // Показываем индикатор загрузки
    var modalBody = document.getElementById('trajectoryDetails');
    modalBody.innerHTML = '<div class="text-center"><i class="fas fa-spinner fa-spin fa-2x text-primary"></i><p class="mt-2">Загрузка данных...</p></div>';
    
    var modal = new bootstrap.Modal(document.getElementById('viewTrajectoryModal'));
    modal.show();
    
    // Загружаем данные траектории
    $.ajax({
        url: '/builder/trajectories/' + trajectoryId + '/detail/',
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        },
        success: function(data) {
            renderTrajectoryDetails(data);
        },
        error: function(xhr, status, error) {
            console.error('Ошибка загрузки данных:', error);
            modalBody.innerHTML = '<div class="alert alert-danger">Ошибка загрузки данных траектории</div>';
        }
    });
}

function renderTrajectoryDetails(data) {
    var modalBody = document.getElementById('trajectoryDetails');
    
    var html = `
        <div class="row">
            <div class="col-md-8">
                <h5 class="text-primary mb-3">${data.name}</h5>
                <p class="text-muted">${data.description}</p>
                
                <div class="row mb-4">
                    <div class="col-md-4">
                        <div class="card border-left-primary">
                            <div class="card-body p-3">
                                <div class="text-xs font-weight-bold text-primary text-uppercase">Курсы</div>
                                <div class="h5 mb-0 font-weight-bold text-gray-800">${data.total_courses}</div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card border-left-success">
                            <div class="card-body p-3">
                                <div class="text-xs font-weight-bold text-success text-uppercase">Группы</div>
                                <div class="h5 mb-0 font-weight-bold text-gray-800">${data.total_groups}</div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card border-left-info">
                            <div class="card-body p-3">
                                <div class="text-xs font-weight-bold text-info text-uppercase">Пользователи</div>
                                <div class="h5 mb-0 font-weight-bold text-gray-800">${data.statistics.total_users}</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card">
                    <div class="card-header">
                        <h6 class="m-0 font-weight-bold text-primary">Статистика прохождения</h6>
                    </div>
                    <div class="card-body">
                        <div class="mb-3">
                            <div class="d-flex justify-content-between">
                                <span>Активные:</span>
                                <strong>${data.statistics.active_users}</strong>
                            </div>
                        </div>
                        <div class="mb-3">
                            <div class="d-flex justify-content-between">
                                <span>Завершили:</span>
                                <strong>${data.statistics.completed_users}</strong>
                            </div>
                        </div>
                        <div class="progress mb-2">
                            <div class="progress-bar bg-success" role="progressbar" 
                                 style="width: ${data.statistics.completion_rate}%" 
                                 aria-valuenow="${data.statistics.completion_rate}" 
                                 aria-valuemin="0" aria-valuemax="100">
                                ${data.statistics.completion_rate}%
                            </div>
                        </div>
                        <small class="text-muted">Процент завершения</small>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="row mt-4">
            <div class="col-md-6">
                <h6 class="font-weight-bold text-primary mb-3">
                    <i class="fas fa-graduation-cap"></i> Курсы в траектории
                </h6>
                ${renderCoursesList(data.courses)}
            </div>
            <div class="col-md-6">
                <h6 class="font-weight-bold text-success mb-3">
                    <i class="fas fa-users"></i> Назначенные группы
                </h6>
                ${renderGroupsList(data.groups)}
            </div>
        </div>
    `;
    
    modalBody.innerHTML = html;
}

function renderCoursesList(courses) {
    if (courses.length === 0) {
        return '<div class="text-muted">Курсы не добавлены</div>';
    }
    
    var html = '<div class="list-group list-group-flush">';
    courses.forEach(function(course, index) {
        html += `
            <div class="list-group-item d-flex justify-content-between align-items-center">
                <div>
                    <div class="d-flex align-items-center">
                        <span class="badge badge-primary mr-2">${course.order}</span>
                        <strong>${course.title}</strong>
                    </div>
                    <small class="text-muted">
                        ${course.lesson_count} уроков • Автор: ${course.author}
                    </small>
                </div>
            </div>
        `;
    });
    html += '</div>';
    return html;
}

function renderGroupsList(groups) {
    if (groups.length === 0) {
        return '<div class="text-muted">Группы не назначены</div>';
    }
    
    var html = '<div class="list-group list-group-flush">';
    groups.forEach(function(group) {
        html += `
            <div class="list-group-item d-flex justify-content-between align-items-center">
                <div>
                    <strong>${group.name}</strong>
                </div>
                <span class="badge badge-success badge-pill">${group.user_count} пользователей</span>
            </div>
        `;
    });
    html += '</div>';
    return html;
}

function editTrajectory(trajectoryId) {
    // Перенаправление на страницу редактирования
    window.location.href = '/builder/trajectories/' + trajectoryId + '/edit/';
}

function manageCourses(trajectoryId) {
    // Перенаправление на страницу управления курсами
    window.location.href = '/builder/trajectories/' + trajectoryId + '/courses/';
}

function deleteTrajectory(trajectoryId, trajectoryName) {
    if (confirm('Вы уверены, что хотите удалить траекторию "' + trajectoryName + '"?\n\nЭто действие нельзя отменить.')) {
        // Здесь можно добавить AJAX запрос для удаления
        // window.location.href = '/courses/trajectory/' + trajectoryId + '/delete/';
    }
}

// Функция для показа уведомлений
function showNotification(message, type) {
    // Создаем элемент уведомления
    var alertClass = type === 'success' ? 'alert-success' : 'alert-danger';
    var icon = type === 'success' ? 'fas fa-check-circle' : 'fas fa-exclamation-circle';
    
    var notification = $('<div class="alert ' + alertClass + ' alert-dismissible fade show" role="alert">' +
        '<i class="' + icon + '"></i> ' + message +
        '<button type="button" class="btn-close" data-bs-dismiss="alert"></button></div>');
    
    // Добавляем уведомление в начало страницы
    $('.container-fluid').prepend(notification);
    
    // Автоматически скрываем через 5 секунд
    setTimeout(function() {
        notification.alert('close');
    }, 5000);
}

// Инициализация при загрузке страницы
$(document).ready(function() {
    
    // Обработка создания курса
    $('#createCourseForm').on('submit', function(e) {
        e.preventDefault();
        var form = $(this);
        var submitBtn = form.find('button[type="submit"]');
        var originalText = submitBtn.text();
        
        // Показываем индикатор загрузки
        submitBtn.prop('disabled', true).text('Создание...');
        
        // Создаем FormData для отправки файлов
        var formData = new FormData(form[0]);
        
        $.ajax({
            url: form.attr('action'),
            method: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json'
            },
            success: function(data) {
                if (data.success) {
                    // Показываем уведомление об успехе
                    showNotification('Курс успешно создан!', 'success');
                    var modal = bootstrap.Modal.getInstance(document.getElementById('createCourseModal'));
                    modal.hide();
                    // Перенаправляем к созданному курсу
                    setTimeout(function() {
                        window.location.href = '/courses/course/' + data.slug + '/';
                    }, 1000);
                } else {
                    showNotification('Ошибка при создании курса', 'error');
                }
            },
            error: function(xhr, status, error) {
                showNotification('Ошибка при создании курса: ' + error, 'error');
            },
            complete: function() {
                // Восстанавливаем кнопку
                submitBtn.prop('disabled', false).text(originalText);
            }
        });
    });

    // Обработка создания траектории
    $('#createTrajectoryForm').on('submit', function(e) {
        e.preventDefault();
        var form = $(this);
        var submitBtn = form.find('button[type="submit"]');
        var originalText = submitBtn.text();
        
        // Показываем индикатор загрузки
        submitBtn.prop('disabled', true).text('Создание...');
        
        $.ajax({
            url: form.attr('action'),
            method: 'POST',
            data: form.serialize(),
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            },
            success: function(data) {
                if (data.success) {
                    showNotification('Траектория успешно создана!', 'success');
                    var modal = bootstrap.Modal.getInstance(document.getElementById('createTrajectoryModal'));
                    modal.hide();
                    // Перезагружаем страницу для обновления статистики
                    setTimeout(function() {
                        location.reload();
                    }, 1000);
                } else {
                    showNotification('Ошибка при создании траектории', 'error');
                }
            },
            error: function(xhr, status, error) {
                console.error('Ошибка AJAX:', error);
                console.error('Статус:', xhr.status);
                console.error('Ответ:', xhr.responseText);
                showNotification('Ошибка при создании траектории: ' + error, 'error');
            },
            complete: function() {
                submitBtn.prop('disabled', false).text(originalText);
            }
        });
    });

    // Обработка создания теста
    $('#createQuizForm').on('submit', function(e) {
        e.preventDefault();
        var form = $(this);
        var submitBtn = form.find('button[type="submit"]');
        var originalText = submitBtn.text();
        
        // Показываем индикатор загрузки
        submitBtn.prop('disabled', true).text('Создание...');
        
        $.ajax({
            url: form.attr('action'),
            method: 'POST',
            data: form.serialize(),
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            },
            success: function(data) {
                if (data.success) {
                    showNotification('Тест успешно создан!', 'success');
                    var modal = bootstrap.Modal.getInstance(document.getElementById('createQuizModal'));
                    modal.hide();
                    // Перезагружаем страницу для обновления статистики
                    setTimeout(function() {
                        location.reload();
                    }, 1000);
                } else {
                    showNotification('Ошибка при создании теста', 'error');
                }
            },
            error: function(xhr, status, error) {
                console.error('Ошибка AJAX:', error);
                console.error('Статус:', xhr.status);
                console.error('Ответ:', xhr.responseText);
                showNotification('Ошибка при создании теста: ' + error, 'error');
            },
            complete: function() {
                submitBtn.prop('disabled', false).text(originalText);
            }
        });
    });

    // Очистка форм при закрытии модальных окон
    $('.modal').on('hidden.bs.modal', function() {
        $(this).find('form')[0].reset();
    });

    // Инициализация DataTables для улучшенной функциональности таблицы
    if ($('#trajectoriesTable').length) {
        $('#trajectoriesTable').DataTable({
            "language": {
                "url": "//cdn.datatables.net/plug-ins/1.10.24/i18n/Russian.json"
            },
            "pageLength": 25,
            "order": [[0, "asc"]],
            "responsive": true
        });
    }
});

// ===== КОД ДЛЯ СОЗДАНИЯ ТЕСТОВ =====

// Глобальные переменные для управления вопросами
let questionCounter = 0;
let isFormSubmitting = false; // Флаг для предотвращения двойной отправки
let currentRequestId = null; // Уникальный ID для текущего запроса

// Функция для добавления нового вопроса
function addQuestion() {
    questionCounter++;
    const questionHtml = `
        <div class="question-block card mb-3" data-question-id="${questionCounter}">
            <div class="card-header d-flex justify-content-between align-items-center">
                <h6 class="mb-0">Вопрос ${questionCounter}</h6>
                <button type="button" class="btn btn-danger btn-sm" onclick="removeQuestion(${questionCounter})">
                    <i class="fas fa-trash"></i> Удалить
                </button>
            </div>
            <div class="card-body">
                <!-- Текст вопроса -->
                <div class="form-group mb-3">
                    <label class="form-label">Текст вопроса *</label>
                    <input type="text" class="form-control" name="questions[${questionCounter}][text]" required>
                </div>
                
                <!-- Тип вопроса -->
                <div class="form-group mb-3">
                    <label class="form-label">Тип вопроса *</label>
                    <select class="form-control" name="questions[${questionCounter}][type]" onchange="toggleAnswerType(${questionCounter}, this.value)">
                        <option value="single">Один правильный ответ</option>
                        <option value="multiple">Несколько правильных ответов</option>
                        <option value="text">Открытый ответ</option>
                    </select>
                </div>
                
                <!-- Контейнер для ответов -->
                <div class="answers-container" id="answers-${questionCounter}">
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <label class="form-label mb-0">Варианты ответов</label>
                        <button type="button" class="btn btn-outline-primary btn-sm" onclick="addAnswer(${questionCounter})">
                            <i class="fas fa-plus"></i> Добавить ответ
                        </button>
                    </div>
                    <div class="answers-list" id="answers-list-${questionCounter}">
                        <!-- Ответы будут добавляться динамически -->
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.getElementById('questionsContainer').insertAdjacentHTML('beforeend', questionHtml);
    
    // Добавляем первые два ответа по умолчанию
    addAnswer(questionCounter);
    addAnswer(questionCounter);
}

// Функция для удаления вопроса
function removeQuestion(questionId) {
    const questionBlock = document.querySelector(`[data-question-id="${questionId}"]`);
    if (questionBlock) {
        questionBlock.remove();
        // Пересчитываем номера вопросов
        renumberQuestions();
    }
}

// Функция для добавления ответа
function addAnswer(questionId) {
    const answersList = document.getElementById(`answers-list-${questionId}`);
    const answerCount = answersList.children.length + 1;
    
    const answerHtml = `
        <div class="answer-item d-flex align-items-center mb-2" data-answer-id="${answerCount}">
            <div class="flex-grow-1 me-2">
                <input type="text" class="form-control form-control-sm" 
                       name="questions[${questionId}][answers][${answerCount}][text]" 
                       placeholder="Вариант ответа ${answerCount}" required>
            </div>
            <div class="me-2">
                <div class="form-check">
                    <input class="form-check-input" type="checkbox" 
                           name="questions[${questionId}][answers][${answerCount}][correct]" 
                           id="correct-${questionId}-${answerCount}"
                           onchange="handleCheckboxChange(${questionId}, this)">
                    <label class="form-check-label" for="correct-${questionId}-${answerCount}">
                        Правильный
                    </label>
                </div>
            </div>
            <button type="button" class="btn btn-outline-danger btn-sm" onclick="removeAnswer(${questionId}, ${answerCount})">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;
    
    answersList.insertAdjacentHTML('beforeend', answerHtml);
}

// Функция для удаления ответа
function removeAnswer(questionId, answerId) {
    const answerItem = document.querySelector(`[data-question-id="${questionId}"] .answer-item[data-answer-id="${answerId}"]`);
    if (answerItem) {
        answerItem.remove();
        // Пересчитываем номера ответов
        renumberAnswers(questionId);
    }
}

// Функция для переключения типа вопроса
function toggleAnswerType(questionId, questionType) {
    const answersContainer = document.getElementById(`answers-${questionId}`);
    const answersList = document.getElementById(`answers-list-${questionId}`);
    
    if (questionType === 'text') {
        // Для открытого ответа скрываем варианты ответов
        answersContainer.style.display = 'none';
        answersList.innerHTML = '';
    } else {
        // Для других типов показываем варианты ответов
        answersContainer.style.display = 'block';
        if (answersList.children.length === 0) {
            // Добавляем первые два ответа если их нет
            addAnswer(questionId);
            addAnswer(questionId);
        }
    }
    
    // Валидируем чекбоксы при смене типа
    validateCheckboxes(questionId, questionType);
}

// Функция для валидации чекбоксов в зависимости от типа вопроса
function validateCheckboxes(questionId, questionType) {
    const answersList = document.getElementById(`answers-list-${questionId}`);
    const checkboxes = answersList.querySelectorAll('input[type="checkbox"]');
    
    if (questionType === 'single') {
        // Для одного правильного ответа снимаем все чекбоксы кроме первого отмеченного
        let firstChecked = null;
        checkboxes.forEach((checkbox, index) => {
            if (checkbox.checked && firstChecked === null) {
                firstChecked = index;
            } else if (checkbox.checked && firstChecked !== null) {
                checkbox.checked = false;
            }
        });
    }
}

// Функция для обработки изменения чекбокса
function handleCheckboxChange(questionId, changedCheckbox) {
    const questionBlock = document.querySelector(`[data-question-id="${questionId}"]`);
    const questionType = questionBlock.querySelector('select[name*="[type]"]').value;
    
    if (questionType === 'single' && changedCheckbox.checked) {
        // Если это вопрос с одним правильным ответом и чекбокс отмечен
        const answersList = document.getElementById(`answers-list-${questionId}`);
        const checkboxes = answersList.querySelectorAll('input[type="checkbox"]');
        
        // Снимаем все остальные чекбоксы
        checkboxes.forEach(checkbox => {
            if (checkbox !== changedCheckbox) {
                checkbox.checked = false;
            }
        });
    }
}

// Функция для пересчета номеров вопросов
function renumberQuestions() {
    const questions = document.querySelectorAll('.question-block');
    questions.forEach((question, index) => {
        const questionNumber = index + 1;
        question.setAttribute('data-question-id', questionNumber);
        question.querySelector('.card-header h6').textContent = `Вопрос ${questionNumber}`;
        
        // Обновляем все атрибуты name в вопросе
        const questionInputs = question.querySelectorAll('input, select');
        questionInputs.forEach(input => {
            if (input.name) {
                input.name = input.name.replace(/questions\[\d+\]/, `questions[${questionNumber}]`);
            }
        });
        
        // Обновляем ID и onclick для кнопок
        const removeButton = question.querySelector('.btn-danger');
        if (removeButton) {
            removeButton.setAttribute('onclick', `removeQuestion(${questionNumber})`);
        }
        
        const addAnswerButton = question.querySelector('.btn-outline-primary');
        if (addAnswerButton) {
            addAnswerButton.setAttribute('onclick', `addAnswer(${questionNumber})`);
        }
        
        // Обновляем ID контейнеров ответов
        const answersContainer = question.querySelector('.answers-container');
        if (answersContainer) {
            answersContainer.id = `answers-${questionNumber}`;
        }
        
        const answersList = question.querySelector('.answers-list');
        if (answersList) {
            answersList.id = `answers-list-${questionNumber}`;
        }
        
        // Пересчитываем ответы в этом вопросе
        renumberAnswers(questionNumber);
    });
    
    // Обновляем глобальный счетчик
    questionCounter = questions.length;
}

// Функция для пересчета номеров ответов
function renumberAnswers(questionId) {
    const answers = document.querySelectorAll(`[data-question-id="${questionId}"] .answer-item`);
    answers.forEach((answer, index) => {
        const answerNumber = index + 1;
        answer.setAttribute('data-answer-id', answerNumber);
        
        // Обновляем атрибуты name
        const textInput = answer.querySelector('input[type="text"]');
        if (textInput) {
            textInput.name = textInput.name.replace(/answers\[\d+\]/, `answers[${answerNumber}]`);
            textInput.placeholder = `Вариант ответа ${answerNumber}`;
        }
        
        const checkbox = answer.querySelector('input[type="checkbox"]');
        if (checkbox) {
            checkbox.name = checkbox.name.replace(/answers\[\d+\]/, `answers[${answerNumber}]`);
            checkbox.id = `correct-${questionId}-${answerNumber}`;
        }
        
        const label = answer.querySelector('label');
        if (label) {
            label.setAttribute('for', `correct-${questionId}-${answerNumber}`);
        }
        
        // Обновляем onclick для кнопки удаления
        const removeButton = answer.querySelector('.btn-outline-danger');
        if (removeButton) {
            removeButton.setAttribute('onclick', `removeAnswer(${questionId}, ${answerNumber})`);
        }
    });
}

// Функция валидации формы теста
function validateQuizForm() {
    const questions = document.querySelectorAll('.question-block');
    
    for (let i = 0; i < questions.length; i++) {
        const question = questions[i];
        const questionNumber = i + 1;
        
        // Проверяем текст вопроса
        const questionText = question.querySelector('input[name*="[text]"]').value.trim();
        if (!questionText) {
            return {
                isValid: false,
                message: `Вопрос ${questionNumber}: Текст вопроса не может быть пустым`
            };
        }
        
        // Проверяем тип вопроса
        const questionType = question.querySelector('select[name*="[type]"]').value;
        
        // Проверяем ответы для вопросов с вариантами
        if (questionType !== 'text') {
            const answers = question.querySelectorAll('.answer-item');
            let correctAnswersCount = 0;
            let hasAnswers = false;
            
            for (let j = 0; j < answers.length; j++) {
                const answer = answers[j];
                const answerText = answer.querySelector('input[type="text"]').value.trim();
                const isCorrect = answer.querySelector('input[type="checkbox"]').checked;
                
                if (answerText) {
                    hasAnswers = true;
                    if (isCorrect) {
                        correctAnswersCount++;
                    }
                }
            }
            
            // Проверяем, что есть хотя бы один ответ
            if (!hasAnswers) {
                return {
                    isValid: false,
                    message: `Вопрос ${questionNumber}: Добавьте хотя бы один вариант ответа`
                };
            }
            
            // Проверяем правильность ответов в зависимости от типа
            if (questionType === 'single') {
                if (correctAnswersCount === 0) {
                    return {
                        isValid: false,
                        message: `Вопрос ${questionNumber}: Для вопроса с одним правильным ответом выберите один правильный вариант`
                    };
                } else if (correctAnswersCount > 1) {
                    return {
                        isValid: false,
                        message: `Вопрос ${questionNumber}: Для вопроса с одним правильным ответом выберите только один правильный вариант (сейчас выбрано ${correctAnswersCount})`
                    };
                }
            } else if (questionType === 'multiple') {
                if (correctAnswersCount === 0) {
                    return {
                        isValid: false,
                        message: `Вопрос ${questionNumber}: Для вопроса с несколькими правильными ответами выберите хотя бы один правильный вариант`
                    };
                }
            }
        }
    }
    
    return { isValid: true, message: '' };
}

// Функция для показа модального окна создания теста
function showCreateQuizModal() {
    // Сбрасываем флаг отправки
    isFormSubmitting = false;
    
    // Очищаем контейнер вопросов
    document.getElementById('questionsContainer').innerHTML = '';
    questionCounter = 0;
    
    // Очищаем форму
    document.getElementById('createQuizForm').reset();
    
    // Показываем модальное окно
    $('#createQuizModal').modal('show');
    
    // Фокусируемся на поле названия теста
    setTimeout(() => {
        document.getElementById('quiz_name').focus();
    }, 500);
}

// Функция для отправки формы теста
function submitQuizForm() {
    // Проверяем, что форма уже не отправляется
    if (isFormSubmitting) {
        console.log('Форма уже отправляется, игнорируем повторный запрос');
        return;
    }
    
    // Проверяем, что есть хотя бы один вопрос
    if (questionCounter === 0) {
        alert('Добавьте хотя бы один вопрос к тесту!');
        return;
    }
    
    // Валидация вопросов и ответов
    const validationResult = validateQuizForm();
    if (!validationResult.isValid) {
        alert(validationResult.message);
        return;
    }
    
    // Устанавливаем флаг отправки и генерируем уникальный ID запроса
    isFormSubmitting = true;
    currentRequestId = Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    
    // Получаем форму и кнопку
    const form = document.getElementById('createQuizForm');
    const submitButton = form.querySelector('button[onclick="submitQuizForm()"]');
    const originalText = submitButton.innerHTML;
    
    // Отключаем кнопку отправки
    submitButton.disabled = true;
    submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Создание...';
    
    // Собираем данные формы
    const formData = new FormData(form);
    formData.append('request_id', currentRequestId);
    
    // Отправляем AJAX запрос
    fetch(form.action, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        // Проверяем, что ответ действительно JSON
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            throw new Error('Сервер вернул неверный формат ответа. Попробуйте еще раз.');
        }
        
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // Сбрасываем флаг отправки
            isFormSubmitting = false;
            
            // Закрываем модальное окно
            $('#createQuizModal').modal('hide');
            
            // Показываем уведомление об успехе
            if (typeof showNotification === 'function') {
                showNotification('Тест успешно создан!', 'success');
            } else {
                alert('Тест успешно создан!');
            }
            
            // Перезагружаем страницу через секунду
            setTimeout(() => {
                location.reload();
            }, 1000);
        } else {
            alert('Ошибка при создании теста: ' + (data.error || 'Неизвестная ошибка'));
            // Восстанавливаем кнопку и флаг
            submitButton.disabled = false;
            submitButton.innerHTML = originalText;
            isFormSubmitting = false;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        
        // Показываем понятное сообщение об ошибке
        let errorMessage = 'Ошибка при создании теста';
        if (error.message.includes('Unexpected token')) {
            errorMessage = 'Ошибка сервера: получен неверный ответ. Попробуйте еще раз или обратитесь к администратору.';
        } else if (error.message.includes('HTTP error')) {
            errorMessage = 'Ошибка сервера: ' + error.message;
        } else {
            errorMessage = error.message;
        }
        
        alert(errorMessage);
        // Восстанавливаем кнопку и флаг
        submitButton.disabled = false;
        submitButton.innerHTML = originalText;
        isFormSubmitting = false;
    });
}
