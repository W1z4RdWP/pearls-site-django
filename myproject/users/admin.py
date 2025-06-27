from rangefilter.filters import DateRangeFilterBuilder
from django.contrib import admin
from .models import Profile

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'first_name', 'last_name', 'date_of_birth', 'is_approved']
    list_filter = ['is_approved', ("date_of_birth", DateRangeFilterBuilder()),]
    search_fields = ['user__username', 'first_name']
    actions = ['approve_users']

    def approve_users(self, request, queryset):
        queryset.update(is_approved=True)
    approve_users.short_description = "Одобрить выбранных пользователей"