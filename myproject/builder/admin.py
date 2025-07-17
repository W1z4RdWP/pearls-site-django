from django.contrib import admin
from .models import CategoryName, LessonVersion, LessonCategoryMirror, DictionaryTerm, DictionarySection



admin.site.register(CategoryName)

@admin.register(LessonVersion)
class LessonVersionAdmin(admin.ModelAdmin):
    list_display = ('lesson', 'version', 'updated_at', 'updated_by', 'comment')
    list_filter = ('lesson', 'updated_by')
    search_fields = ('lesson__title', 'title', 'comment')


@admin.register(LessonCategoryMirror)
class LessonCategoryMirrorAdmin(admin.ModelAdmin):
    list_display = ('lesson', 'category', 'order')
    list_filter = ('lesson', 'category')
    search_fields = ('lesson__title', 'category__name')


admin.site.register(DictionaryTerm)
admin.site.register(DictionarySection)

# class DictionaryTermAdmin(admin.ModelAdmin):
#     list_display = ('term', 'author', 'order', 'created_at', 'updated_at')
#     search_fields = ('term', 'definition', 'author__username')
#     ordering = ('order', 'term')

#     def save_model(self, request, obj, form, change):
#         if not obj.pk:
#             obj.author = request.user
#         obj.save()