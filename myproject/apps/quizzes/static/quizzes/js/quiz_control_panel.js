// JavaScript для панели управления тестами

// Глобальные переменные
let questionCounter = 0;
let deleteQuizUrl = '';
let quizzesListUrl = '';

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    initializeQuizControlPanel();
});

function initializeQuizControlPanel() {
    // Получаем URL-ы из data-атрибутов
    const container = document.querySelector('[data-delete-url]');
    if (container) {
        deleteQuizUrl = container.dataset.deleteUrl;
        quizzesListUrl = container.dataset.quizzesUrl;
    }
    
    // Инициализируем обработчики для главной страницы
    initializeMainPageHandlers();
    
    // Инициализируем обработчики для страницы редактирования
    initializeEditPageHandlers();
}

// === ФУНКЦИИ ДЛЯ ГЛАВНОЙ СТРАНИЦЫ ===

function initializeMainPageHandlers() {
    // Обработчик для кнопок удаления
    document.querySelectorAll('.btn-delete-quiz').forEach(button => {
        button.addEventListener('click', function() {
            const quizId = this.dataset.quizId;
            const quizName = this.dataset.quizName;
            
            document.getElementById('quizNameToDelete').textContent = quizName;
            document.getElementById('deleteQuizForm').action = deleteQuizUrl.replace('0', quizId);
            
            const deleteModal = new bootstrap.Modal(document.getElementById('deleteQuizModal'));
            deleteModal.show();
        });
    });

    // Обработка создания теста
    const createQuizForm = document.getElementById('createQuizForm');
    if (createQuizForm) {
        createQuizForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const submitBtn = this.querySelector('button[type="submit"]');
            
            // Показываем индикатор загрузки
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Создание...';
            
            fetch(this.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                },
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return response.text().then(text => {
                    try {
                        return JSON.parse(text);
                    } catch (e) {
                        console.error('Не JSON ответ:', text);
                        throw new Error('Сервер вернул некорректный ответ');
                    }
                });
            })
            .then(data => {
                if (data.success) {
                    location.reload();
                } else {
                    alert('Ошибка: ' + data.error);
                }
            })
            .catch(error => {
                alert('Произошла ошибка при создании теста: ' + error.message);
                console.error('Error:', error);
            })
            .finally(() => {
                // Восстанавливаем кнопку
                submitBtn.disabled = false;
                submitBtn.innerHTML = 'Создать тест';
            });
        });
    }
}

// === ФУНКЦИИ ДЛЯ СТРАНИЦЫ РЕДАКТИРОВАНИЯ ===

function initializeEditPageHandlers() {
    // Проверяем, что мы на странице редактирования
    const editForm = document.getElementById('editQuizForm');
    if (!editForm) return;
    
    // Инициализируем счетчик вопросов
    questionCounter = window.initialQuestionCounter || document.querySelectorAll('.question-block').length;
    
    // Если нет вопросов, добавляем первый
    if (questionCounter === 0) {
        addQuestion();
    }
    
    // Обработка отправки формы редактирования
    editForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const formData = new FormData(this);
        const submitBtn = this.querySelector('button[type="submit"]');
        
        // Показываем индикатор загрузки
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Сохранение...';
        
        fetch(this.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            },
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                alert('Тест успешно обновлен!');
                window.location.href = quizzesListUrl || document.querySelector('[data-quizzes-url]').dataset.quizzesUrl;
            } else {
                alert('Ошибка: ' + data.error);
            }
        })
        .catch(error => {
            alert('Произошла ошибка при сохранении теста: ' + error.message);
            console.error('Error:', error);
        })
        .finally(() => {
            // Восстанавливаем кнопку
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-save"></i> Сохранить изменения';
        });
    });
}

// === ФУНКЦИИ УПРАВЛЕНИЯ ВОПРОСАМИ ===

function addQuestion() {
    questionCounter++;
    const container = document.getElementById('questionsContainer');
    
    const questionHtml = `
    <div class="question-block" data-question-id="${questionCounter}">
        <div class="question-header">
            <h6>Вопрос ${questionCounter}</h6>
            <button type="button" class="remove-btn" onclick="removeQuestion(this)">
                <i class="fas fa-times"></i>
            </button>
        </div>
        
        <div class="mb-3">
            <label class="form-label">Текст вопроса</label>
            <textarea class="form-control" name="questions[${questionCounter}][text]" rows="3" required></textarea>
        </div>

        <div class="mb-3">
            <label class="form-label">Тип вопроса</label>
            <select class="form-select" name="questions[${questionCounter}][type]" onchange="toggleAnswers(this)">
                <option value="single">Один правильный ответ</option>
                <option value="multiple">Несколько правильных ответов</option>
                <option value="text">Открытый ответ</option>
                <option value="match">Соответствие</option>
            </select>
        </div>

        <div class="answers-container">
            <label class="form-label">Варианты ответов</label>
            <div class="answer-item">
                <input type="text" class="form-control" name="questions[${questionCounter}][answers][1][text]" 
                       placeholder="Текст ответа" required>
                <div class="form-check">
                    <input type="radio" class="form-check-input" name="questions[${questionCounter}][correct_answer]" value="1">
                    <label class="form-check-label">Правильный</label>
                </div>
                <button type="button" class="remove-btn ms-2" onclick="removeAnswer(this)">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <button type="button" class="btn-mini primary btn-sm mt-2" onclick="addAnswer(this)">
                <i class="fas fa-plus"></i> Добавить ответ
            </button>
        </div>
    </div>`;
    
    container.insertAdjacentHTML('beforeend', questionHtml);
    updateQuestionsCount();
}

function removeQuestion(button) {
    if (document.querySelectorAll('.question-block').length === 1) {
        alert('Должен остаться хотя бы один вопрос');
        return;
    }
    
    button.closest('.question-block').remove();
    updateQuestionsCount();
    renumberQuestions();
}

function addAnswer(button) {
    const answersContainer = button.closest('.answers-container');
    const questionBlock = button.closest('.question-block');
    const questionId = questionBlock.dataset.questionId;
    const questionType = questionBlock.querySelector('select[name*="[type]"]').value;

    if (questionType === 'match') {
        // Для типа соответствия добавляем пару вопрос-ответ
        const existingPairs = answersContainer.querySelectorAll('.match-pair');
        const pairNumber = existingPairs.length + 1;

        const pairHtml = `
            <div class="match-pair mb-3 p-3 border rounded">
                <div class="row">
                    <div class="col-md-6">
                        <label class="form-label">Вопрос ${pairNumber}</label>
                        <input type="text" class="form-control" name="questions[${questionId}][answers][${pairNumber*2-1}][text]"
                               placeholder="Текст вопроса" required>
                    </div>
                    <div class="col-md-6">
                        <label class="form-label">Ответ ${pairNumber}</label>
                        <input type="text" class="form-control" name="questions[${questionId}][answers][${pairNumber*2}][text]"
                               placeholder="Текст ответа" required>
                    </div>
                </div>
                <button type="button" class="btn btn-sm btn-outline-danger mt-2" onclick="removeMatchPair(this)">
                    <i class="fas fa-times"></i> Удалить пару
                </button>
            </div>
        `;

        answersContainer.insertAdjacentHTML('beforeend', pairHtml);
    } else {
        // Для других типов вопросов добавляем одиночный ответ
        const answerCount = answersContainer.querySelectorAll('.answer-item').length + 1;

        let correctAnswerField = '';
        if (questionType === 'single') {
            correctAnswerField = `<input type="radio" class="form-check-input" name="questions[${questionId}][correct_answer]" value="${answerCount}">`;
        } else {
            correctAnswerField = `<input type="checkbox" class="form-check-input" name="questions[${questionId}][answers][${answerCount}][correct]">`;
        }

        // Проверяем нужен ли required (только для не-текстовых вопросов)
        const isRequired = questionType !== 'text' ? 'required' : '';

        // Определяем placeholder в зависимости от типа вопроса
        let placeholder = 'Текст ответа';
        if (questionType === 'match') {
            placeholder = 'left:Текст или right:Текст';
        }

        const answerHtml = `
        <div class="answer-item">
            <input type="text" class="form-control" name="questions[${questionId}][answers][${answerCount}][text]"
                   placeholder="${placeholder}" ${isRequired}>
            <div class="form-check">
                ${correctAnswerField}
                <label class="form-check-label">Правильный</label>
            </div>
            <button type="button" class="remove-btn ms-2" onclick="removeAnswer(this)">
                <i class="fas fa-times"></i>
            </button>
        </div>`;

        button.insertAdjacentHTML('beforebegin', answerHtml);
    }
}

function removeAnswer(button) {
    const answersContainer = button.closest('.answers-container');
    const answerItems = answersContainer.querySelectorAll('.answer-item');

    if (answerItems.length > 1) {
        button.closest('.answer-item').remove();
    } else {
        alert('Должен остаться хотя бы один вариант ответа');
    }
}

function removeMatchPair(button) {
    button.closest('.match-pair').remove();
}

function toggleAnswers(select) {
    const questionBlock = select.closest('.question-block');
    const answersContainer = questionBlock.querySelector('.answers-container');
    const questionId = questionBlock.dataset.questionId;

    if (select.value === 'text') {
        answersContainer.style.display = 'none';
        // Убираем required с полей ответов для текстовых вопросов
        answersContainer.querySelectorAll('input[type="text"]').forEach(input => input.required = false);
    } else if (select.value === 'match') {
        answersContainer.style.display = 'block';
        // Для типа соответствие показываем специальную инструкцию
        const label = answersContainer.querySelector('label');
        if (label) {
            label.innerHTML = 'Пары вопрос-ответ';
        }

        // Очищаем контейнер и добавляем примеры
        const existingContent = answersContainer.querySelectorAll('.answer-item, .match-pair, .alert');
        existingContent.forEach(item => item.remove());

        // Добавляем примеры для соответствия - создаем пары вопрос-ответ
        let pairHtml = '';
        for (let i = 1; i <= 2; i++) {
            pairHtml += `
                <div class="match-pair mb-3 p-3 border rounded">
                    <div class="row">
                        <div class="col-md-6">
                            <label class="form-label">Вопрос ${i}</label>
                            <input type="text" class="form-control" name="questions[${questionId}][answers][${i*2-1}][text]"
                                   placeholder="Текст вопроса" required>
                        </div>
                        <div class="col-md-6">
                            <label class="form-label">Ответ ${i}</label>
                            <input type="text" class="form-control" name="questions[${questionId}][answers][${i*2}][text]"
                                   placeholder="Текст ответа" required>
                        </div>
                    </div>
                    <button type="button" class="btn btn-sm btn-outline-danger mt-2" onclick="removeMatchPair(this)">
                        <i class="fas fa-times"></i> Удалить пару
                    </button>
                </div>
            `;
        }

        const exampleHtml = `
            <div class="alert alert-info">
                <strong>Инструкция:</strong> Для создания вопроса на соответствие создайте пары вопрос-ответ:<br>
                • Введите текст вопроса в поле "Вопрос"<br>
                • Введите правильный ответ в поле "Ответ"<br>
                • Каждая пара автоматически считается правильной
            </div>
            ${pairHtml}
        `;

        answersContainer.insertAdjacentHTML('beforeend', exampleHtml);

        // Добавляем кнопку добавления ответа
        const addButton = answersContainer.querySelector('.btn-mini');
        if (!addButton) {
            answersContainer.insertAdjacentHTML('beforeend', `
                <button type="button" class="btn-mini primary btn-sm mt-2" onclick="addAnswer(this)">
                    <i class="fas fa-plus"></i> Добавить пару
                </button>
            `);
        }
    } else {
        answersContainer.style.display = 'block';
        // Добавляем required для полей ответов
        answersContainer.querySelectorAll('input[type="text"]').forEach(input => input.required = true);

        // Конвертируем поля правильности ответов при смене типа
        const answerItems = answersContainer.querySelectorAll('.answer-item');
        answerItems.forEach((item, index) => {
            const formCheck = item.querySelector('.form-check');
            const answerNumber = index + 1;

            let newInput = '';
            if (select.value === 'single') {
                // Меняем на радиокнопки
                newInput = `<input type="radio" class="form-check-input" name="questions[${questionId}][correct_answer]" value="${answerNumber}">`;
            } else {
                // Меняем на чекбоксы
                newInput = `<input type="checkbox" class="form-check-input" name="questions[${questionId}][answers][${answerNumber}][correct]">`;
            }

            formCheck.innerHTML = newInput + '<label class="form-check-label">Правильный</label>';
        });
    }
}

function updateQuestionsCount() {
    const count = document.querySelectorAll('.question-block').length;
    const countElement = document.getElementById('questionsCount');
    if (countElement) {
        countElement.textContent = `Всего: ${count}`;
    }
}

function renumberQuestions() {
    document.querySelectorAll('.question-block').forEach((block, index) => {
        const newNumber = index + 1;
        block.dataset.questionId = newNumber;
        block.querySelector('.question-header h6').textContent = `Вопрос ${newNumber}`;
        
        // Обновляем имена полей
        block.querySelectorAll('input, textarea, select').forEach(field => {
            if (field.name) {
                field.name = field.name.replace(/questions\[\d+\]/, `questions[${newNumber}]`);
            }
        });
    });
}

// === УТИЛИТЫ ===

function showNotification(message, type = 'success') {
    // Создаем уведомление (можно заменить на более красивую библиотеку)
    const alertClass = type === 'success' ? 'alert-success' : 'alert-danger';
    const alertHtml = `
    <div class="alert ${alertClass} alert-dismissible fade show position-fixed" 
         style="top: 20px; right: 20px; z-index: 9999; min-width: 300px;">
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    </div>`;
    
    document.body.insertAdjacentHTML('beforeend', alertHtml);
    
    // Автоматически скрываем через 5 секунд
    setTimeout(() => {
        const alert = document.querySelector('.alert');
        if (alert) {
            alert.remove();
        }
    }, 5000);
}

// Валидация форм
function validateQuizForm(form) {
    const questions = form.querySelectorAll('.question-block');
    
    if (questions.length === 0) {
        alert('Добавьте хотя бы один вопрос');
        return false;
    }
    
    for (let question of questions) {
        const questionText = question.querySelector('textarea[name*="[text]"]');
        if (!questionText.value.trim()) {
            alert('Заполните текст всех вопросов');
            questionText.focus();
            return false;
        }

        const questionType = question.querySelector('select[name*="[type]"]').value;
        if (questionType !== 'text') {
            if (questionType === 'match') {
                // Для типа соответствия проверяем пары вопрос-ответ
                const matchPairs = question.querySelectorAll('.match-pair');
                if (matchPairs.length === 0) {
                    alert('Добавьте хотя бы одну пару вопрос-ответ для вопросов типа "Соответствие"');
                    return false;
                }

                // Проверяем, что все поля в парах заполнены
                for (let pair of matchPairs) {
                    const inputs = pair.querySelectorAll('input[type="text"]');
                    for (let input of inputs) {
                        if (!input.value.trim()) {
                            alert('Заполните все поля в парах вопрос-ответ');
                            input.focus();
                            return false;
                        }
                    }
                }
            } else {
                const answers = question.querySelectorAll('.answer-item input[type="text"]');
                let hasCorrectAnswer = false;
                let hasAnswerText = false;

                for (let answer of answers) {
                    if (answer.value.trim()) {
                        hasAnswerText = true;

                        // Проверяем правильность ответа (чекбокс или радиокнопка)
                        const checkbox = answer.closest('.answer-item').querySelector('input[type="checkbox"]');
                        const radio = answer.closest('.answer-item').querySelector('input[type="radio"]');

                        if ((checkbox && checkbox.checked) || (radio && radio.checked)) {
                            hasCorrectAnswer = true;
                        }
                    }
                }

                if (!hasAnswerText) {
                    alert('Добавьте варианты ответов для всех вопросов');
                    return false;
                }

                if (!hasCorrectAnswer) {
                    alert('Отметьте правильные ответы для всех вопросов');
                    return false;
                }
            }
        }
    }
    
    return true;
}
