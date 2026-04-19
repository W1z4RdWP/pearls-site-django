# Web Push (PWA) уведомления в messenger

Пуши работают поверх стандартного Web Push API: сервер шлёт зашифрованный
payload в push-сервис браузера (FCM/Mozilla/Apple), а **service worker**
показывает OS-уведомление — даже если у пользователя закрыта вкладка сайта.

## Архитектура

```
Browser                                       Server (messenger)
-------                                       ------------------
chat_room.html
 └─ push-notifications.js  ──subscribe──▶  POST /messenger/push/subscribe/
     (PushManager)                           → WebPushSubscription в БД
 └─ service-worker.js
     (push event → OS notification)

ChatRoomConsumer (WS)
 └─ новое сообщение
     └─ create_notifications_for_participants
         └─ push.send_push_to_user(user, payload)
             └─ pywebpush → push-сервис браузера → service-worker
```

## Компоненты

| Файл | Назначение |
|---|---|
| `models.py :: WebPushSubscription` | endpoint + ключи (p256dh/auth) на одно устройство пользователя |
| `push.py` | `send_push_to_user(user, payload)`, работа с pywebpush + VAPID |
| `views.py :: push_vapid_public_key / push_subscribe / push_unsubscribe` | API для клиента |
| `static/messenger/js/service-worker.js` | ловит `push` и `notificationclick` |
| `static/messenger/js/push-notifications.js` | `window.MessengerPush.enable(csrfToken)` |
| `consumers.py :: ChatRoomConsumer` | вызывает `send_push_to_user` при новом сообщении |
| `management/commands/generate_vapid_keys.py` | генерация пары VAPID-ключей |

## Настройка

1. **Установить зависимости** (уже добавлены в `requirements.txt`):

```bash
pip install -r myproject/requirements.txt
```

Добавлены: `pywebpush`, `py-vapid`.

2. **Сгенерировать VAPID-ключи** (один раз на сервер):

```bash
cd myproject
python manage.py generate_vapid_keys
```

Скопировать вывод в `.env`:

```
VAPID_PUBLIC_KEY=BHj...
VAPID_PRIVATE_KEY=3Qj...
VAPID_ADMIN_EMAIL=admin@yoursite.ru
```

3. **Применить миграции**:

```bash
python manage.py migrate messenger
```

4. **Пересобрать статику** (чтобы `service-worker.js` и
   `push-notifications.js` попали в `staticfiles/`):

```bash
python manage.py collectstatic --noinput
```

5. **HTTPS обязателен**. Service Worker и PushManager работают только на
   `https://` (исключение — `http://localhost`). В проде у вас уже настроен
   HTTPS на `lc.smileterritory.ru`, так что push заработает как есть.

## Как это работает для пользователя

1. Пользователь заходит на страницу комнаты чата.
2. Браузер запрашивает разрешение на уведомления.
3. После `granted` `MessengerPush.enable()` регистрирует service worker и
   отправляет подписку на `/messenger/push/subscribe/`.
4. При новом сообщении от другого участника `ChatRoomConsumer` создаёт
   уведомление в колокольчике И шлёт Web Push всем подписанным
   участникам (с учётом `ChatRoomNotificationSettings`).
5. Service Worker получает `push`, показывает OS-уведомление. Клик —
   открывает/фокусирует вкладку с нужной комнатой.

Если у пользователя в этот момент открыта и сфокусирована вкладка самой
комнаты — service worker не показывает OS-уведомление (страница сама
покажет in-page `Notification`), чтобы не было дублей.

## Отладка

- Chrome DevTools → `Application` → `Service Workers` / `Push` — отправить
  тестовый push.
- В админке `admin/messenger/webpushsubscription/` видны все активные
  подписки.
- Если push-сервис вернул 404/410 — подписка автоматически удаляется
  (см. `push.send_web_push`).
- Если `VAPID_PRIVATE_KEY` не задан — отправка пропускается, в лог
  выводится предупреждение.
