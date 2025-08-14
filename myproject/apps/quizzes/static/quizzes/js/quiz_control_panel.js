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
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    location.reload();
                } else {
                    alert('Ошибка: ' + data.error);
                }
            })
            .catch(error => {
                alert('Произошла ошибка при создании теста');
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
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Тест успешно обновлен!');
                window.location.href = quizzesListUrl || document.querySelector('[data-quizzes-url]').dataset.quizzesUrl;
            } else {
                alert('Ошибка: ' + data.error);
            }
        })
        .catch(error => {
            alert('Произошла ошибка при сохранении теста');
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
            </select>
        </div>

        <div class="answers-container">
            <label class="form-label">Варианты ответов</label>
            <div class="answer-item">
                <input type="text" class="form-control" name="questions[${questionCounter}][answers][1][text]" 
                       placeholder="Текст ответа" required>
                <div class="form-check">
                    <input type="checkbox" class="form-check-input" name="questions[${questionCounter}][answers][1][correct]">
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
    const answerCount = answersContainer.querySelectorAll('.answer-item').length + 1;
    
    const answerHtml = `
    <div class="answer-item">
        <input type="text" class="form-control" name="questions[${questionId}][answers][${answerCount}][text]" 
               placeholder="Текст ответа" required>
        <div class="form-check">
            <input type="checkbox" class="form-check-input" name="questions[${questionId}][answers][${answerCount}][correct]">
            <label class="form-check-label">Правильный</label>
        </div>
        <button type="button" class="remove-btn ms-2" onclick="removeAnswer(this)">
            <i class="fas fa-times"></i>
        </button>
    </div>`;
    
    button.insertAdjacentHTML('beforebegin', answerHtml);
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

function toggleAnswers(select) {
    const answersContainer = select.closest('.question-block').querySelector('.answers-container');
    if (select.value === 'text') {
        answersContainer.style.display = 'none';
        answersContainer.querySelectorAll('input[required]').forEach(input => input.required = false);
    } else {
        answersContainer.style.display = 'block';
        answersContainer.querySelectorAll('input[type="text"]').forEach(input => input.required = true);
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
            const answers = question.querySelectorAll('.answer-item input[type="text"]');
            let hasCorrectAnswer = false;
            let hasAnswerText = false;
            
            for (let answer of answers) {
                if (answer.value.trim()) {
                    hasAnswerText = true;
                    const checkbox = answer.closest('.answer-item').querySelector('input[type="checkbox"]');
                    if (checkbox.checked) {
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
    
    return true;
}
