from django import forms

from .models import NewsItem


class NewsItemForm(forms.ModelForm):
    class Meta:
        model = NewsItem
        fields = [
            'title',
            'news_type',
            'description',
            'content',
            'main_image',
            'video',
            'video_embed_url',
        ]
        labels = {
            'title': 'Заголовок',
            'news_type': 'Рубрика',
            'description': 'Краткое описание',
            'content': 'Полный текст',
            'main_image': 'Главное изображение',
            'video': 'Видеофайл',
            'video_embed_url': 'Ссылка на видео (YouTube, VK и т. п.)',
        }
        widgets = {
            'title': forms.TextInput(
                attrs={
                    'class': 'form-control nfc-control',
                    'maxlength': 255,
                    'autocomplete': 'off',
                }
            ),
            'news_type': forms.Select(attrs={'class': 'form-control nfc-control'}),
            'description': forms.Textarea(
                attrs={
                    'class': 'form-control nfc-control',
                    'rows': 4,
                    'placeholder': 'Текст для карточки в ленте (2–4 строки)',
                }
            ),
            'content': forms.Textarea(
                attrs={
                    'class': 'form-control nfc-control',
                    'rows': 14,
                    'placeholder': 'Полный текст публикации',
                }
            ),
            'main_image': forms.ClearableFileInput(
                attrs={
                    'class': 'form-control nfc-control',
                    'accept': 'image/*',
                }
            ),
            'video': forms.ClearableFileInput(
                attrs={
                    'class': 'form-control nfc-control',
                    'accept': 'video/*',
                }
            ),
            'video_embed_url': forms.URLInput(
                attrs={
                    'class': 'form-control nfc-control',
                    'placeholder': 'https://www.youtube.com/watch?v=…',
                    'autocomplete': 'off',
                }
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        max_gallery_bytes = 12 * 1024 * 1024
        allowed_image_types = (
            'image/jpeg',
            'image/png',
            'image/webp',
            'image/gif',
        )
        for f in self.files.getlist('gallery_files'):
            if f.size > max_gallery_bytes:
                raise forms.ValidationError(
                    f'Файл «{f.name}» слишком большой (максимум {max_gallery_bytes // (1024 * 1024)} МБ).'
                )
            ct = (getattr(f, 'content_type', None) or '').lower()
            if ct and ct not in allowed_image_types:
                raise forms.ValidationError(
                    f'В галерее допустимы только изображения (JPEG, PNG, WebP, GIF): «{f.name}».'
                )
        return cleaned_data
