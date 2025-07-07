document.addEventListener('DOMContentLoaded', () => {
    // --- Переключение между курсами ---
    const toggleCoursesBtn = document.getElementById('toggle-courses-btn');
    const unfinishedBlock = document.getElementById('unfinished-courses');
    const finishedBlock = document.getElementById('finished-courses');

    if (toggleCoursesBtn) {
        toggleCoursesBtn.addEventListener('click', () => {
            const isFinishedVisible = finishedBlock.style.display === 'block';
            finishedBlock.style.display = isFinishedVisible ? 'none' : 'block';
            unfinishedBlock.style.display = isFinishedVisible ? 'block' : 'none';
            toggleCoursesBtn.textContent = isFinishedVisible 
                ? 'Показать завершенные курсы' 
                : 'Показать незавершенные курсы';
        });
    }

    // --- Элементы для работы с тестами ---
    const toggleQuizzesBtn = document.getElementById('toggle-quizzes-btn');
    const quizzesSection = document.querySelector('.quiz-history-container');
    
    // --- Инициализация состояния тестов ---
    let isQuizzesVisible = localStorage.getItem('quizzesVisible') === 'true';
    if (quizzesSection) {
        quizzesSection.style.display = isQuizzesVisible ? 'block' : 'none';
        if (toggleQuizzesBtn) {
            toggleQuizzesBtn.textContent = isQuizzesVisible ? 'Скрыть тесты' : 'Показать тесты';
        }
    }

    // --- Обработчик кнопки тестов ---
    if (toggleQuizzesBtn && quizzesSection) {
        toggleQuizzesBtn.addEventListener('click', () => {
            isQuizzesVisible = !isQuizzesVisible;
            quizzesSection.style.display = isQuizzesVisible ? 'block' : 'none';
            toggleQuizzesBtn.textContent = isQuizzesVisible ? 'Скрыть тесты' : 'Показать тесты';
            localStorage.setItem('quizzesVisible', isQuizzesVisible);
        });
    }

    // --- Пагинация с AJAX ---
    if (quizzesSection) {
        quizzesSection.addEventListener('click', async (e) => {
            const target = e.target.closest('.page-link');
            if (!target) return;
            
            e.preventDefault();
            
            // Активируем блок если скрыт
            if (!isQuizzesVisible) {
                isQuizzesVisible = true;
                quizzesSection.style.display = 'block';
                if (toggleQuizzesBtn) {
                    toggleQuizzesBtn.textContent = 'Скрыть тесты';
                    localStorage.setItem('quizzesVisible', true);
                }
            }

            const url = new URL(target.href);
            const page = url.searchParams.get('page');
            
            try {
                const response = await fetch(`?page=${page}`, {
                    headers: {'X-Requested-With': 'XMLHttpRequest'}
                });
                const html = await response.text();
                
                document.getElementById('quiz-history-content').innerHTML = html;
                history.pushState(null, null, `?page=${page}`);
            } catch (error) {
                console.error('Ошибка загрузки:', error);
                document.getElementById('quiz-history-content').innerHTML = `
                    <div class="alert alert-danger mt-3">
                        Ошибка загрузки данных. Попробуйте обновить страницу.
                    </div>
                `;
            }
        });
    }

    // --- Обработка истории браузера ---
    window.addEventListener('popstate', async () => {
        const urlParams = new URLSearchParams(window.location.search);
        const page = urlParams.get('page') || 1;
        
        try {
            const response = await fetch(`?page=${page}`, {
                headers: {'X-Requested-With': 'XMLHttpRequest'}
            });
            const html = await response.text();
            
            if (quizzesSection) {
                document.getElementById('quiz-history-content').innerHTML = html;
                quizzesSection.style.display = 'block';
                isQuizzesVisible = true;
                if (toggleQuizzesBtn) {
                    toggleQuizzesBtn.textContent = 'Скрыть тесты';
                    localStorage.setItem('quizzesVisible', true);
                }
            }
        } catch (error) {
            console.error('Ошибка загрузки:', error);
        }
    });

    // --- Переключение режимов редактирования профиля ---
    const editProfileBtn = document.getElementById('edit-profile-btn');
    const cancelEditBtn = document.getElementById('cancel-edit-btn');
    const editProfileForm = document.getElementById('edit-profile-form');
    const progressBar = document.querySelector('.progress-bar-user');

    if (editProfileBtn && cancelEditBtn) {
        editProfileBtn.addEventListener('click', function() {
            editProfileForm.style.display = 'block';
            editProfileBtn.style.display = 'none';
            if (toggleCoursesBtn) toggleCoursesBtn.style.display = 'none';
            if (toggleQuizzesBtn) toggleQuizzesBtn.style.display = 'none';
            if (progressBar) progressBar.style.display = 'none';
        });

        cancelEditBtn.addEventListener('click', function(event) {
            event.preventDefault();
            editProfileForm.style.display = 'none';
            editProfileBtn.style.display = 'block';
            if (toggleCoursesBtn) toggleCoursesBtn.style.display = 'block';
            if (toggleQuizzesBtn) toggleQuizzesBtn.style.display = 'block';
            if (progressBar) progressBar.style.display = 'block';
        });
    }
});

// --- Показ/скрытие пароля ---
document.addEventListener('DOMContentLoaded', function() {
    const passwordInput = document.querySelector('input[type="password"], input[type="text"][name*="password"]');
    if (!passwordInput) return;

    // SVG для открытого и закрытого глаза
    const eyeOpen = `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" style="vertical-align:middle;" fill="none" stroke="#555" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="12" rx="9" ry="5"/><circle cx="12" cy="12" r="2"/></svg>`;
    const eyeClosed = `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" style="vertical-align:middle;" fill="none" stroke="#555" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="12" rx="9" ry="5"/><path d="M3 3l18 18"/></svg>`;

    // Обёртка для позиционирования
    const wrapper = document.createElement('div');
    wrapper.style.position = 'relative';
    passwordInput.parentNode.insertBefore(wrapper, passwordInput);
    wrapper.appendChild(passwordInput);

    // Кнопка-глаз
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.innerHTML = eyeClosed;
    btn.style.position = 'absolute';
    btn.style.right = '8px';
    btn.style.top = '50%';
    btn.style.transform = 'translateY(-50%)';
    btn.style.border = 'none';
    btn.style.background = 'none';
    btn.style.cursor = 'pointer';
    btn.style.padding = '0';
    btn.style.height = '24px';
    btn.style.width = '24px';

    wrapper.appendChild(btn);

    let shown = false;
    btn.addEventListener('click', function(e) {
        e.preventDefault();
        shown = !shown;
        passwordInput.type = shown ? 'text' : 'password';
        btn.innerHTML = shown ? eyeOpen : eyeClosed;
    });
});














// // --- Переключение между курсами --- old
// const toggleCoursesBtn = document.getElementById('toggle-courses-btn');
// const unfinishedBlock = document.getElementById('unfinished-courses');
// const finishedBlock = document.getElementById('finished-courses');

// toggleCoursesBtn.addEventListener('click', () => {
//     const isFinishedVisible = finishedBlock.style.display === 'block';
//     finishedBlock.style.display = isFinishedVisible ? 'none' : 'block';
//     unfinishedBlock.style.display = isFinishedVisible ? 'block' : 'none';
//     toggleCoursesBtn.textContent = isFinishedVisible 
//         ? 'Показать завершенные курсы' 
//         : 'Показать незавершенные курсы';
// });

// // --- Переключение между тестами и их отображением ---
// const toggleQuizzesBtn = document.getElementById('toggle-quizzes-btn');
// // Найдём нужный блок с тестами (вторая .container.mt-4)
// const containers = document.querySelectorAll('.container.mt-4');
// const quizzesSection = containers[1]; // второй блок - история тестов

// // По умолчанию скрываем блок с тестами
// quizzesSection.style.display = 'none';
// toggleQuizzesBtn.textContent = 'Показать тесты';

// toggleQuizzesBtn.addEventListener('click', () => {
//     const isVisible = quizzesSection.style.display === 'block';
//     quizzesSection.style.display = isVisible ? 'none' : 'block';
//     toggleQuizzesBtn.textContent = isVisible ? 'Показать тесты' : 'Скрыть тесты';
// });

// // --- Переключение режимов редактирования профиля ---
// const editProfileBtn = document.getElementById('edit-profile-btn');
// const cancelEditBtn = document.getElementById('cancel-edit-btn');
// const editProfileForm = document.getElementById('edit-profile-form');
// const progressBar = document.querySelector('.progress-bar-user');

// editProfileBtn.addEventListener('click', function() {
//     editProfileForm.style.display = 'block';
//     editProfileBtn.style.display = 'none';
//     toggleCoursesBtn.style.display = 'none';
//     toggleQuizzesBtn.style.display = 'none';
//     progressBar.style.display = 'none';
// });

// cancelEditBtn.addEventListener('click', function(event) {
//     event.preventDefault();
//     editProfileForm.style.display = 'none';
//     editProfileBtn.style.display = 'block';
//     toggleCoursesBtn.style.display = 'block';
//     toggleQuizzesBtn.style.display = 'block';
//     progressBar.style.display = 'block';
// });
