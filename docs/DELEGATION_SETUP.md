# Быстрый старт системы делегирования

## 1. Применить миграции

```bash
cd /opt/pearls-site-django/myproject
source ../.venv/bin/activate
python manage.py migrate delegation
```

## 2. Создать суперпользователя (если еще не создан)

```bash
python manage.py createsuperuser
```

## 3. Запустить сервер

```bash
python manage.py runserver
```

## 4. Доступ к системе

- **Пользовательская панель**: http://localhost:8000/delegation/
- **Административная панель**: http://localhost:8000/admin/delegation/delegation/
- **Главная панель управления**: http://localhost:8000/builder/dashboard/

## 5. Настройка автоматического завершения делегирований

Для автоматического завершения истекших делегирований настройте cron:

```bash
# Открыть crontab
crontab -e

# Добавить строку (запуск каждый день в 00:05)
5 0 * * * cd /opt/pearls-site-django/myproject && source ../.venv/bin/activate && python manage.py complete_expired_delegations >> /var/log/delegation_cron.log 2>&1
```

Или запустить вручную:
```bash
python manage.py complete_expired_delegations
```

## Использование

### Создание делегирования:
1. Перейдите в панель управления `/builder/dashboard/`
2. Нажмите "Панель управления делегированием"
3. Нажмите кнопку "Делегировать права"
4. Заполните форму и отправьте запрос

### Подтверждение делегирования:
1. Зайдите под пользователем, которому делегировали права
2. Перейдите в панель делегирования
3. Откройте вкладку "Входящие"
4. Нажмите "Принять" или "Отклонить"

### Отмена делегирования:
1. Откройте вкладку "Исходящие"
2. Найдите нужное делегирование
3. Нажмите "Отменить"

## Иконка для кнопки

Используется иконка FontAwesome `fa-user-shield`:
```html
<i class="fas fa-user-shield"></i>
```

## Проверка работы

Проверьте, что:
- ✅ Миграции применены: `python manage.py showmigrations delegation`
- ✅ Приложение добавлено в INSTALLED_APPS
- ✅ URLs подключены в главном urls.py
- ✅ Нет ошибок в консоли Django

## Особенности

- В пользовательском интерфейсе отображаются только делегирования за последние 30 дней
- Полная история доступна администраторам в Django Admin
- Система автоматически проверяет права доступа
- Нельзя делегировать права самому себе

## Дополнительная информация

Подробная документация: `/opt/pearls-site-django/myproject/apps/delegation/README.md`

