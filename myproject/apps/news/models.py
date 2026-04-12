from urllib.parse import parse_qs, urlparse

from django.db import models
from django.urls import reverse


class NewsType(models.TextChoices):
    NEW_EMPLOYEES = 'new_employees', 'Новые сотрудники'
    EVENTS = 'events', 'Мероприятия'
    BIRTHDAYS = 'birthdays', 'Дни рождения'
    CORPORATE_EVENTS = 'corporate_events', 'Корпоративная жизнь'
    INTERNAL_EVENTS = 'internal_events', 'Праздники компании'
    NEW_YEAR = 'new_year', 'Новый год'
    OTHER = 'other', 'Другое'


class NewsItem(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, help_text='Краткое описание для карточки в ленте')
    content = models.TextField()
    news_type = models.CharField(
        max_length=32,
        choices=NewsType.choices,
        default=NewsType.OTHER,
        db_index=True,
    )
    main_image = models.ImageField(upload_to='news/main/', blank=True, null=True)
    video = models.FileField(upload_to='news/video/', blank=True, null=True)
    video_embed_url = models.URLField(blank=True, help_text='Ссылка на видео (YouTube, VK и т.п.)')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('news:news_detail', kwargs={'pk': self.pk})

    @property
    def resolved_video_embed_src(self):
        """URL для iframe: поддержка watch/v и youtu.be, иначе исходная https-ссылка."""
        url = (self.video_embed_url or '').strip()
        if not url:
            return ''
        if 'youtube.com/embed/' in url:
            return url
        try:
            parsed = urlparse(url)
            host = (parsed.hostname or '').lower()
            if host in ('www.youtube.com', 'youtube.com', 'm.youtube.com') and parsed.path == '/watch':
                v = parse_qs(parsed.query).get('v', [None])[0]
                if v:
                    return f'https://www.youtube.com/embed/{v}'
            if host == 'youtu.be':
                vid = parsed.path.strip('/').split('?')[0]
                if vid:
                    return f'https://www.youtube.com/embed/{vid}'
        except (ValueError, TypeError):
            return ''
        return url if url.startswith('https://') else ''

    def get_news_type_display_label(self):
        return self.get_news_type_display()


class NewsGalleryImage(models.Model):
    news_item = models.ForeignKey(
        NewsItem,
        related_name='gallery_images',
        on_delete=models.CASCADE,
    )
    image = models.ImageField(upload_to='news/gallery/')
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'id']

    def __str__(self):
        return f'{self.news_item_id}: {self.image.name}'
