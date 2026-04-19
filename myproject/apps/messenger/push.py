"""
Отправка Web Push уведомлений для messenger.

Использует pywebpush и VAPID-ключи из настроек. Функции синхронные — при вызове
из асинхронного кода (consumers) оборачивайте в database_sync_to_async /
sync_to_async, как это делается для остального sync-кода.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Iterable

from django.conf import settings

try:
    from pywebpush import WebPushException, webpush
except ImportError:  # pragma: no cover
    webpush = None
    WebPushException = Exception  # type: ignore[assignment]

from .models import WebPushSubscription

logger = logging.getLogger(__name__)


def _get_vapid_claims() -> dict:
    email = getattr(settings, 'VAPID_ADMIN_EMAIL', '') or 'admin@example.com'
    return {'sub': f'mailto:{email}'}


def is_configured() -> bool:
    """VAPID-ключи настроены и библиотека установлена."""
    return bool(
        webpush is not None
        and getattr(settings, 'VAPID_PRIVATE_KEY', '')
        and getattr(settings, 'VAPID_PUBLIC_KEY', '')
    )


def send_web_push(subscription: WebPushSubscription, payload: dict[str, Any]) -> bool:
    """
    Отправляет payload на конкретную подписку.

    Возвращает True, если push успешно передан push-сервису; False — если нет.
    При получении 404/410 подписка считается недействительной и удаляется.
    """
    if webpush is None:
        logger.warning('pywebpush не установлен — web push отправка пропущена')
        return False

    private_key = getattr(settings, 'VAPID_PRIVATE_KEY', '')
    if not private_key:
        logger.debug('VAPID_PRIVATE_KEY не настроен — web push пропущен')
        return False

    try:
        webpush(
            subscription_info=subscription.to_subscription_info(),
            data=json.dumps(payload, ensure_ascii=False),
            vapid_private_key=private_key,
            vapid_claims=_get_vapid_claims(),
            ttl=getattr(settings, 'VAPID_TTL', 60 * 60 * 24),
        )
        return True
    except WebPushException as exc:  # type: ignore[misc]
        response = getattr(exc, 'response', None)
        status = getattr(response, 'status_code', None)
        if status in (404, 410):
            subscription.delete()
            logger.info('Удалена устаревшая Web Push подписка (status=%s) для user_id=%s', status, subscription.user_id)
        else:
            logger.warning('Ошибка отправки web push (status=%s): %s', status, exc)
        return False
    except Exception as exc:  # pragma: no cover - защитный catch-all
        logger.exception('Непредвиденная ошибка при отправке web push: %s', exc)
        return False


def send_push_to_user(user, payload: dict[str, Any]) -> int:
    """
    Шлёт payload на все подписки пользователя. Возвращает число успешных отправок.
    """
    if not is_configured():
        return 0

    subscriptions: Iterable[WebPushSubscription] = list(
        WebPushSubscription.objects.filter(user=user)
    )
    if not subscriptions:
        return 0

    delivered = 0
    for sub in subscriptions:
        if send_web_push(sub, payload):
            delivered += 1
    return delivered
