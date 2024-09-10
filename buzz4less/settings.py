from pathlib import Path
import os
from django.contrib.messages import constants as messages
import ssl
import certifi
import dj_database_url
import cloudinary
import cloudinary.uploader
import cloudinary.api

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Set the SSL certificate file path
os.environ['SSL_CERT_FILE'] = certifi.where()

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("SECRET_KEY")
# SECRET_KEY = 'django-insecure-8$@5^1++h3^b_5wu&omho*1%)l!rmpn%r6o0x-&8p4x7z08!bk'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DEBUG", "False").lower() == "false"

ALLOWED_HOSTS = ['buzz4less.onrender.com', 'localhost', '127.0.0.1', 'www.buzzforless.com']

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'pages.apps.PagesConfig',
    'services.apps.ServicesConfig',
    'accounts.apps.AccountsConfig',
    'contacts.apps.ContactsConfig',
    'django.contrib.humanize',
    'cloudinary',
    'cloudinary_storage',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
]

ROOT_URLCONF = 'buzz4less.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR), 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'buzz4less.wsgi.application'

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'buzz4lessdb',
        'USER': 'macintosh',
        'PASSWORD': 'buzz4less',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

database_url = "postgresql://buzz4lessdb_user:rOgzRBopY0F0MpJzuKbvhXArdaG4L2hs@dpg-crbekkt6l47c73d4qi00-a.oregon-postgres.render.com/buzz4lessdb"
DATABASES["default"] = dj_database_url.parse(database_url)
# postgresql://buzz4lessdb_user:rOgzRBopY0F0MpJzuKbvhXArdaG4L2hs@dpg-crbekkt6l47c73d4qi00-a.oregon-postgres.render.com/buzz4lessdb

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATIC_URL = 'static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'buzz4less/static')
]

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Cloudinary for media file storage
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
STRIPE_PUBLISHABLE_KEY = 'pk_live_51PonNDCDCOrfP3WnPIiJAlJRL8CBQNVJVHGjtA8c3IIq1skvkkYlS3QXgeHiprkM4naTpR4xtxT8WW6xNhaWQAvb005Z0vKVjk'

# settings.py
STRIPE_ENDPOINT_SECRET = os.getenv('STRIPE_ENDPOINT_SECRET')

MESSAGE_TAGS = {
    messages.ERROR: 'danger'
}

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 465
EMAIL_USE_SSL = True
EMAIL_HOST_USER = "chinemeremokpara93@gmail.com"
EMAIL_HOST_PASSWORD = "sjjv gzyd skqs ukge"

DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# SSL Configuration
SSL_CERT_FILE = certifi.where()

# Optional: Override SSL verification for development (not recommended for production)
ssl._create_default_https_context = ssl._create_unverified_context  # Uncomment this for development only

CLOUDINARY_STORAGE = {
    'CLOUD_NAME': 'dystjcg1j',
    'API_KEY': '716197218755935',
    'API_SECRET': 'Fq1AYvBjvSZy7M6rSbY8W9ABDWo',
}

cloudinary.config(
    cloud_name=CLOUDINARY_STORAGE['CLOUD_NAME'],
    api_key=CLOUDINARY_STORAGE['API_KEY'],
    api_secret=CLOUDINARY_STORAGE['API_SECRET']
)
