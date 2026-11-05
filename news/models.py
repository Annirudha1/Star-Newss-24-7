import re
import uuid
from urllib.parse import parse_qs, urlparse

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone
from django.utils.text import slugify

YOUTUBE_ID_RE = re.compile(
    r'(?:youtube\.com/(?:watch\?v=|embed/|v/|live/|shorts/)|youtu\.be/)([A-Za-z0-9_-]{11})'
)


def news_video_thumbnail_path(instance, filename):
    extension = filename.rsplit('.', 1)[-1].lower() if '.' in filename else 'jpg'
    return f'thumbnails/{uuid.uuid4().hex}.{extension}'


def news_video_file_path(instance, filename):
    extension = filename.rsplit('.', 1)[-1].lower() if '.' in filename else 'mp4'
    return f'videos/{uuid.uuid4().hex}.{extension}'

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(blank=True, unique=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class NewsSource(models.Model):
    name = models.CharField(max_length=200, unique=True)
    website_url = models.URLField(blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class RSSFeed(models.Model):
    source = models.ForeignKey(NewsSource, on_delete=models.PROTECT, related_name='feeds')
    feed_url = models.URLField(unique=True)
    is_active = models.BooleanField(default=True)
    last_fetched_at = models.DateTimeField(blank=True, null=True)
    last_error = models.TextField(blank=True)

    class Meta:
        ordering = ['source__name', 'feed_url']
        verbose_name = 'RSS feed'
        verbose_name_plural = 'RSS feeds'

    def __str__(self):
        return f'{self.source}: {self.feed_url}'


class NewsArticle(models.Model):
    source = models.ForeignKey(NewsSource, on_delete=models.PROTECT, related_name='articles')
    feed = models.ForeignKey(
        RSSFeed,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='articles',
    )
    title = models.CharField(max_length=500)
    summary = models.TextField(blank=True)
    original_author = models.CharField(max_length=200, blank=True)
    original_url = models.URLField()
    external_id = models.CharField(max_length=500, blank=True)
    original_published_at = models.DateTimeField(blank=True, null=True)
    original_updated_at = models.DateTimeField(blank=True, null=True)
    image_url = models.URLField(blank=True)
    image_credit = models.CharField(max_length=300, blank=True)
    imported_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-original_published_at', '-imported_at']
        constraints = [
            models.UniqueConstraint(
                fields=['feed', 'external_id'],
                name='unique_article_id_per_feed',
            ),
        ]

    def __str__(self):
        return self.title


class NewsVideo(models.Model):
    title = models.CharField(max_length=255)
    youtube_link = models.URLField(blank=True)
    description = models.TextField(blank=True)
    original_source = models.ForeignKey(
        NewsSource,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='videos',
    )
    original_author = models.CharField(max_length=200, blank=True)
    original_article_url = models.URLField(blank=True)
    original_published_at = models.DateTimeField(blank=True, null=True)
    original_updated_at = models.DateTimeField(blank=True, null=True)
    image_credit = models.CharField(max_length=300, blank=True)
    thumbnail = models.ImageField(upload_to=news_video_thumbnail_path, blank=True, null=True)
    uploaded_video = models.FileField(upload_to=news_video_file_path, blank=True, null=True)
    category = models.ForeignKey('Category', blank=True, null=True, on_delete=models.SET_NULL, related_name='videos')
    created_at = models.DateTimeField(auto_now_add=True)
    likes = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='liked_videos')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()
        errors = {}
        if not self.youtube_link and not self.uploaded_video:
            errors['uploaded_video'] = 'Upload a video file.'
        if not self.youtube_link and not self.thumbnail:
            errors['thumbnail'] = 'Upload a thumbnail image.'
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        old_file_names = {}
        fields_to_track = ('thumbnail', 'uploaded_video')

        if self.pk:
            old_instance = type(self).objects.filter(pk=self.pk).only(*fields_to_track).first()
            if old_instance:
                for field_name in fields_to_track:
                    old_file = getattr(old_instance, field_name)
                    old_file_names[field_name] = old_file.name if old_file else ''

        super().save(*args, **kwargs)

        for field_name in fields_to_track:
            old_name = old_file_names.get(field_name, '')
            current_file = getattr(self, field_name)
            current_name = current_file.name if current_file else ''
            if old_name and old_name != current_name:
                storage = self._meta.get_field(field_name).storage
                transaction.on_commit(lambda name=old_name, field_storage=storage: field_storage.delete(name))

    def delete(self, *args, **kwargs):
        file_names = {}
        for field_name in ('thumbnail', 'uploaded_video'):
            file_obj = getattr(self, field_name)
            file_names[field_name] = file_obj.name if file_obj else ''

        super().delete(*args, **kwargs)

        for field_name, file_name in file_names.items():
            if file_name:
                storage = self._meta.get_field(field_name).storage
                transaction.on_commit(lambda name=file_name, field_storage=storage: field_storage.delete(name))

    @property
    def video_id(self):
        url = self.youtube_link or ''
        parsed = urlparse(url)
        hostname = parsed.hostname or ''
        path = parsed.path or ''

        if hostname.endswith('youtube.com') and path == '/watch':
            query = parse_qs(parsed.query)
            candidate = query.get('v', [''])[0]
        elif hostname.endswith('youtube.com') and path:
            parts = path.split('/')
            candidate = parts[2] if len(parts) > 2 else ''
        elif hostname.endswith('youtu.be'):
            candidate = path.lstrip('/')
        else:
            candidate = ''

        if re.match(r'^[A-Za-z0-9_-]{11}$', candidate):
            return candidate
        match = YOUTUBE_ID_RE.search(url)
        return match.group(1) if match else ''

    @property
    def thumbnail_url(self):
        if self.thumbnail:
            return self.thumbnail.url
        vid = self.video_id
        return f'https://img.youtube.com/vi/{vid}/hqdefault.jpg' if vid else ''

    @property
    def embed_url(self):
        if self.uploaded_video:
            return self.uploaded_video.url
        vid = self.video_id
        return f'https://www.youtube.com/embed/{vid}?rel=0' if vid else ''

    @property
    def video_url(self):
        if self.uploaded_video:
            return self.uploaded_video.url
        return self.embed_url

    @property
    def like_count(self):
        return self.likes.count()


class Comment(models.Model):
    video = models.ForeignKey(NewsVideo, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Comment by {self.user or "Anonymous"} on {self.video.title[:30]}'
