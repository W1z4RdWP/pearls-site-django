"""
Утилиты для аудита операций в базе знаний
"""
import json
from typing import Any, Dict, Optional, Union
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.http import HttpRequest
from .models import AuditLog


def get_client_ip(request: HttpRequest) -> Optional[str]:
    """Получает IP адрес клиента"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def serialize_model_data(instance: models.Model, fields: Optional[list] = None) -> Dict[str, Any]:
    """
    Сериализует данные модели для сохранения в JSON
    """
    if not instance:
        return {}
    
    data = {}
    model_fields = instance._meta.get_fields()
    
    for field in model_fields:
        # Пропускаем обратные связи
        if hasattr(field, 'related_model') and field.related_model:
            continue
            
        field_name = field.name
        
        # Если указаны конкретные поля, берем только их
        if fields and field_name not in fields:
            continue
            
        try:
            value = getattr(instance, field_name)
            
            # Обработка разных типов полей
            if isinstance(field, models.DateTimeField):
                data[field_name] = value.isoformat() if value else None
            elif isinstance(field, models.DateField):
                data[field_name] = value.isoformat() if value else None
            elif isinstance(field, models.ForeignKey):
                if value:
                    data[field_name] = {
                        'id': value.pk,
                        'name': str(value)
                    }
                else:
                    data[field_name] = None
            elif isinstance(field, models.ManyToManyField):
                if hasattr(instance, field_name):
                    related_objects = getattr(instance, field_name).all()
                    data[field_name] = [
                        {'id': obj.pk, 'name': str(obj)} 
                        for obj in related_objects
                    ]
                else:
                    data[field_name] = []
            elif isinstance(field, (models.ImageField, models.FileField)):
                data[field_name] = value.url if value else None
            else:
                # Обычные поля (CharField, TextField, IntegerField, etc.)
                data[field_name] = value
                
        except Exception as e:
            # Если не можем получить значение поля, записываем ошибку
            data[field_name] = f"<error: {str(e)}>"
    
    return data


def log_audit_action(
    user,
    action: str,
    instance: models.Model,
    request: Optional[HttpRequest] = None,
    old_values: Optional[Dict] = None,
    new_values: Optional[Dict] = None,
    extra_data: Optional[Dict] = None,
    comment: str = ""
) -> AuditLog:
    """
    Создает запись аудита для операции
    
    Args:
        user: Пользователь, выполнивший операцию
        action: Тип операции ('create', 'update', 'delete', etc.)
        instance: Объект, над которым выполнена операция
        request: HTTP запрос (для получения IP)
        old_values: Старые значения полей (для update)
        new_values: Новые значения полей (для create/update)
        extra_data: Дополнительные данные
        comment: Комментарий к операции
    """
    content_type = ContentType.objects.get_for_model(instance)
    
    # Получаем название объекта
    object_name = str(instance)
    
    # Получаем IP адрес
    ip_address = None
    if request:
        ip_address = get_client_ip(request)
    
    # Если не переданы значения, пытаемся получить их автоматически
    if action in ['create', 'update'] and new_values is None:
        new_values = serialize_model_data(instance)
    
    audit_log = AuditLog.objects.create(
        user=user,
        action=action,
        content_type=content_type,
        object_id=instance.pk if hasattr(instance, 'pk') else None,
        object_name=object_name,
        model_name=instance._meta.model_name,
        ip_address=ip_address,
        old_values=old_values or {},
        new_values=new_values or {},
        extra_data=extra_data or {},
        comment=comment
    )
    
    return audit_log


def log_create(user, instance: models.Model, request: Optional[HttpRequest] = None, 
               extra_data: Optional[Dict] = None, comment: str = "") -> AuditLog:
    """Логирует создание объекта"""
    return log_audit_action(
        user=user,
        action='create',
        instance=instance,
        request=request,
        extra_data=extra_data,
        comment=comment
    )


def log_update(user, instance: models.Model, old_values: Dict, 
               request: Optional[HttpRequest] = None, extra_data: Optional[Dict] = None, 
               comment: str = "") -> AuditLog:
    """Логирует обновление объекта"""
    return log_audit_action(
        user=user,
        action='update',
        instance=instance,
        request=request,
        old_values=old_values,
        extra_data=extra_data,
        comment=comment
    )


def log_delete(user, instance: models.Model, request: Optional[HttpRequest] = None, 
               extra_data: Optional[Dict] = None, comment: str = "") -> AuditLog:
    """Логирует удаление объекта"""
    # Для удаления сохраняем текущие значения как старые
    old_values = serialize_model_data(instance)
    
    return log_audit_action(
        user=user,
        action='delete',
        instance=instance,
        request=request,
        old_values=old_values,
        extra_data=extra_data,
        comment=comment
    )


def log_copy(user, original_instance: models.Model, new_instance: models.Model,
             request: Optional[HttpRequest] = None, extra_data: Optional[Dict] = None,
             comment: str = "") -> AuditLog:
    """Логирует копирование объекта"""
    extra_data = extra_data or {}
    extra_data.update({
        'original_id': original_instance.pk,
        'original_name': str(original_instance),
        'new_id': new_instance.pk,
        'new_name': str(new_instance)
    })
    
    return log_audit_action(
        user=user,
        action='copy',
        instance=new_instance,
        request=request,
        extra_data=extra_data,
        comment=comment
    )


def log_move(user, instance: models.Model, old_parent, new_parent,
             request: Optional[HttpRequest] = None, extra_data: Optional[Dict] = None,
             comment: str = "") -> AuditLog:
    """Логирует перемещение объекта"""
    extra_data = extra_data or {}
    extra_data.update({
        'old_parent': str(old_parent) if old_parent else 'Корень',
        'new_parent': str(new_parent) if new_parent else 'Корень',
        'old_parent_id': old_parent.pk if old_parent else None,
        'new_parent_id': new_parent.pk if new_parent else None
    })
    
    return log_audit_action(
        user=user,
        action='move',
        instance=instance,
        request=request,
        extra_data=extra_data,
        comment=comment
    )


def log_reorder(user, instances: list, request: Optional[HttpRequest] = None,
                extra_data: Optional[Dict] = None, comment: str = "") -> list:
    """Логирует изменение порядка нескольких объектов"""
    logs = []
    
    for instance in instances:
        instance_extra_data = extra_data.copy() if extra_data else {}
        instance_extra_data['order'] = getattr(instance, 'order', None)
        
        log = log_audit_action(
            user=user,
            action='reorder',
            instance=instance,
            request=request,
            extra_data=instance_extra_data,
            comment=comment
        )
        logs.append(log)
    
    return logs


def log_mirror(user, lesson, category, mirror_instance,
               request: Optional[HttpRequest] = None, extra_data: Optional[Dict] = None,
               comment: str = "") -> AuditLog:
    """Логирует создание зеркала урока"""
    extra_data = extra_data or {}
    extra_data.update({
        'lesson_id': lesson.pk,
        'lesson_name': str(lesson),
        'category_id': category.pk,
        'category_name': str(category)
    })
    
    return log_audit_action(
        user=user,
        action='mirror',
        instance=mirror_instance,
        request=request,
        extra_data=extra_data,
        comment=comment
    )


def log_actualize(user, lesson_version, request: Optional[HttpRequest] = None,
                  extra_data: Optional[Dict] = None, comment: str = "") -> AuditLog:
    """Логирует актуализацию урока"""
    extra_data = extra_data or {}
    extra_data.update({
        'lesson_id': lesson_version.lesson.pk,
        'lesson_name': str(lesson_version.lesson),
        'version': lesson_version.version,
        'next_update': lesson_version.next_update.isoformat() if lesson_version.next_update else None,
        'update_period_days': lesson_version.update_period_days
    })
    
    return log_audit_action(
        user=user,
        action='actualize',
        instance=lesson_version,
        request=request,
        extra_data=extra_data,
        comment=comment
    )


class AuditLoggerMixin:
    """
    Миксин для автоматического логирования операций в view
    """
    
    def get_audit_user(self):
        """Возвращает пользователя для аудита"""
        return getattr(self.request, 'user', None)
    
    def log_create_action(self, instance, comment: str = ""):
        """Логирует создание объекта"""
        return log_create(
            user=self.get_audit_user(),
            instance=instance,
            request=self.request,
            comment=comment
        )
    
    def log_update_action(self, instance, old_values: Dict, comment: str = ""):
        """Логирует обновление объекта"""
        return log_update(
            user=self.get_audit_user(),
            instance=instance,
            old_values=old_values,
            request=self.request,
            comment=comment
        )
    
    def log_delete_action(self, instance, comment: str = ""):
        """Логирует удаление объекта"""
        return log_delete(
            user=self.get_audit_user(),
            instance=instance,
            request=self.request,
            comment=comment
        )
