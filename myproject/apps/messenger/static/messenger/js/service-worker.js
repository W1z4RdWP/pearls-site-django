/*
 * Service Worker для Web Push уведомлений messenger.
 *
 * Обрабатывает push-события от push-сервиса браузера и показывает системные
 * уведомления, даже если вкладка сайта закрыта.
 */

self.addEventListener('install', (event) => {
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    event.waitUntil(self.clients.claim());
});

self.addEventListener('push', (event) => {
    event.waitUntil(handlePush(event));
});

async function handlePush(event) {
    let data = {};
    try {
        data = event.data ? event.data.json() : {};
    } catch (e) {
        const text = event.data ? event.data.text() : '';
        data = { title: 'Новое сообщение', body: text };
    }

    const title = data.title || 'Новое сообщение';
    const targetUrl = data.url || '/';
    const tag = data.tag || 'messenger';

    // Если уже есть открытая сфокусированная вкладка на нужном URL —
    // push-уведомление на уровне ОС не показываем, страница сама покажет in-page
    // уведомление через Notification API.
    try {
        const clientsList = await self.clients.matchAll({
            type: 'window',
            includeUncontrolled: true,
        });
        const urlPath = targetUrl.split('?')[0];
        const hasFocusedOnTarget = clientsList.some((client) => {
            return client.focused && client.url && client.url.indexOf(urlPath) !== -1;
        });
        if (hasFocusedOnTarget) {
            return;
        }
    } catch (_) {
        // Игнорируем ошибки доступа к clients
    }

    const options = {
        body: data.body || '',
        icon: data.icon || '/static/global/imgs/favicon.ico',
        badge: data.badge || '/static/global/imgs/favicon.ico',
        tag: tag,
        renotify: true,
        requireInteraction: false,
        data: { url: targetUrl },
    };

    return self.registration.showNotification(title, options);
}

self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    const targetUrl = (event.notification.data && event.notification.data.url) || '/';
    event.waitUntil(focusOrOpen(targetUrl));
});

async function focusOrOpen(targetUrl) {
    const clientsList = await self.clients.matchAll({
        type: 'window',
        includeUncontrolled: true,
    });
    const urlPath = targetUrl.split('?')[0];
    for (const client of clientsList) {
        if (client.url && client.url.indexOf(urlPath) !== -1 && 'focus' in client) {
            return client.focus();
        }
    }
    if (self.clients.openWindow) {
        return self.clients.openWindow(targetUrl);
    }
    return null;
}
