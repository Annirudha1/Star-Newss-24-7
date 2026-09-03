from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name, default=False):
    value = config(name, default=default)
    if isinstance(value, bool):
        return value

    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "t", "yes", "y", "on", "debug", "development"}:
        return True
    if normalized in {"0", "false", "f", "no", "n", "off", "release", "production"}:
        return False
    return bool(default)

# ==========================================================
# BASIC SETTINGS
# ==========================================================

SECRET_KEY = config(
    "SECRET_KEY",
    default="django-insecure-starnews-24x7-secret-key"
)

DEBUG = env_bool("DEBUG", default=True)

# ==========================================================
# ALLOWED HOSTS
# ==========================================================

ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    "starnews24x7.com",
    "www.starnews24x7.com",
    "187.127.166.29",
]

# ==========================================================
# CSRF
# ==========================================================

CSRF_TRUSTED_ORIGINS = [
    
    "http://127.0.0.1:8008",
    "http://localhost:8008",
    "https://starnews24x7.com",
    "https://www.starnews24x7.com",
]

# ==========================================================
# APPLICATIONS
# ==========================================================

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",

    "rest_framework",

    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",

    "news",
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "news.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
}

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

SITE_ID = 1

LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

ACCOUNT_EMAIL_VERIFICATION = "none"

SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_EMAIL_REQUIRED = True
SOCIALACCOUNT_EMAIL_VERIFICATION = "none"

SOCIALACCOUNT_ADAPTER = "news.adapters.CustomSocialAccountAdapter"

SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "SCOPE": ["profile", "email"],
        "AUTH_PARAMS": {
            "access_type": "online",
        },
        "APP": {
            "client_id": config("GOOGLE_OAUTH_CLIENT_ID", default=""),
            "secret": config("GOOGLE_OAUTH_CLIENT_SECRET", default=""),
            "key": "",
        },
    },
}

# ==========================================================
# MIDDLEWARE
# ==========================================================

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "starnews_project.urls"

# ==========================================================
# TEMPLATES
# ==========================================================

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "starnews_project.wsgi.application"

# ==========================================================
# DATABASE
# ==========================================================

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# ==========================================================
# PASSWORDS
# ==========================================================

AUTH_PASSWORD_VALIDATORS = []

# ==========================================================
# INTERNATIONALIZATION
# ==========================================================

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Asia/Kolkata"

USE_I18N = True
USE_TZ = True

# ==========================================================
# STATIC FILES
# ==========================================================

STATIC_URL = "/static/"

STATICFILES_DIRS = [
    BASE_DIR / "static",
]

STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ==========================================================
# MEDIA STORAGE
# ==========================================================

CLOUDFLARE_R2_ENABLED = env_bool("CLOUDFLARE_R2_ENABLED", default=False)
CLOUDFLARE_R2_ACCOUNT_ID = config("CLOUDFLARE_R2_ACCOUNT_ID", default="")
CLOUDFLARE_R2_ACCESS_KEY_ID = config("CLOUDFLARE_R2_ACCESS_KEY_ID", default="")
CLOUDFLARE_R2_SECRET_ACCESS_KEY = config("CLOUDFLARE_R2_SECRET_ACCESS_KEY", default="")
CLOUDFLARE_R2_BUCKET_NAME = config("CLOUDFLARE_R2_BUCKET_NAME", default="")
CLOUDFLARE_R2_ENDPOINT_URL = config(
    "CLOUDFLARE_R2_ENDPOINT_URL",
    default=f"https://{CLOUDFLARE_R2_ACCOUNT_ID}.r2.cloudflarestorage.com" if CLOUDFLARE_R2_ACCOUNT_ID else "",
)
CLOUDFLARE_R2_CUSTOM_DOMAIN = config("CLOUDFLARE_R2_CUSTOM_DOMAIN", default="")
CLOUDFLARE_R2_MEDIA_LOCATION = config("CLOUDFLARE_R2_MEDIA_LOCATION", default="media")

STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
    "default": {
        "BACKEND": "news.storage_backends.MediaStorage",
    },
}

# ==========================================================
# DEFAULT PK
# ==========================================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ==========================================================
# SECURITY
# ==========================================================

if DEBUG:
    # LOCAL DEVELOPMENT
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    SECURE_SSL_REDIRECT = False

else:
    # PRODUCTION
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True

    SECURE_PROXY_SSL_HEADER = (
        "HTTP_X_FORWARDED_PROTO",
        "https",
    )
