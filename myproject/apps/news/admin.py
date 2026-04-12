from django.contrib import admin

from .models import NewsGalleryImage, NewsItem


class NewsGalleryImageInline(admin.TabularInline):
    model = NewsGalleryImage
    extra = 1
    ordering = ('sort_order', 'id')


@admin.register(NewsItem)
class NewsItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'news_type', 'created_at', 'updated_at')
    list_filter = ('news_type',)
    search_fields = ('title', 'description', 'content')
    ordering = ('-created_at',)
    inlines = (NewsGalleryImageInline,)

