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
    content = models.TextField()
    news_type = models.CharField(
        max_length=100,
        choices=NewsType.choices,
        default=NewsType.OTHER,
        db_index=True,
    )
    main_image = models.ImageField(upload_to='news/main/', blank=True, null=True)
    video = models.FileField(upload_to='news/video/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Новость'
        verbose_name_plural = 'Новости'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('news:news_detail', kwargs={'pk': self.pk})

    @property
    def first_gallery_media(self):
        for media in self.gallery_images.all():
            if media.image or media.video:
                return media
        return None

    @property
    def first_gallery_image(self):
        for media in self.gallery_images.all():
            if media.image:
                return media
        return None


    def get_news_type_display_label(self):
        return self.get_news_type_display()


class NewsGalleryImage(models.Model):
    news_item = models.ForeignKey(
        NewsItem,
        related_name='gallery_images',
        on_delete=models.CASCADE,
    )
    image = models.ImageField(upload_to='news/gallery/', blank=True, null=True)
    video = models.FileField(upload_to='news/gallery/video/', blank=True, null=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'id']

    @property
    def is_image(self):
        return bool(self.image)

    @property
    def is_video(self):
        return bool(self.video)

    @property
    def file_name(self):
        media_file = self.image or self.video
        return media_file.name if media_file else ''

    def __str__(self):
        return f'{self.news_item_id}: {self.file_name or "empty"}'
