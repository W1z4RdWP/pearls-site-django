from django.contrib import admin
from .models import Category

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'order')
    list_filter = ('parent',)
    search_fields = ('name',)

admin.site.register(Category, CategoryAdmin)