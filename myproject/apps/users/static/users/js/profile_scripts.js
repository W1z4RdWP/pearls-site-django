document.addEventListener('DOMContentLoaded', () => {
    // --- Переключение между курсами ---
    const toggleCoursesBtn = document.getElementById('toggle-courses-btn');
    const unfinishedBlock = document.getElementById('unfinished-courses');
    const finishedBlock = document.getElementById('finished-courses');

    if (toggleCoursesBtn && unfinishedBlock && finishedBlock) {
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
    const gamificationSection = document.getElementById('gamification-section');
    const supportBtn = document.getElementById('support-btn');
    const mailBtn = document.getElementById('mail-btn');

    if (editProfileBtn && cancelEditBtn && editProfileForm) {
        editProfileBtn.addEventListener('click', function() {
            editProfileForm.style.display = 'block';
            editProfileBtn.style.display = 'none';
            if (toggleCoursesBtn) toggleCoursesBtn.style.display = 'none';
            if (toggleQuizzesBtn) toggleQuizzesBtn.style.display = 'none';
            if (progressBar) progressBar.style.display = 'none';
            if (gamificationSection) gamificationSection.style.display = 'none';
            if (supportBtn) supportBtn.style.display = 'none';
            if (mailBtn) mailBtn.style.display = 'none';
        });

        cancelEditBtn.addEventListener('click', function(event) {
            event.preventDefault();
            editProfileForm.style.display = 'none';
            editProfileBtn.style.display = 'block';
            if (toggleCoursesBtn) toggleCoursesBtn.style.display = 'block';
            if (toggleQuizzesBtn) toggleQuizzesBtn.style.display = 'block';
            if (progressBar) progressBar.style.display = 'block';
            if (gamificationSection) gamificationSection.style.display = 'block';
            if (supportBtn) supportBtn.style.display = 'block';
            if (mailBtn) mailBtn.style.display = 'block';
        });
    }

    // --- Геймификация: Обработка бейджей и достижений ---
    const showAllBadgesBtn = document.getElementById('show-all-badges');
    const showAllAchievementsBtn = document.getElementById('show-all-achievements');
    
    if (showAllBadgesBtn) {
        showAllBadgesBtn.addEventListener('click', async () => {
            try {
                const response = await fetch('/users/profile/all-badges/', {
                    headers: {'X-Requested-With': 'XMLHttpRequest'}
                });
                const html = await response.text();
                
                // Создаем модальное окно
                const modal = document.createElement('div');
                modal.className = 'modal-overlay';
                modal.innerHTML = `
                    <div class="modal-content">
                        <div class="modal-header">
                            <h3>Все бейджи</h3>
                            <button class="modal-close">&times;</button>
                        </div>
                        <div class="modal-body">
                            ${html}
                        </div>
                    </div>
                `;
                
                document.body.appendChild(modal);
                
                // Обработчик закрытия
                modal.addEventListener('click', (e) => {
                    if (e.target === modal || e.target.classList.contains('modal-close')) {
                        document.body.removeChild(modal);
                    }
                });
                
            } catch (error) {
                console.error('Ошибка загрузки бейджей:', error);
                alert('Ошибка загрузки бейджей. Попробуйте позже.');
            }
        });
    }
    
    if (showAllAchievementsBtn) {
        showAllAchievementsBtn.addEventListener('click', async () => {
            try {
                const response = await fetch('/users/profile/all-achievements/', {
                    headers: {'X-Requested-With': 'XMLHttpRequest'}
                });
                const html = await response.text();
                
                // Создаем модальное окно
                const modal = document.createElement('div');
                modal.className = 'modal-overlay';
                modal.innerHTML = `
                    <div class="modal-content">
                        <div class="modal-header">
                            <h3>Все достижения</h3>
                            <button class="modal-close">&times;</button>
                        </div>
                        <div class="modal-body">
                            ${html}
                        </div>
                    </div>
                `;
                
                document.body.appendChild(modal);
                
                // Обработчик закрытия
                modal.addEventListener('click', (e) => {
                    if (e.target === modal || e.target.classList.contains('modal-close')) {
                        document.body.removeChild(modal);
                    }
                });
                
            } catch (error) {
                console.error('Ошибка загрузки достижений:', error);
                alert('Ошибка загрузки достижений. Попробуйте позже.');
            }
        });
    }
    
    // Анимация для бейджей и достижений
    const badgeItems = document.querySelectorAll('.badge-item, .achievement-item');
    badgeItems.forEach(item => {
        item.addEventListener('mouseenter', () => {
            item.style.transform = 'translateY(-3px) scale(1.05)';
        });
        
        item.addEventListener('mouseleave', () => {
            item.style.transform = 'translateY(0) scale(1)';
        });
    });
    
    // Анимация для бейджа DASCOIN
    const dascoinBadge = document.querySelector('.dascoin-badge');
    if (dascoinBadge) {
        dascoinBadge.addEventListener('mouseenter', () => {
            dascoinBadge.style.transform = 'scale(1.1)';
            dascoinBadge.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.3)';
        });
        
        dascoinBadge.addEventListener('mouseleave', () => {
            dascoinBadge.style.transform = 'scale(1)';
            dascoinBadge.style.boxShadow = '0 2px 8px rgba(0, 0, 0, 0.2)';
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


// --- Отключение блока прогресса курсов ---
const toggleCoursesProgressBtn = document.getElementById('toggle-courses-progress-btn');
const profileCoursesProgress = document.getElementById('profile-courses-progress');

function toggleCoursesProgress() {
    if (profileCoursesProgress.style.display === 'block') {
        profileCoursesProgress.style.display = 'none';
        toggleCoursesProgressBtn.innerHTML = '📁';
    } else {
        profileCoursesProgress.style.display = 'block';
        toggleCoursesProgressBtn.innerHTML = '📂';
    }
}

// --- Работа с камерой для аватара (встроенное приложение) ---
document.addEventListener('DOMContentLoaded', function() {
    const cameraBtn = document.getElementById('camera-btn');
    const cameraInput = document.getElementById('camera-input');
    const imageInput = document.getElementById('id_image');
    const cameraPreview = document.getElementById('camera-preview');
    const cameraPreviewImg = document.getElementById('camera-preview-img');
    const useCameraPhotoBtn = document.getElementById('use-camera-photo');
    const retakePhotoBtn = document.getElementById('retake-photo');

    // Открытие встроенной камеры устройства
    if (cameraBtn && cameraInput) {
        cameraBtn.addEventListener('click', function() {
            cameraInput.click();
        });
    }

    // Обработка выбранного фото с камеры
    if (cameraInput) {
        cameraInput.addEventListener('change', function(event) {
            const file = event.target.files[0];
            if (file) {
                // Показываем превью
                const reader = new FileReader();
                reader.onload = function(e) {
                    cameraPreviewImg.src = e.target.result;
                    cameraPreview.style.display = 'block';
                };
                reader.readAsDataURL(file);
            }
        });
    }

    // Использование снятого фото
    if (useCameraPhotoBtn) {
        useCameraPhotoBtn.addEventListener('click', function() {
            const file = cameraInput.files[0];
            if (file) {
                // Передаем файл в основное поле загрузки
                const dataTransfer = new DataTransfer();
                dataTransfer.items.add(file);
                imageInput.files = dataTransfer.files;
                
                // Показываем уведомление
                showSuccess('Фото с камеры выбрано для загрузки');
                
                // Скрываем превью
                cameraPreview.style.display = 'none';
            }
        });
    }

    // Переснять фото
    if (retakePhotoBtn) {
        retakePhotoBtn.addEventListener('click', function() {
            cameraInput.value = '';
            cameraPreview.style.display = 'none';
            cameraInput.click();
        });
    }

    // Функция показа успешного сообщения
    function showSuccess(message) {
        // Создаем временное уведомление
        const alert = document.createElement('div');
        alert.className = 'alert alert-success alert-dismissible fade show';
        alert.style.position = 'fixed';
        alert.style.top = '20px';
        alert.style.right = '20px';
        alert.style.zIndex = '9999';
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(alert);
        
        // Автоматически удаляем через 3 секунды
        setTimeout(() => {
            if (alert.parentNode) {
                alert.parentNode.removeChild(alert);
            }
        }, 3000);
    }
});



