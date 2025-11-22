#admin@123.com
from pathlib import Path
import os 

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

CSRF_TRUSTED_ORIGINS = [
    'https://6c55333ff0514a429d88d8735f8b667e.vfs.cloud9.us-east-1.amazonaws.com'
]

ALLOWED_HOSTS = [os.environ.get('EB_HOST', ''), '*.elasticbeanstalk.com']  


AWS_REGION = "us-east-1"
AWS_PARAM_BUCKET = "/bevflow/s3bucket-name"
AWS_ENV_ID = "24231584"  # NCI ID
BEVFLOW_ORDER_QUEUE_NAME = f"bevflow-orders-{AWS_ENV_ID}"
BEVFLOW_ORDER_TOPIC_NAME = f"bevflow-orders-topic-{AWS_ENV_ID}"

BEVFLOW_ORDER_QUEUE_NAME = f"bevflow-orders-{AWS_ENV_ID}"
BEVFLOW_ORDER_TOPIC_NAME = f"bevflow-orders-topic-{AWS_ENV_ID}"
BEVFLOW_LAMBDA_NAME = f"bevflow-order-processor-{AWS_ENV_ID}"
BEVFLOW_LAMBDA_SSM_PARAM = f"/bevflow/lambda-arn-{AWS_ENV_ID}"
BEVFLOW_SQS_SSM_PARAM = f"/bevflow/sqs-url-{AWS_ENV_ID}"
BEVFLOW_SNS_SSM_PARAM = f"/bevflow/sns-arn-{AWS_ENV_ID}"
BEVFLOW_DDB_TABLE = f"bevflow-orders-table-{AWS_ENV_ID}"
BEVFLOW_LOGS_BUCKET_PARAM = f"/bevflow/logs-bucket-{AWS_ENV_ID}"

# SES env var for Lambda; set a default or update in SSM later
SES_SENDER = "jeevanjotsingh070@gmail.com"

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-x+-=jy4mv)a_!g6@j*m3rbg4s)^b@)t^!i0-7tv=t1p8n0a=-v'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['6c55333ff0514a429d88d8735f8b667e.vfs.cloud9.us-east-1.amazonaws.com']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'bevflow',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'BevFreshFlow.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'bevflow', 'templates')],
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

WSGI_APPLICATION = 'BevFreshFlow.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'bevflow/static')]

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


