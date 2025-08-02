from django.contrib import admin
from .models import Badge, Achievement, UserBadge, UserAchievement, DascoinTransaction


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ['name', 'badge_type', 'points_required', 'is_active', 'created_at']
    list_filter = ['badge_type', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['points_required', 'name']


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ['name', 'achievement_type', 'is_unique', 'is_active', 'created_at']
    list_filter = ['achievement_type', 'is_unique', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ['user', 'badge', 'earned_at']
    list_filter = ['badge__badge_type', 'earned_at']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'badge__name']
    ordering = ['-earned_at']


@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ['user', 'achievement', 'earned_at']
    list_filter = ['achievement__achievement_type', 'earned_at']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'achievement__name']
    ordering = ['-earned_at']


@admin.register(DascoinTransaction)
class DascoinTransactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'transaction_type', 'points_change', 'points_before', 'points_after', 'admin_user', 'created_at']
    list_filter = ['transaction_type', 'created_at', 'admin_user']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'reason']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    
    def has_add_permission(self, request):
        return False  # Запрещаем ручное создание транзакций