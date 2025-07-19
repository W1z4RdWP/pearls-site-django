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
