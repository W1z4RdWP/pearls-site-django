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

    if (editProfileBtn && cancelEditBtn && editProfileForm) {
        editProfileBtn.addEventListener('click', function() {
            editProfileForm.style.display = 'block';
            editProfileBtn.style.display = 'none';
            if (toggleCoursesBtn) toggleCoursesBtn.style.display = 'none';
            if (toggleQuizzesBtn) toggleQuizzesBtn.style.display = 'none';
            if (progressBar) progressBar.style.display = 'none';
            if (gamificationSection) gamificationSection.style.display = 'none';
        });

        cancelEditBtn.addEventListener('click', function(event) {
            event.preventDefault();
            editProfileForm.style.display = 'none';
            editProfileBtn.style.display = 'block';
            if (toggleCoursesBtn) toggleCoursesBtn.style.display = 'block';
            if (toggleQuizzesBtn) toggleQuizzesBtn.style.display = 'block';
            if (progressBar) progressBar.style.display = 'block';
            if (gamificationSection) gamificationSection.style.display = 'block';
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
        toggleCoursesProgressBtn.innerHTML = '📂';
    } else {
        profileCoursesProgress.style.display = 'block';
        toggleCoursesProgressBtn.innerHTML = '📁';
    }
}

// --- Работа с камерой для аватара ---
document.addEventListener('DOMContentLoaded', function() {
    const cameraBtn = document.getElementById('camera-btn');
    const cameraModal = document.getElementById('cameraModal');
    const video = document.getElementById('camera-video');
    const canvas = document.getElementById('camera-canvas');
    const captureBtn = document.getElementById('camera-capture');
    const retryBtn = document.getElementById('camera-retry');
    const useBtn = document.getElementById('camera-use');
    const switchBtn = document.getElementById('camera-switch');
    const previewDiv = document.getElementById('photo-preview');
    const previewImage = document.getElementById('preview-image');
    const errorDiv = document.getElementById('camera-error');
    const imageInput = document.getElementById('id_image');
    const httpsWarning = document.getElementById('https-warning');
    
    let stream = null;
    let capturedImageBlob = null;
    let currentFacingMode = 'user'; // 'user' для фронтальной, 'environment' для задней
    let availableCameras = [];

    // Универсальная функция получения доступа к камере
    async function getUserMedia(constraints) {
        // Современный API
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
            return await navigator.mediaDevices.getUserMedia(constraints);
        }
        
        // Fallback для старых браузеров
        const getUserMedia = navigator.getUserMedia || 
                            navigator.webkitGetUserMedia || 
                            navigator.mozGetUserMedia;
        
        if (getUserMedia) {
            return new Promise((resolve, reject) => {
                getUserMedia.call(navigator, constraints, resolve, reject);
            });
        }
        
        throw new Error('getUserMedia не поддерживается');
    }

    // Получение списка доступных камер
    async function getAvailableCameras() {
        try {
            if (navigator.mediaDevices && navigator.mediaDevices.enumerateDevices) {
                const devices = await navigator.mediaDevices.enumerateDevices();
                availableCameras = devices.filter(device => device.kind === 'videoinput');
                return availableCameras.length > 1; // Возвращаем true если есть несколько камер
            }
        } catch (error) {
            console.log('Не удалось получить список камер:', error);
        }
        return false;
    }

    // Запуск камеры с указанными параметрами
    async function startCamera(facingMode = 'user') {
        const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
        
        // Сначала пробуем с подробными настройками
        let constraints = {
            video: isMobile ? {
                facingMode: facingMode,
                width: { ideal: 480 },
                height: { ideal: 640 }
            } : {
                width: { ideal: 640 }, 
                height: { ideal: 480 },
                facingMode: facingMode
            }
        };
        
        try {
            return await getUserMedia(constraints);
        } catch (error) {
            console.log('Попытка с упрощенными настройками...', error);
            
            // Fallback: пробуем с минимальными настройками
            constraints = {
                video: {
                    facingMode: facingMode
                }
            };
            
            try {
                return await getUserMedia(constraints);
            } catch (error2) {
                console.log('Попытка без facingMode...', error2);
                
                // Последняя попытка: совсем простые настройки
                constraints = {
                    video: true
                };
                
                return await getUserMedia(constraints);
            }
        }
    }

    // Открытие камеры
    if (cameraBtn) {
        cameraBtn.addEventListener('click', async function() {
            try {
                // Проверяем доступность нескольких камер
                const hasMultipleCameras = await getAvailableCameras();
                if (hasMultipleCameras && switchBtn) {
                    switchBtn.style.display = 'inline-block';
                }
                
                stream = await startCamera(currentFacingMode);
                video.srcObject = stream;
                
                // Показываем модальное окно
                const modal = new bootstrap.Modal(cameraModal);
                modal.show();
                
                // Сбрасываем состояние
                resetCameraState();
                
            } catch (error) {
                console.error('Ошибка доступа к камере:', error);
                
                let errorMessage = 'Не удалось получить доступ к камере. ';
                
                if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
                    errorMessage += 'Разрешите доступ к камере в настройках браузера.';
                } else if (error.name === 'NotFoundError' || error.name === 'DevicesNotFoundError') {
                    errorMessage += 'Камера не найдена на устройстве.';
                } else if (error.name === 'NotSupportedError') {
                    errorMessage += 'Камера не поддерживается в данном браузере.';
                } else if (error.name === 'NotReadableError' || error.name === 'TrackStartError') {
                    errorMessage += 'Камера уже используется другим приложением.';
                } else {
                    errorMessage += 'Попробуйте перезагрузить страницу или использовать другой браузер.';
                }
                
                showError(errorMessage);
            }
        });
    }

    // Переключение камеры
    if (switchBtn) {
        switchBtn.addEventListener('click', async function() {
            try {
                // Останавливаем текущий поток
                stopCamera();
                
                // Переключаем режим камеры
                currentFacingMode = currentFacingMode === 'user' ? 'environment' : 'user';
                
                // Запускаем новую камеру
                stream = await startCamera(currentFacingMode);
                video.srcObject = stream;
                
            } catch (error) {
                console.error('Ошибка переключения камеры:', error);
                showError('Не удалось переключить камеру. Попробуйте еще раз.');
                
                // Возвращаем предыдущий режим
                currentFacingMode = currentFacingMode === 'user' ? 'environment' : 'user';
            }
        });
    }

    // Съемка фото
    if (captureBtn) {
        captureBtn.addEventListener('click', function() {
            if (stream) {
                // Устанавливаем размеры canvas равными размерам видео
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                
                // Рисуем кадр из видео на canvas
                const ctx = canvas.getContext('2d');
                ctx.drawImage(video, 0, 0);
                
                // Конвертируем в blob
                canvas.toBlob(function(blob) {
                    capturedImageBlob = blob;
                    
                    // Показываем превью
                    const url = URL.createObjectURL(blob);
                    previewImage.src = url;
                    
                    // Переключаем интерфейс
                    video.style.display = 'none';
                    previewDiv.style.display = 'block';
                    captureBtn.style.display = 'none';
                    retryBtn.style.display = 'inline-block';
                    useBtn.style.display = 'inline-block';
                    
                }, 'image/jpeg', 0.8);
            }
        });
    }

    // Переснять фото
    if (retryBtn) {
        retryBtn.addEventListener('click', function() {
            resetCameraState();
        });
    }

    // Использовать снятое фото
    if (useBtn) {
        useBtn.addEventListener('click', function() {
            if (capturedImageBlob) {
                // Создаем File объект из blob
                const file = new File([capturedImageBlob], 'camera-photo.jpg', { 
                    type: 'image/jpeg' 
                });
                
                // Создаем DataTransfer для установки файла в input
                const dataTransfer = new DataTransfer();
                dataTransfer.items.add(file);
                imageInput.files = dataTransfer.files;
                
                // Показываем уведомление
                showSuccess('Фото с камеры выбрано для загрузки');
                
                // Закрываем модальное окно
                const modal = bootstrap.Modal.getInstance(cameraModal);
                modal.hide();
            }
        });
    }

    // Очистка ресурсов при закрытии модального окна
    if (cameraModal) {
        cameraModal.addEventListener('hidden.bs.modal', function() {
            stopCamera();
            resetCameraState();
        });
    }

    // Функция сброса состояния камеры
    function resetCameraState() {
        video.style.display = 'block';
        previewDiv.style.display = 'none';
        captureBtn.style.display = 'inline-block';
        retryBtn.style.display = 'none';
        useBtn.style.display = 'none';
        errorDiv.style.display = 'none';
        
        // Показываем кнопку переключения только если есть несколько камер
        if (switchBtn && availableCameras.length > 1) {
            switchBtn.style.display = 'inline-block';
        }
        
        capturedImageBlob = null;
        
        if (previewImage.src) {
            URL.revokeObjectURL(previewImage.src);
            previewImage.src = '';
        }
    }

    // Функция остановки камеры
    function stopCamera() {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
            stream = null;
            video.srcObject = null;
        }
    }

    // Функция показа ошибки
    function showError(message) {
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
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

    // Проверяем поддержку getUserMedia с улучшенной совместимостью
    function checkCameraSupport() {
        // Проверяем HTTPS (обязательно для камеры в большинстве браузеров)
        const isSecure = location.protocol === 'https:' || location.hostname === 'localhost' || location.hostname === '127.0.0.1';
        
        if (!isSecure) {
            if (httpsWarning) {
                httpsWarning.style.display = 'block';
            }
            return false;
        }
        
        // Проверяем современный API
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
            return true;
        }
        
        // Проверяем старые API для совместимости
        if (navigator.getUserMedia || navigator.webkitGetUserMedia || navigator.mozGetUserMedia) {
            return true;
        }
        
        // Проверяем через MediaDevices polyfill
        if (window.MediaStreamTrack && window.MediaStreamTrack.getSources) {
            return true;
        }
        
        return false;
    }
    
    if (!checkCameraSupport()) {
        if (cameraBtn) {
            cameraBtn.disabled = true;
            const isSecure = location.protocol === 'https:' || location.hostname === 'localhost' || location.hostname === '127.0.0.1';
            
            if (!isSecure) {
                cameraBtn.innerHTML = '<i class="fa fa-lock"></i> Требуется HTTPS';
                cameraBtn.title = 'Для работы камеры требуется защищенное соединение HTTPS';
            } else {
                cameraBtn.innerHTML = '<i class="fa fa-camera-slash"></i> Камера недоступна';
                cameraBtn.title = 'Ваш браузер не поддерживает доступ к камере';
            }
        }
    }
});



