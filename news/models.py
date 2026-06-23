import re
from urllib.parse import parse_qs, urlparse

from django.conf import settings
from django.db import models, transaction
from django.utils import timezone
from django.utils.text import slugify

YOUTUBE_ID_RE = re.compile(
    r'(?:youtube\.com/(?:watch\?v=|embed/|v/|live/|shorts/)|youtu\.be/)([A-Za-z0-9_-]{11})'
)

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


class NewsVideo(models.Model):
    title = models.CharField(max_length=255)
    youtube_link = models.URLField()
    category = models.ForeignKey('Category', blank=True, null=True, on_delete=models.SET_NULL, related_name='videos')
    created_at = models.DateTimeField(auto_now_add=True)
    likes = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='liked_videos')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def video_id(self):
        url = self.youtube_link or ''
        parsed = urlparse(url)
        hostname = parsed.hostname or ''
        path = parsed.path or ''

        # Standard watch URLs
        if hostname.endswith('youtube.com') and path == '/watch':
            query = parse_qs(parsed.query)
            candidate = query.get('v', [''])[0]
        # Direct embed or path-based URLs
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
        vid = self.video_id
        return f'https://img.youtube.com/vi/{vid}/hqdefault.jpg' if vid else ''

    @property
    def embed_url(self):
        vid = self.video_id
        return f'https://www.youtube.com/embed/{vid}?rel=0' if vid else ''

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
