import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "django-insecure-change-me-in-production")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DJANGO_DEBUG", "True").lower() == "true"

ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

# Application definition
INSTALLED_APPS = [
    "unfold",  # Must be before django.contrib.admin
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "core",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "core.middleware.AdminOnlyMiddleware",  # Custom middleware for admin-only access
]

ROOT_URLCONF = "lotus_admin.urls"

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

WSGI_APPLICATION = "lotus_admin.wsgi.application"

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME", "postgres"),
        "USER": os.environ.get("DB_USER", "postgres"),
        "PASSWORD": os.environ.get("DB_PASSWORD", "postgres"),
        "HOST": os.environ.get("DB_HOST", "localhost"),
        "PORT": os.environ.get("DB_PORT", "5432"),
        "OPTIONS": {
            "options": "-c search_path=source,public",
        },
    }
}

# Custom authentication backend
AUTHENTICATION_BACKENDS = [
    "core.backends.LotusUserBackend",
    "django.contrib.auth.backends.ModelBackend",  # Fallback
]

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Unfold (Django Admin Theme) Configuration
# https://unfoldadmin.com/
UNFOLD = {
    "SITE_TITLE": "Lotus Admin Portal",
    "SITE_HEADER": "Lotus Admin",
    "SITE_URL": "/",
    "SITE_ICON": None,  # You can add a path to your icon here
    "SITE_LOGO": None,  # You can add a path to your logo here
    "SITE_SYMBOL": "settings",  # Icon shown in the sidebar
    "SITE_FAVICONS": None,
    "SHOW_HISTORY": True,  # Show history button in admin
    "SHOW_VIEW_ON_SITE": True,  # Show "view on site" button
    "ENVIRONMENT": os.environ.get("ENVIRONMENT", "development").title(),  # Environment label
    "DASHBOARD_CALLBACK": None,  # Optional: customize dashboard
    "LOGIN": {
        "image": None,  # Custom login image
        "redirect_after": None,  # Redirect after login
    },
    "STYLES": [],  # Custom CSS styles
    "SCRIPTS": [],  # Custom JavaScript scripts
}

# Admin-only access settings
ADMIN_ONLY_ACCESS = True  # Set to False to allow non-admin users
ADMIN_ROLE_NAME = "Admin"  # Role name from users table that grants admin access
ADMIN_ALLOWED_GROUPS = [
    "product_manager",
    "ml_engineer",
]  # Django groups that can access admin interface
