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
    // === ПОИСК ПО НАЗВАНИЮ ТЕСТА ===
    initializeQuizSearch();
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
    
    // Инициализируем обработчики для переключения текст/картинка
    initializeMatchImageToggles();
    
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
                <option value="sequence">Последовательность</option>
            </select>
        </div>

        <div class="mb-3 mentor-instruction-field" style="display: none;">
            <label class="form-label">Комментарий для наставника</label>
            <textarea class="form-control" 
                    name="questions[${questionCounter}][mentor_instruction]" 
                    rows="3" 
                    placeholder="Введите комментарий, который будет отображаться наставнику при проверке этого вопроса"></textarea>
            <div class="form-text">Этот комментарий будет показан наставнику при наведении на иконку "?" рядом с вопросом</div>
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

    if (questionType === 'sequence') {
        // Для типа последовательность добавляем элемент с номером
        const answerCount = answersContainer.querySelectorAll('.answer-item, .sequence-answer-item').length + 1;
        
        const sequenceHtml = `
        <div class="answer-item sequence-answer-item">
            <span class="sequence-order-number">${answerCount}</span>
            <input type="text" class="form-control" 
                   name="questions[${questionId}][answers][${answerCount}][text]"
                   placeholder="Элемент ${answerCount}" required>
            <button type="button" class="remove-btn" onclick="removeAnswer(this)">
                <i class="fas fa-times"></i>
            </button>
        </div>`;
        
        button.insertAdjacentHTML('beforebegin', sequenceHtml);
    } else if (questionType === 'match') {
        // Для типа соответствия добавляем пару вопрос-ответ
        const existingPairs = answersContainer.querySelectorAll('.match-pair');
        const pairNumber = existingPairs.length + 1;

        const pairHtml = `
            <div class="match-pair mb-3 p-3 border rounded">
                <div class="row">
                    <div class="col-md-6">
                        <label class="form-label">Вопрос ${pairNumber}</label>
                        <div class="form-check mb-2">
                            <input type="checkbox" class="form-check-input match-image-toggle" 
                                   data-target="question-${questionId}-${pairNumber*2-1}">
                            <label class="form-check-label">Использовать картинку</label>
                        </div>
                        <input type="text" class="form-control match-text-input mb-2" 
                               id="question-text-${questionId}-${pairNumber*2-1}"
                               name="questions[${questionId}][answers][${pairNumber*2-1}][text]"
                               placeholder="Текст вопроса" required>
                        <div class="match-image-upload" id="question-${questionId}-${pairNumber*2-1}" style="display: none;">
                            <input type="file" class="form-control" 
                                   name="questions[${questionId}][answers][${pairNumber*2-1}][image]"
                                   accept="image/*">
                        </div>
                    </div>
                    <div class="col-md-6">
                        <label class="form-label">Ответ ${pairNumber}</label>
                        <div class="form-check mb-2">
                            <input type="checkbox" class="form-check-input match-image-toggle" 
                                   data-target="answer-${questionId}-${pairNumber*2}">
                            <label class="form-check-label">Использовать картинку</label>
                        </div>
                        <input type="text" class="form-control match-text-input mb-2" 
                               id="answer-text-${questionId}-${pairNumber*2}"
                               name="questions[${questionId}][answers][${pairNumber*2}][text]"
                               placeholder="Текст ответа" required>
                        <div class="match-image-upload" id="answer-${questionId}-${pairNumber*2}" style="display: none;">
                            <input type="file" class="form-control" 
                                   name="questions[${questionId}][answers][${pairNumber*2}][image]"
                                   accept="image/*">
                        </div>
                    </div>
                </div>
                <button type="button" class="btn btn-sm btn-outline-danger mt-2" onclick="removeMatchPair(this)">
                    <i class="fas fa-times"></i> Удалить пару
                </button>
            </div>
        `;

        answersContainer.insertAdjacentHTML('beforeend', pairHtml);
        
        // Инициализируем обработчики для новой пары
        initializeMatchImageToggles();
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
    const questionBlock = button.closest('.question-block');
    const questionType = questionBlock.querySelector('select[name*="[type]"]').value;
    const answerItems = answersContainer.querySelectorAll('.answer-item, .sequence-answer-item');

    if (answerItems.length > 1) {
        button.closest('.answer-item, .sequence-answer-item').remove();
        
        // Перенумеровываем элементы последовательности
        if (questionType === 'sequence') {
            const remainingItems = answersContainer.querySelectorAll('.sequence-answer-item');
            remainingItems.forEach((item, index) => {
                const numberSpan = item.querySelector('.sequence-order-number');
                if (numberSpan) {
                    numberSpan.textContent = index + 1;
                }
            });
        }
    } else {
        alert('Должен остаться хотя бы один вариант ответа');
    }
}

function removeMatchPair(button) {
    const answersContainer = button.closest('.answers-container');
    const questionBlock = button.closest('.question-block');
    const questionId = questionBlock.dataset.questionId;
    
    // Проверяем, что остается хотя бы одна пара
    const existingPairs = answersContainer.querySelectorAll('.match-pair');
    if (existingPairs.length <= 1) {
        alert('Должна остаться хотя бы одна пара вопрос-ответ');
        return;
    }
    
    button.closest('.match-pair').remove();
    
    // Перенумеровываем оставшиеся пары
    renumberMatchPairs(questionId);
}

function toggleAnswers(select) {
    const questionBlock = select.closest('.question-block');
    const answersContainer = questionBlock.querySelector('.answers-container');
    const mentorInstructionField = questionBlock.querySelector('.mentor-instruction-field');
    const questionId = questionBlock.dataset.questionId;

    if (select.value === 'text') {
        answersContainer.style.display = 'none';
        // Показываем поле комментария для наставника
        if (mentorInstructionField) {
            mentorInstructionField.style.display = 'block';
        }
        // Убираем required с полей ответов для текстовых вопросов
        answersContainer.querySelectorAll('input[type="text"]').forEach(input => input.required = false);
    } else if (select.value === 'sequence') {
        answersContainer.style.display = 'block';
        // Скрываем поле комментария для наставника
        if (mentorInstructionField) {
            mentorInstructionField.style.display = 'none';
        }
        // Для типа последовательность показываем специальную инструкцию
        const label = answersContainer.querySelector('label');
        if (label) {
            label.innerHTML = 'Элементы последовательности';
        }

        // Проверяем, есть ли уже элементы последовательности
        const existingSequence = answersContainer.querySelectorAll('.sequence-answer-item, .answer-item');
        
        if (existingSequence.length === 0) {
            // Очищаем контейнер
            const existingContent = answersContainer.querySelectorAll('.match-pair, .alert');
            existingContent.forEach(item => item.remove());

            // Добавляем примеры элементов последовательности
            let sequenceHtml = '';
            for (let i = 1; i <= 3; i++) {
                sequenceHtml += `
                    <div class="answer-item sequence-answer-item">
                        <span class="sequence-order-number">${i}</span>
                        <input type="text" class="form-control" 
                               name="questions[${questionId}][answers][${i}][text]"
                               placeholder="Элемент ${i}" required>
                        <button type="button" class="remove-btn" onclick="removeAnswer(this)">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                `;
            }

            const exampleHtml = `
                <div class="alert alert-info">
                    <strong>Инструкция:</strong> Добавьте элементы в правильном порядке. Первый добавленный элемент будет первым в правильной последовательности.
                </div>
                ${sequenceHtml}
            `;

            answersContainer.insertAdjacentHTML('beforeend', exampleHtml);
        } else {
            // Убедимся что есть инструкция
            const existingAlert = answersContainer.querySelector('.alert-info');
            if (!existingAlert) {
                const alertHtml = `
                    <div class="alert alert-info">
                        <strong>Инструкция:</strong> Добавьте элементы в правильном порядке. Первый добавленный элемент будет первым в правильной последовательности.
                    </div>
                `;
                const firstElement = answersContainer.querySelector('.sequence-answer-item, .answer-item');
                if (firstElement) {
                    firstElement.insertAdjacentHTML('beforebegin', alertHtml);
                } else {
                    answersContainer.insertAdjacentHTML('afterbegin', alertHtml);
                }
            }

            // Удаляем галочки "правильный" для существующих элементов
            existingSequence.forEach((item, index) => {
                const formCheck = item.querySelector('.form-check');
                if (formCheck) {
                    formCheck.remove();
                }
                
                // Добавляем класс sequence-answer-item если его нет
                if (!item.classList.contains('sequence-answer-item')) {
                    item.classList.add('sequence-answer-item');
                }
                
                // Добавляем номер последовательности если его нет
                if (!item.querySelector('.sequence-order-number')) {
                    const input = item.querySelector('input[type="text"]');
                    if (input) {
                        const orderNumber = document.createElement('span');
                        orderNumber.className = 'sequence-order-number';
                        orderNumber.textContent = index + 1;
                        input.parentElement.insertBefore(orderNumber, input);
                    }
                } else {
                    // Обновляем существующий номер
                    const orderNumber = item.querySelector('.sequence-order-number');
                    orderNumber.textContent = index + 1;
                }
            });
        }

        // Добавляем кнопку добавления элемента если её нет
        const addButton = answersContainer.querySelector('.btn-mini');
        if (!addButton) {
            answersContainer.insertAdjacentHTML('beforeend', `
                <button type="button" class="btn-mini primary btn-sm mt-2" onclick="addAnswer(this)">
                    <i class="fas fa-plus"></i> Добавить элемент
                </button>
            `);
        }
    } else if (select.value === 'match') {
        answersContainer.style.display = 'block';
        // Скрываем поле комментария для наставника
        if (mentorInstructionField) {
            mentorInstructionField.style.display = 'none';
        }
        // Для типа соответствие показываем специальную инструкцию
        const label = answersContainer.querySelector('label');
        if (label) {
            label.innerHTML = 'Пары вопрос-ответ';
        }

        // Проверяем, есть ли уже match-pair элементы (редактирование существующего вопроса)
        const existingMatchPairs = answersContainer.querySelectorAll('.match-pair');
        
        if (existingMatchPairs.length === 0) {
            // Только если нет существующих пар, создаем новые
            // Очищаем контейнер и добавляем примеры
            const existingContent = answersContainer.querySelectorAll('.answer-item, .alert');
            existingContent.forEach(item => item.remove());

            // Добавляем примеры для соответствия - создаем пары вопрос-ответ
            let pairHtml = '';
            for (let i = 1; i <= 2; i++) {
                pairHtml += `
                    <div class="match-pair mb-3 p-3 border rounded">
                        <div class="row">
                            <div class="col-md-6">
                                <label class="form-label">Вопрос ${i}</label>
                                <div class="form-check mb-2">
                                    <input type="checkbox" class="form-check-input match-image-toggle" 
                                           data-target="question-${questionId}-${i*2-1}">
                                    <label class="form-check-label">Использовать картинку</label>
                                </div>
                                <input type="text" class="form-control match-text-input mb-2" 
                                       id="question-text-${questionId}-${i*2-1}"
                                       name="questions[${questionId}][answers][${i*2-1}][text]"
                                       placeholder="Текст вопроса" required>
                                <div class="match-image-upload" id="question-${questionId}-${i*2-1}" style="display: none;">
                                    <input type="file" class="form-control" 
                                           name="questions[${questionId}][answers][${i*2-1}][image]"
                                           accept="image/*">
                                </div>
                            </div>
                            <div class="col-md-6">
                                <label class="form-label">Ответ ${i}</label>
                                <div class="form-check mb-2">
                                    <input type="checkbox" class="form-check-input match-image-toggle" 
                                           data-target="answer-${questionId}-${i*2}">
                                    <label class="form-check-label">Использовать картинку</label>
                                </div>
                                <input type="text" class="form-control match-text-input mb-2" 
                                       id="answer-text-${questionId}-${i*2}"
                                       name="questions[${questionId}][answers][${i*2}][text]"
                                       placeholder="Текст ответа" required>
                                <div class="match-image-upload" id="answer-${questionId}-${i*2}" style="display: none;">
                                    <input type="file" class="form-control" 
                                           name="questions[${questionId}][answers][${i*2}][image]"
                                           accept="image/*">
                                </div>
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
            
            // Инициализируем обработчики для новых пар
            initializeMatchImageToggles();
        } else {
            // Убедимся что есть инструкция
            const existingAlert = answersContainer.querySelector('.alert-info');
            if (!existingAlert) {
                const alertHtml = `
                    <div class="alert alert-info">
                        <strong>Инструкция:</strong> Для создания вопроса на соответствие создайте пары вопрос-ответ:<br>
                        • Введите текст вопроса в поле "Вопрос"<br>
                        • Введите правильный ответ в поле "Ответ"<br>
                        • Каждая пара автоматически считается правильной
                    </div>
                `;
                const firstElement = answersContainer.querySelector('.match-pair, .answer-item');
                if (firstElement) {
                    firstElement.insertAdjacentHTML('beforebegin', alertHtml);
                } else {
                    answersContainer.insertAdjacentHTML('afterbegin', alertHtml);
                }
            }
        }

        // Добавляем кнопку добавления ответа если её нет
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
        // Скрываем поле комментария для наставника
        if (mentorInstructionField) {
            mentorInstructionField.style.display = 'none';
        }
        // Добавляем required для полей ответов
        answersContainer.querySelectorAll('input[type="text"]').forEach(input => input.required = true);

        // Конвертируем поля правильности ответов при смене типа
        const answerItems = answersContainer.querySelectorAll('.answer-item');
        answerItems.forEach((item, index) => {
            const formCheck = item.querySelector('.form-check');
            const answerNumber = index + 1;

            // Удаляем номера последовательности если они есть
            const sequenceNumber = item.querySelector('.sequence-order-number');
            if (sequenceNumber) {
                sequenceNumber.remove();
            }
            
            // Удаляем класс sequence-answer-item если он есть
            if (item.classList.contains('sequence-answer-item')) {
                item.classList.remove('sequence-answer-item');
            }

            if (!formCheck) {
                // Если нет formCheck, создаем его
                const removeBtn = item.querySelector('.remove-btn');
                const newFormCheck = document.createElement('div');
                newFormCheck.className = 'form-check';
                
                let newInput = '';
                if (select.value === 'single') {
                    newInput = `<input type="radio" class="form-check-input" name="questions[${questionId}][correct_answer]" value="${answerNumber}">`;
                } else {
                    newInput = `<input type="checkbox" class="form-check-input" name="questions[${questionId}][answers][${answerNumber}][correct]">`;
                }
                
                newFormCheck.innerHTML = newInput + '<label class="form-check-label">Правильный</label>';
                if (removeBtn) {
                    removeBtn.parentElement.insertBefore(newFormCheck, removeBtn);
                } else {
                    item.appendChild(newFormCheck);
                }
            } else {
                let newInput = '';
                if (select.value === 'single') {
                    // Меняем на радиокнопки
                    newInput = `<input type="radio" class="form-check-input" name="questions[${questionId}][correct_answer]" value="${answerNumber}">`;
                } else {
                    // Меняем на чекбоксы
                    newInput = `<input type="checkbox" class="form-check-input" name="questions[${questionId}][answers][${answerNumber}][correct]">`;
                }

                formCheck.innerHTML = newInput + '<label class="form-check-label">Правильный</label>';
            }
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
        
        // Обновляем data-target для галочек "Использовать картинку" в парах соответствия
        const matchImageToggles = block.querySelectorAll('.match-image-toggle');
        matchImageToggles.forEach(toggle => {
            const currentTarget = toggle.dataset.target;
            if (currentTarget) {
                // Обновляем ID в data-target, заменяя старый номер вопроса на новый
                const newTarget = currentTarget.replace(/question-\d+-|answer-\d+-/, (match) => {
                    return match.replace(/\d+/, newNumber);
                });
                toggle.dataset.target = newTarget;
            }
        });
        
        // Обновляем ID для контейнеров загрузки изображений
        const imageUploads = block.querySelectorAll('.match-image-upload');
        imageUploads.forEach(upload => {
            const currentId = upload.id;
            if (currentId) {
                const newId = currentId.replace(/question-\d+-|answer-\d+-/, (match) => {
                    return match.replace(/\d+/, newNumber);
                });
                upload.id = newId;
            }
        });
        
        // Обновляем ID для полей ввода текста
        const textInputs = block.querySelectorAll('.match-text-input');
        textInputs.forEach(input => {
            const currentId = input.id;
            if (currentId) {
                const newId = currentId.replace(/question-text-\d+-|answer-text-\d+-/, (match) => {
                    return match.replace(/\d+/, newNumber);
                });
                input.id = newId;
            }
        });
    });
    
    // Переинициализируем обработчики для галочек после перенумерации
    initializeMatchImageToggles();
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

// === ФУНКЦИИ ДЛЯ РАБОТЫ С ИЗОБРАЖЕНИЯМИ В MATCH ТИПЕ ===

function initializeMatchImageToggles() {
    const toggles = document.querySelectorAll('.match-image-toggle');
    
    toggles.forEach(toggle => {
        // Удаляем старые обработчики если есть
        toggle.removeEventListener('change', handleMatchImageToggle);
        // Добавляем новый обработчик
        toggle.addEventListener('change', handleMatchImageToggle);
    });
}

function handleMatchImageToggle(event) {
    const checkbox = event.target;
    const targetId = checkbox.dataset.target;
    const imageUpload = document.getElementById(targetId);
    const textInput = document.getElementById(targetId.replace(/^(question|answer)-/, '$1-text-'));
    
    if (checkbox.checked) {
        // Показываем поле для загрузки изображения
        imageUpload.style.display = 'block';
        // Делаем текстовое поле необязательным
        if (textInput) {
            textInput.required = false;
            textInput.placeholder = 'Текст (опционально, если используется картинка)';
        }
    } else {
        // Скрываем поле для загрузки изображения
        imageUpload.style.display = 'none';
        // Делаем текстовое поле обязательным
        if (textInput) {
            textInput.required = true;
            const isQuestion = targetId.includes('question-');
            textInput.placeholder = isQuestion ? 'Текст вопроса' : 'Текст ответа';
        }
        // Очищаем поле file input
        const fileInput = imageUpload.querySelector('input[type="file"]');
        if (fileInput) {
            fileInput.value = '';
        }
    }
}

// Функция для перенумерации пар соответствия
function renumberMatchPairs(questionId) {
    const answersContainer = document.querySelector(`[data-question-id="${questionId}"] .answers-container`);
    const pairs = answersContainer.querySelectorAll('.match-pair');
    
    pairs.forEach((pair, index) => {
        const pairNumber = index + 1;
        const baseIndex = pairNumber * 2 - 1;
        
        // Обновляем метки
        const questionLabel = pair.querySelector('.col-md-6:first-child .form-label');
        if (questionLabel) {
            questionLabel.textContent = `Вопрос ${pairNumber}`;
        }
        
        const answerLabel = pair.querySelector('.col-md-6:last-child .form-label');
        if (answerLabel) {
            answerLabel.textContent = `Ответ ${pairNumber}`;
        }
        
        // Обновляем атрибуты name для полей ввода текста
        const textInputs = pair.querySelectorAll('input[type="text"]');
        if (textInputs.length >= 2) {
            textInputs[0].name = textInputs[0].name.replace(/answers\[\d+\]/, `answers[${baseIndex}]`);
            textInputs[0].id = `question-text-${questionId}-${baseIndex}`;
            textInputs[0].placeholder = 'Текст вопроса';
            
            textInputs[1].name = textInputs[1].name.replace(/answers\[\d+\]/, `answers[${baseIndex + 1}]`);
            textInputs[1].id = `answer-text-${questionId}-${baseIndex + 1}`;
            textInputs[1].placeholder = 'Текст ответа';
        }
        
        // Обновляем атрибуты для полей загрузки файлов
        const fileInputs = pair.querySelectorAll('input[type="file"]');
        if (fileInputs.length >= 2) {
            fileInputs[0].name = fileInputs[0].name.replace(/answers\[\d+\]/, `answers[${baseIndex}]`);
            fileInputs[1].name = fileInputs[1].name.replace(/answers\[\d+\]/, `answers[${baseIndex + 1}]`);
        }
        
        // Обновляем data-target для галочек
        const checkboxes = pair.querySelectorAll('.match-image-toggle');
        if (checkboxes.length >= 2) {
            checkboxes[0].dataset.target = `question-${questionId}-${baseIndex}`;
            checkboxes[1].dataset.target = `answer-${questionId}-${baseIndex + 1}`;
        }
        
        // Обновляем id для контейнеров загрузки изображений
        const imageUploads = pair.querySelectorAll('.match-image-upload');
        if (imageUploads.length >= 2) {
            imageUploads[0].id = `question-${questionId}-${baseIndex}`;
            imageUploads[1].id = `answer-${questionId}-${baseIndex + 1}`;
        }
    });
    
    // Переинициализируем обработчики для галочек
    initializeMatchImageToggles();
}


// === ФУНКЦИЯ ПОИСКА ТЕСТОВ С AJAX ===

/**
 * Инициализация функциональности поиска тестов по названию
 * Использует AJAX для поиска по всей базе данных
 */
function initializeQuizSearch() {
    const searchInput = document.getElementById('quizSearch');
    if (!searchInput) return;
    
    const container = document.querySelector('[data-search-url]');
    if (!container) {
        console.error('Не найден контейнер с data-search-url');
        return;
    }
    
    const searchUrl = container.dataset.searchUrl;
    const quizCards = document.querySelectorAll('.quiz-card');
    const paginationNav = document.querySelector('nav[aria-label="Page navigation"]');
    
    // Сохраняем оригинальные карточки для восстановления
    const originalRow = document.querySelector('.container .row:last-of-type');
    let originalContent = null;
    
    /**
     * Обработчик ввода в поле поиска с debounce
     */
    let searchTimeout;
    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        
        const searchTerm = this.value.trim();
        
        // Если поле пустое - восстанавливаем оригинальное состояние
        if (searchTerm === '') {
            restoreOriginalState(originalRow, originalContent, paginationNav);
            return;
        }
        
        // Debounce 300мс для снижения нагрузки на сервер
        searchTimeout = setTimeout(() => {
            performAjaxSearch(searchTerm, searchUrl, originalRow, paginationNav);
        }, 300);
    });
    
    // Сохраняем оригинальный контент при первом поиске
    if (!originalContent) {
        originalContent = originalRow.innerHTML;
    }
}

/**
 * Выполняет AJAX запрос для поиска тестов
 * @param {string} searchTerm - Поисковый запрос
 * @param {string} searchUrl - URL для AJAX запроса
 * @param {HTMLElement} targetRow - Контейнер для результатов
 * @param {HTMLElement} paginationNav - Элемент пагинации
 */
function performAjaxSearch(searchTerm, searchUrl, targetRow, paginationNav) {
    // Показываем индикатор загрузки
    showLoadingState(targetRow);
    
    // Скрываем пагинацию во время поиска
    if (paginationNav) {
        paginationNav.style.display = 'none';
    }
    
    // Выполняем AJAX запрос
    fetch(`${searchUrl}?q=${encodeURIComponent(searchTerm)}`, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            renderSearchResults(data.results, targetRow, searchTerm);
        } else {
            showErrorMessage(targetRow, data.error || 'Ошибка поиска');
        }
    })
    .catch(error => {
        console.error('Ошибка AJAX запроса:', error);
        showErrorMessage(targetRow, 'Не удалось выполнить поиск. Попробуйте позже.');
    });
}

/**
 * Отображает результаты поиска
 * @param {Array} results - Массив найденных тестов
 * @param {HTMLElement} targetRow - Контейнер для результатов
 * @param {string} searchTerm - Поисковый запрос для подсветки
 */
function renderSearchResults(results, targetRow, searchTerm) {
    if (results.length === 0) {
        showNoResultsMessage(targetRow, searchTerm);
        return;
    }
    
    // Очищаем контейнер
    targetRow.innerHTML = '';
    
    // Генерируем HTML для каждого результата
    results.forEach(quiz => {
        const quizCard = createQuizCardHTML(quiz, searchTerm);
        targetRow.insertAdjacentHTML('beforeend', quizCard);
    });
    
    // Переинициализируем обработчики для кнопок удаления
    initializeMainPageHandlers();
}

/**
 * Создает HTML для карточки теста
 * @param {Object} quiz - Объект с данными теста
 * @param {string} searchTerm - Поисковый запрос для подсветки
 * @returns {string} HTML строка
 */
function createQuizCardHTML(quiz, searchTerm) {
    // Подсвечиваем совпадение в названии
    const highlightedName = highlightSearchTerm(quiz.name, searchTerm);
    const attemptLimit = quiz.attempt_limit > 0 ? quiz.attempt_limit : '∞';
    
    return `
        <div class="col-12 mb-3">
            <div class="card quiz-card shadow-sm h-100" data-quiz-name="${quiz.name.toLowerCase()}">
                <div class="card-body d-flex align-items-center">
                    <div class="quiz-info">
                        <h5 class="card-title mb-1">${highlightedName}</h5>
                        <p class="text-muted mb-2">${quiz.questions_count} вопросов</p>
                        <p class="text-muted mb-1">
                            <i class="fas fa-redo-alt"></i> 
                            Лимит попыток: ${attemptLimit}
                        </p>
                        <p class="text-muted mb-2">
                            <i class="fas fa-percentage"></i> 
                            Проходной балл: ${quiz.pass_threshold}%
                        </p>
                        <small class="text-secondary">ID: ${quiz.id}</small>
                    </div>
                    <div class="quiz-actions">
                        <a href="/quizzes/start/${quiz.id}/?from_control_panel=1" 
                           class="btn-mini success btn-sm">
                            <i class="fas fa-play"></i> Запустить
                        </a>
                        <a href="/quizzes/edit/${quiz.id}/" 
                           class="btn-mini edit btn-sm">
                            <i class="fas fa-edit"></i> Редактировать
                        </a>
                        <button type="button" 
                                class="btn-mini delete btn-sm btn-delete-quiz"
                                data-quiz-id="${quiz.id}"
                                data-quiz-name="${quiz.name}">
                            <i class="fas fa-trash"></i> Удалить
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
}

/**
 * Подсвечивает поисковый запрос в тексте
 * @param {string} text - Исходный текст
 * @param {string} searchTerm - Что нужно подсветить
 * @returns {string} Текст с HTML подсветкой
 */
function highlightSearchTerm(text, searchTerm) {
    if (!searchTerm) return text;
    
    const regex = new RegExp(`(${escapeRegExp(searchTerm)})`, 'gi');
    return text.replace(regex, '<mark class="search-highlight">$1</mark>');
}

/**
 * Экранирует спецсимволы для регулярного выражения
 * @param {string} string - Строка для экранирования
 * @returns {string} Экранированная строка
 */
function escapeRegExp(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

/**
 * Показывает индикатор загрузки
 * @param {HTMLElement} container - Контейнер
 */
function showLoadingState(container) {
    container.innerHTML = `
        <div class="col-12">
            <div class="text-center py-5">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Загрузка...</span>
                </div>
                <p class="mt-3 text-muted">Поиск тестов...</p>
            </div>
        </div>
    `;
}

/**
 * Показывает сообщение об отсутствии результатов
 * @param {HTMLElement} container - Контейнер
 * @param {string} searchTerm - Поисковый запрос
 */
function showNoResultsMessage(container, searchTerm) {
    container.innerHTML = `
        <div class="col-12">
            <div class="no-results-message">
                <i class="fas fa-search"></i>
                <h5 class="text-muted">Ничего не найдено</h5>
                <p class="text-muted mb-0">По запросу "<strong>${searchTerm}</strong>" не найдено ни одного теста</p>
                <p class="text-muted mt-2"><small>Попробуйте изменить поисковый запрос</small></p>
            </div>
        </div>
    `;
}

/**
 * Показывает сообщение об ошибке
 * @param {HTMLElement} container - Контейнер
 * @param {string} errorMessage - Текст ошибки
 */
function showErrorMessage(container, errorMessage) {
    container.innerHTML = `
        <div class="col-12">
            <div class="alert alert-danger text-center">
                <i class="fas fa-exclamation-triangle me-2"></i>
                ${errorMessage}
            </div>
        </div>
    `;
}

/**
 * Восстанавливает оригинальное состояние страницы
 * @param {HTMLElement} container - Контейнер
 * @param {string} originalContent - Оригинальный HTML
 * @param {HTMLElement} paginationNav - Элемент пагинации
 */
function restoreOriginalState(container, originalContent, paginationNav) {
    if (originalContent) {
        container.innerHTML = originalContent;
        
        // Показываем пагинацию обратно
        if (paginationNav) {
            paginationNav.style.display = 'block';
        }
        
        // Переинициализируем обработчики
        initializeMainPageHandlers();
    }
}