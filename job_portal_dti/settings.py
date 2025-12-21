from pathlib import Path
import environ
import os

# ------------------------
# BASE DIR
# ------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# ------------------------
# ENV SETTINGS
# ------------------------
env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))  # load .env file

# ------------------------
# SECURITY SETTINGS
# ------------------------
SECRET_KEY = env("SECRET_KEY", default="change-me")   # from .env
DEBUG = env("DEBUG", default="True") == "True"

ALLOWED_HOSTS = ["*"]

# ------------------------
# CSRF SETTINGS
# ------------------------
CSRF_TRUSTED_ORIGINS = [
    "https://skill-based-job-portal-management-system.onrender.com",
    "http://127.0.0.1:8000",
]


# ------------------------
# APPS
# ------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'my_App',
]

# ------------------------
# MIDDLEWARE
# ------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ------------------------
# URLS + TEMPLATES
# ------------------------
ROOT_URLCONF = 'job_portal_dti.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],           # Add templates folder path if you have one
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'job_portal_dti.wsgi.application'

# ------------------------
# EMAIL SETTINGS (FROM .env)
# ------------------------
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False

EMAIL_HOST_USER = env("EMAIL")               # from .env
EMAIL_HOST_PASSWORD = env("EMAIL_PASSWORD")  # from .env
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# ------------------------
# DATABASE
# ------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ------------------------
# PASSWORD VALIDATION
# ------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ------------------------
# INTERNATIONALIZATION
# ------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ------------------------
# STATIC & MEDIA
# ------------------------
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ------------------------
# DEFAULT AUTO FIELD
# ------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ------------------------
# LOGIN REDIRECT
# ------------------------
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'
