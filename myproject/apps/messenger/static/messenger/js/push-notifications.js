/*
 * Клиентский модуль Web Push для messenger.
 *
 * Публикует window.MessengerPush.enable(csrfToken) и .disable(csrfToken).
 * enable() регистрирует service-worker, подписывается на PushManager и
 * отправляет подписку на сервер.
 */

(function () {
    'use strict';

    const SERVICE_WORKER_URL = '/static/messenger/js/service-worker.js';
    const VAPID_ENDPOINT = '/messenger/push/vapid-public-key/';
    const SUBSCRIBE_ENDPOINT = '/messenger/push/subscribe/';
    const UNSUBSCRIBE_ENDPOINT = '/messenger/push/unsubscribe/';

    function isSupported() {
        return (
            typeof navigator !== 'undefined' &&
            'serviceWorker' in navigator &&
            typeof window !== 'undefined' &&
            'PushManager' in window &&
            'Notification' in window
        );
    }

    function urlBase64ToUint8Array(base64String) {
        const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
        const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
        const rawData = atob(base64);
        const outputArray = new Uint8Array(rawData.length);
        for (let i = 0; i < rawData.length; i++) {
            outputArray[i] = rawData.charCodeAt(i);
        }
        return outputArray;
    }

    async function getServiceWorkerRegistration() {
        const existing = await navigator.serviceWorker.getRegistration(SERVICE_WORKER_URL);
        if (existing) {
            return existing;
        }
        return navigator.serviceWorker.register(SERVICE_WORKER_URL);
    }

    async function fetchVapidKey() {
        const res = await fetch(VAPID_ENDPOINT, { credentials: 'same-origin' });
        if (!res.ok) {
            throw new Error('Не удалось получить VAPID public key (status ' + res.status + ')');
        }
        const data = await res.json();
        if (!data.publicKey) {
            throw new Error('В ответе отсутствует publicKey');
        }
        return data.publicKey;
    }

    async function sendSubscriptionToServer(subscription, csrfToken) {
        const json = subscription.toJSON();
        const res = await fetch(SUBSCRIBE_ENDPOINT, {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
            },
            body: JSON.stringify({
                endpoint: json.endpoint,
                keys: json.keys,
            }),
        });
        if (!res.ok) {
            throw new Error('Сервер отклонил подписку (status ' + res.status + ')');
        }
        return res.json();
    }

    async function deleteSubscriptionOnServer(endpoint, csrfToken) {
        try {
            await fetch(UNSUBSCRIBE_ENDPOINT, {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                },
                body: JSON.stringify({ endpoint: endpoint }),
            });
        } catch (_) {
            // Ошибка удаления на сервере не критична для клиента
        }
    }

    async function enable(csrfToken) {
        if (!isSupported()) {
            console.info('[MessengerPush] Web Push не поддерживается этим браузером');
            return null;
        }
        if (Notification.permission !== 'granted') {
            console.info('[MessengerPush] Нет разрешения на уведомления, подписка пропущена');
            return null;
        }

        try {
            const registration = await getServiceWorkerRegistration();
            await navigator.serviceWorker.ready;

            let subscription = await registration.pushManager.getSubscription();
            if (!subscription) {
                const publicKey = await fetchVapidKey();
                subscription = await registration.pushManager.subscribe({
                    userVisibleOnly: true,
                    applicationServerKey: urlBase64ToUint8Array(publicKey),
                });
            }

            await sendSubscriptionToServer(subscription, csrfToken);
            return subscription;
        } catch (err) {
            console.warn('[MessengerPush] Ошибка подписки на Web Push:', err);
            return null;
        }
    }

    async function disable(csrfToken) {
        if (!isSupported()) {
            return false;
        }
        try {
            const registration = await navigator.serviceWorker.getRegistration(SERVICE_WORKER_URL);
            if (!registration) {
                return false;
            }
            const subscription = await registration.pushManager.getSubscription();
            if (!subscription) {
                return false;
            }
            const endpoint = subscription.endpoint;
            await subscription.unsubscribe();
            await deleteSubscriptionOnServer(endpoint, csrfToken);
            return true;
        } catch (err) {
            console.warn('[MessengerPush] Ошибка отписки от Web Push:', err);
            return false;
        }
    }

    window.MessengerPush = {
        isSupported: isSupported,
        enable: enable,
        disable: disable,
    };
})();
