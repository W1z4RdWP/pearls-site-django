from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.db import transaction
from .models import ProductOrder
from gamification.utils import award_dascoin_points
import logging

logger = logging.getLogger(__name__)

# Словарь для хранения старых статусов заказов
_old_order_status = {}


@receiver(pre_save, sender=ProductOrder)
def store_old_order_status(sender, instance, **kwargs):
    """Сохраняет старый статус заказа перед сохранением"""
    if instance.pk:
        try:
            old_instance = ProductOrder.objects.get(pk=instance.pk)
            _old_order_status[instance.pk] = old_instance.status
        except ProductOrder.DoesNotExist:
            _old_order_status[instance.pk] = None
    else:
        # Для новых заказов
        _old_order_status[id(instance)] = None


@receiver(post_save, sender=ProductOrder)
def refund_points_on_rejection_or_cancellation(sender, instance, created, **kwargs):
    """
    Возвращает баллы пользователю при отклонении или отмене заказа.
    Также создает уведомления о смене статуса заказа.
    Баллы возвращаются только если статус изменился на 'rejected' или 'cancelled'.
    """
    if created:
        # Для новых заказов создаем уведомление о создании заказа
        _old_order_status.pop(id(instance), None)
        try:
            from notifications.models import Notification
            Notification.create_order_status_notification(
                order=instance,
                old_status=None,
                new_status='pending'
            )
        except Exception as e:
            logger.error(
                f"Ошибка при создании уведомления о создании заказа #{instance.id}: {str(e)}",
                exc_info=True
            )
        return
    
    # Получаем старый статус
    old_status = _old_order_status.pop(instance.pk, None)
    
    # Если статус не изменился, ничего не делаем
    if old_status == instance.status:
        return
    
    # Создаем уведомление о смене статуса
    try:
        from notifications.models import Notification
        Notification.create_order_status_notification(
            order=instance,
            old_status=old_status,
            new_status=instance.status
        )
    except Exception as e:
        logger.error(
            f"Ошибка при создании уведомления о смене статуса заказа #{instance.id}: {str(e)}",
            exc_info=True
        )
    
    # Проверяем, нужно ли вернуть баллы
    # Баллы возвращаются только если:
    # 1. Статус изменился на 'rejected' или 'cancelled'
    # 2. Старый статус был не 'rejected' и не 'cancelled' (чтобы не возвращать дважды)
    # 3. Баллы еще не были возвращены (статус был pending, approved и т.д.)
    should_refund = (
        instance.status in ['rejected', 'cancelled'] and
        old_status not in ['rejected', 'cancelled', None] and
        instance.points_spent > 0
    )
    
    if should_refund:
        try:
            with transaction.atomic():
                # Возвращаем баллы пользователю
                reason = f'Возврат баллов за отмененный заказ товара: {instance.product.name}'
                if instance.status == 'rejected':
                    reason = f'Возврат баллов за отклоненный заказ товара: {instance.product.name}'
                
                award_dascoin_points(
                    user=instance.user,
                    points=instance.points_spent,
                    reason=reason,
                    admin_user=instance.reviewed_by
                )
                
                logger.info(
                    f"Возвращены баллы пользователю {instance.user.username} за заказ #{instance.id}. "
                    f"Статус изменен с '{old_status}' на '{instance.status}'. "
                    f"Возвращено баллов: {instance.points_spent}"
                )
        except Exception as e:
            logger.error(
                f"Ошибка при возврате баллов за заказ #{instance.id}: {str(e)}",
                exc_info=True
            )

