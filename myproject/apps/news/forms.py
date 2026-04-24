import os

from django import forms

from .models import NewsItem


class NewsItemForm(forms.ModelForm):
    class Meta:
        model = NewsItem
        fields = [
            'title',
            'news_type',
            'content',
        ]
        labels = {
            'title': 'Заголовок',
            'news_type': 'Рубрика',
            'content': 'Полный текст',
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
            'content': forms.Textarea(
                attrs={
                    'class': 'form-control nfc-control',
                    'rows': 14,
                    'placeholder': 'Полный текст публикации',
                }
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        max_media_bytes = 50 * 1024 * 1024
        allowed_image_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
        allowed_video_extensions = {'.mp4', '.webm', '.mov', '.avi', '.mkv', '.m4v', '.ogg'}

        for f in self.files.getlist('media_files'):
            if f.size > max_media_bytes:
                raise forms.ValidationError(
                    f'Файл «{f.name}» слишком большой (максимум {max_media_bytes // (1024 * 1024)} МБ).'
                )

            ct = (getattr(f, 'content_type', None) or '').lower()
            ext = os.path.splitext((getattr(f, 'name', '') or '').lower())[1]
            is_image = ct.startswith('image/') or ext in allowed_image_extensions
            is_video = ct.startswith('video/') or ext in allowed_video_extensions

            if not (is_image or is_video):
                raise forms.ValidationError(
                    f'Допустимы только изображения и видео (JPEG, PNG, WebP, GIF, MP4, WebM, MOV, AVI, MKV, M4V, OGG): «{f.name}».'
                )
        return cleaned_data
