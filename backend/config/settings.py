from pathlib import Path
import os

from django.core.exceptions import ImproperlyConfigured


def get_env_variable(name: str):
    """Get environment variable or raise ImproperlyConfigured exception."""
    try:
        return os.environ.get(name)
    except KeyError:
        raise ImproperlyConfigured(f'Environment variable {name} not found.')


BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = get_env_variable('SECRET_KEY')
SANDBOX_API_URL = get_env_variable('SANDBOX_API_URL')
SANDBOX_API_HEADER = get_env_variable('SANDBOX_API_HEADER')
SANDBOX_API_TOKEN = get_env_variable('SANDBOX_API_TOKEN')

DEBUG = get_env_variable('DEBUG') == 'True'

ALLOWED_HOSTS = ['*']


class Constants:
    TOPIC_THRESHOLD_LOW: float = 61.0
    TOPIC_THRESHOLD_MEDIUM: float = 76.0
    TOPIC_THRESHOLD_HIGH: float = 91.0
    TOPIC_THEORY_MAX_POINTS: float = 40.0
    TOPIC_PRACTICE_MAX_POINTS: float = 60.0

    POINTS_EASY: float = 5.0
    POINTS_NORMAL: float = 9.0
    POINTS_HARD: float = 18.0

    ALGORITHM_SKILL_LEVEL_PLACEMENT_ANSWERS: int = 5
    ALGORITHM_SKILL_LEVEL_PLACEMENT_BONUS: float = 0.15
    ALGORITHM_SKILL_LEVEL_PLACEMENT_BIAS: float = 0.2
    ALGORITHM_SKILL_LEVEL_PLACEMENT_POINTS_COEFFICIENT: float = 0.5
    ALGORITHM_CORRECT_ANSWER_BONUS_EASY: float = 0.05
    ALGORITHM_CORRECT_ANSWER_BONUS_NORMAL: float = 0.075
    ALGORITHM_CORRECT_ANSWER_BONUS_HARD: float = 0.1
    AVERAGE_SKILL_LEVEL: float = 1.7

    ALGORITHM_DIFFICULTY_COEFFICIENT_EASY: float = 0.3
    ALGORITHM_DIFFICULTY_COEFFICIENT_NORMAL: float = 0.6
    ALGORITHM_DIFFICULTY_COEFFICIENT_HARD: float = 0.9

    ALGORITHM_SUITABLE_DIFFICULTY_PROBABILITY: float = 0.75

    SUB_TOPIC_POINTS_COEFFICIENT: float = 1 / 3

    MAX_NUMBER_OF_SUB_TOPICS: int = 5
    WEAKEST_LINK_MAX_PROBLEMS_PER_GROUP: int = 3
    WEAKEST_LINK_NUMBER_OF_PROBLEMS_TO_SOLVE: int = 2
    WEAKEST_LINK_PENALTY: float = 0.1

    PROBLEM_SIMILARITY_PERCENT: float = 0.66
    MIN_CORRECT_ANSWER_COEFFICIENT: float = 0.66

    JOIN_CODE_CHARACTERS: str = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ123456789'
    JOIN_CODE_LENGTH: int = 5

    MAX_NUMBER_OF_ATTEMPTS_PER_PRACTICE_PROBLEM: int = 2


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'courses',
    'answers',
    'accounts',
    'algorithm',
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

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates')
        ],
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

WSGI_APPLICATION = 'config.wsgi.application'

# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': get_env_variable('POSTGRES_NAME'),
        'USER': get_env_variable('POSTGRES_USER'),
        'PASSWORD': get_env_variable('POSTGRES_PASSWORD'),
        'HOST': get_env_variable('POSTGRES_HOST'),
        'PORT': get_env_variable('POSTGRES_PORT'),
    }
}

# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = 'static/'

STATICFILES_DIRS = [
    'static/'
]

STATIC_ROOT = '/var/www/als/static/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

SECURE_CROSS_ORIGIN_OPENER_POLICY = None

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname}\t{asctime}\t{module} ::: {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'django.log',
            'formatter': 'verbose'
        },
    },
    'root': {
        'handlers': ['file'],
        'level': 'DEBUG',
    },
}
