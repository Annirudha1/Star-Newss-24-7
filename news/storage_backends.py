from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.files.storage import FileSystemStorage

try:
    from storages.backends.s3boto3 import S3Boto3Storage
except ImportError:  # pragma: no cover - optional dependency
    S3Boto3Storage = None


class LocalMediaStorage(FileSystemStorage):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('location', settings.MEDIA_ROOT)
        kwargs.setdefault('base_url', settings.MEDIA_URL)
        super().__init__(*args, **kwargs)


if settings.CLOUDFLARE_R2_ENABLED:
    if S3Boto3Storage is None:
        raise ImproperlyConfigured(
            'Cloudflare R2 storage is enabled, but django-storages is not installed.'
        )

    class MediaStorage(S3Boto3Storage):
        bucket_name = settings.CLOUDFLARE_R2_BUCKET_NAME
        access_key = settings.CLOUDFLARE_R2_ACCESS_KEY_ID
        secret_key = settings.CLOUDFLARE_R2_SECRET_ACCESS_KEY
        endpoint_url = settings.CLOUDFLARE_R2_ENDPOINT_URL
        region_name = 'auto'
        default_acl = None
        file_overwrite = True
        querystring_auth = not bool(settings.CLOUDFLARE_R2_CUSTOM_DOMAIN)
        custom_domain = settings.CLOUDFLARE_R2_CUSTOM_DOMAIN or None
        location = settings.CLOUDFLARE_R2_MEDIA_LOCATION

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

else:
    class MediaStorage(LocalMediaStorage):
        pass
