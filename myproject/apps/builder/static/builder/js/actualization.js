// --- Логика модалки актуализации ---
function openActualizeModal() {
    const modal = document.getElementById('actualize-modal');
    if (!modal) return;

    // Загружаем разрешенные роли для урока
    const lessonId = document.getElementById('actualize-lesson-id').value;
    if (lessonId) {
        fetch(`/user_management/lessons/${lessonId}/allowed-roles/`)
            .then(response => response.json())
            .then(data => {
                const roleSelect = document.getElementById('actualize-role');
                if (roleSelect) {
                    // Очищаем список, оставляя только первый option
                    roleSelect.innerHTML = '<option value="">— выберите роль —</option>';

                    data.allowed_roles.forEach(role => {
                        const option = document.createElement('option');
                        option.value = role.id;
                        option.textContent = role.name;
                        roleSelect.appendChild(option);
                    });

                    // Автозаполнение роли из предыдущей версии (после загрузки ролей)
                    if (window.previousRoleId && window.previousRoleId !== null) {
                        roleSelect.value = window.previousRoleId;
                        // Триггерим событие change для загрузки пользователей
                        const event = new Event('change');
                        roleSelect.dispatchEvent(event);
                    } else {
                        // Если нет предыдущей роли, все равно вызываем валидацию
                        validateActualizeForm();
                    }
                }
            })
            .catch(error => {
                console.error('Ошибка загрузки разрешенных ролей:', error);
                validateActualizeForm();
            });
    } else {
        // Если нет lessonId, все равно вызываем валидацию
        validateActualizeForm();
    }

    // Заполняем поля
    const createdInput = document.getElementById('actualize-created');
    const versionInput = document.getElementById('actualize-version');
    const periodInput = document.getElementById('actualize-period');
    const nextUpdateInput = document.getElementById('actualize-next-update');
    const roleSelect = document.getElementById('actualize-role');
    const responsibleFio = document.getElementById('actualize-responsible-fio');
    const confirmBtn = document.getElementById('actualize-confirm-btn');
    const closeBtn = document.getElementById('actualize-modal-close');
    const form = document.getElementById('actualize-form');
    if (!createdInput || !versionInput || !periodInput || !nextUpdateInput || !roleSelect || !responsibleFio || !confirmBtn || !closeBtn || !form) {
        console.error('Один из элементов модалки не найден!');
        return;
    }
    // Получаем данные из последней строки истории (или из блока)
    let last = null;
    if (window._lessonVersions && window._lessonVersions.length) {
        last = window._lessonVersions[0];
    }
    // Альтернативно — из actualization_history, если есть
    let historyRows = document.querySelectorAll('#actualization-history-dropdown tbody tr');
    if (historyRows.length) {
        const tds = historyRows[0].querySelectorAll('td');
        // created, version, period, next_update, role, fio
        createdInput.value = tds[0]?.textContent.trim() || '';
        versionInput.value = tds[1]?.textContent.replace(/^v/, '').trim() || '';
        periodInput.value = tds[2]?.textContent.trim() || '90';
        nextUpdateInput.value = tds[3]?.textContent.trim().split('.').reverse().join('-') || '';
    } else {
        // fallback
        const today = (window._actualizationToday || new Date()).toISOString().slice(0, 10);
        createdInput.value = today.split('-').reverse().join('.');
        versionInput.value = '1';
        periodInput.value = '90';
        nextUpdateInput.value = today;
    }
    // Инициализируем поля роли и ответственного
    responsibleFio.value = '';

    // Функция валидации формы
    function validateActualizeForm() {
        let valid = true;
        const days = parseInt(periodInput.value, 10);
        const d2 = new Date(nextUpdateInput.value);
        if (!days || days < 1 || days > 180) valid = false;
        if (!nextUpdateInput.value) valid = false;
        if ((d2 - today) / (1000 * 60 * 60 * 24) < 0 || (d2 - today) / (1000 * 60 * 60 * 24) > 180) valid = false;
        if (!roleSelect.value) valid = false;
        if (!responsibleFio.value) valid = false;
        confirmBtn.disabled = !valid;
    }

    // Автозаполнение роли из предыдущей версии (перемещаем после добавления обработчиков)

    // Ограничения для даты
    const today = new Date();
    const maxDate = new Date(today.getTime() + 180 * 24 * 60 * 60 * 1000);
    nextUpdateInput.min = today.toISOString().slice(0, 10);
    nextUpdateInput.max = maxDate.toISOString().slice(0, 10);

    // При изменении периода — меняем дату
    periodInput.oninput = function () {
        let days = parseInt(periodInput.value, 10);
        if (isNaN(days) || days < 1) days = 1;
        if (days > 180) days = 180;
        periodInput.value = days;
        const d = new Date();
        d.setDate(d.getDate() + days);
        nextUpdateInput.value = d.toISOString().slice(0, 10);
        validateActualizeForm();
    };
    // При изменении даты — меняем период
    nextUpdateInput.oninput = function () {
        const d1 = today;
        const d2 = new Date(nextUpdateInput.value);
        let diff = Math.round((d2 - d1) / (1000 * 60 * 60 * 24));
        if (diff < 1) diff = 1;
        if (diff > 180) diff = 180;
        periodInput.value = diff;
        validateActualizeForm();
    };

    // Обработчик изменения роли
    roleSelect.addEventListener('change', function () {
        const roleId = this.value;

        if (roleId) {
            // Загружаем пользователей с данной ролью
            fetch(`/user_management/roles/${roleId}/users/`)
                .then(response => response.json())
                .then(data => {
                    responsibleFio.value = '';

                    // Ищем ответственного пользователя
                    const responsibleUser = data.users.find(user => user.is_responsible);
                    if (responsibleUser) {
                        responsibleFio.value = responsibleUser.full_name;
                    }

                    validateActualizeForm();
                })
                .catch(error => {
                    console.error('Ошибка загрузки пользователей:', error);
                    responsibleFio.value = '';
                    validateActualizeForm();
                });
        } else {
            responsibleFio.value = '';
            validateActualizeForm();
        }
    });

    // Валидация формы
    periodInput.oninput(); // триггерим заполнение даты и валидацию

    // Закрытие
    closeBtn.onclick = function () { modal.style.display = 'none'; };
    modal.onclick = function (e) { if (e.target === modal) modal.style.display = 'none'; };

    // Сабмит
    form.onsubmit = function (ev) {
        ev.preventDefault();
        confirmBtn.disabled = true;
        // Собираем данные
        const id = document.getElementById('actualize-lesson-id')?.value;
        if (!id) { alert('Не удалось определить ID урока'); return; }
        // Получаем ID ответственного пользователя из выбранной роли
        const roleId = roleSelect.value;
        fetch(`/user_management/roles/${roleId}/users/`)
            .then(response => response.json())
            .then(userData => {
                const responsibleUser = userData.users.find(user => user.is_responsible);
                if (!responsibleUser) {
                    alert('Для выбранной роли не найден ответственный пользователь');
                    confirmBtn.disabled = false;
                    return;
                }

                return fetch('/builder/actualize_version/', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': (document.querySelector('[name=csrfmiddlewaretoken]') || {}).value || '',
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        lesson_id: id,
                        period: parseInt(periodInput.value, 10),
                        next_update: nextUpdateInput.value,
                        responsible_id: responsibleUser.id
                    })
                });
            })
            .then(data => {
                if (data.error) {
                    alert('Ошибка: ' + data.error);
                    confirmBtn.disabled = false;
                    return;
                }
                modal.style.display = 'none';
                // Обновляем detail-блок (AJAX reload)
                const lessonId = id;
                fetch(`/builder/lesson/${lessonId}/?ajax=1`)
                    .then(r => r.text())
                    .then(html => {
                        document.getElementById('detail').innerHTML = html;
                        initActualizationHistoryDropdown();
                    });
            })
            .catch(() => {
                alert('Ошибка сети');
                confirmBtn.disabled = false;
            });
    };
    modal.style.display = 'flex';
}

