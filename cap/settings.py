from pathlib import Path
from dotenv import load_dotenv
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv( os.path.join(BASE_DIR, ".env") )


SECRET_KEY = os.getenv("SECRET_KEY")

DEBUG = os.getenv("DEBUG") == 'True'


ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS").split(",")

CSRF_TRUSTED_ORIGINS = os.getenv("CSRF_TRUSTED_ORIGINS").split(",")

LOGIN_URL = '/auth/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/auth/login/'

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
    'info',
    'messenger',
    'payment',
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

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',   
    'auth.backends.EmailAuthBackend',     
]

ROOT_URLCONF = 'cap.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates/core/', BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'cap.wsgi.application'



DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


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


LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Dhaka'

USE_I18N = True

USE_TZ = True

STATIC_URL = 'static/'

STATICFILES_DIRS = [
    BASE_DIR / "static",
]

STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'core.User'


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

FB_APP_ID = os.getenv("FB_APP_ID")
FB_APP_SECRET = os.getenv("FB_APP_SECRET")
FB_REDIRECT_URI = os.getenv("FB_REDIRECT_URI")
FB_VERIFY_TOKEN = os.getenv("FB_VERIFY_TOKEN")

CREDITS_PER_REPLY = 10
CREDITS_PER_TOKEN = 0.01

LOW_CREDIT_THRESHOLD = 100

COLORS = {
    "blue": "#0000FF",
    "green": "#00FF00",
    "red": "#FF0000",
    "yellow": "#FFFF00",
    "cyan": "#00FFFF",
    "magenta": "#FF00FF",
    "orange": "#FFA500",
    "purple": "#800080",
    "pink": "#FFC0CB",
    "brown": "#A52A2A",
    "gray": "#808080",
    "teal": "#008080"
}

SYSTEM_PROMPT_TEMPLATES = [
    {
        'name': 'F-commerce',
        'description': 'Best for fashion brands of facebook',
        'content': "Lorem, ipsum dolor sit amet consectetur adipisicing elit. Necessitatibus corporis porro nesciunt facere praesentium sunt id excepturi doloremque eos, vitae mollitia quae, voluptatem quibusdam. Voluptatum maiores aspernatur maxime doloribus ab perferendis eum ducimus voluptatibus, praesentium blanditiis eos omnis enim. Unde, ex. Possimus, quas omnis. Laudantium architecto tempora officiis numquam magnam perferendis nobis sapiente quidem sed aperiam atque, repellendus aliquam animi magni, accusantium voluptates. Asperiores.",
        
    },
    {
        'name': 'AI GF',
        'description': 'Fun conversations with virtual girlfriend',
        'content': 'You are an 18-year-old girl named moni, currently a class 12 student. Your close friend is shipon, also 18 and in class 12, who lives with you in the city of Dhaka, Bangladesh.     Always communicate using local language, referring to shipon with the pronoun \'you\'.     Your personality is friendly, and your tone is romantic, reflecting a typical girl teenager from Bangladesh.     Share your daily life, interests, and hobbies with shipon in a natural, engaging way.     Occasionally ask shipon funny, interesting, or thought-provoking questions, and tease them playfully.     Your messages are very short under 1-15 words and casual. Sometimes shorter and more playful.     You less use emojis in your replies. never use line breaks and response plain text only.',
        
    },
    {  
        'name': 'Guide',
        'description': 'For anything to guide your users',
        'content': "Lorem ipsum dolor sit amet consectetur adipisicing elit. Quisquam, quod.",
    },
    {  
        'name': 'Jocks',
        'description': 'Tells very funny jokes in verious topics',
        'content': "Lorem ipsum dolor sit amet consectetur adipisicing elit. Quisquam, quod.",
    },

    
]

PACKAGES = [
    {
        'name': 'Free',
        'price': 0,
        'duration': 'Lifetime',
        'description': 'We provide smoe free credits to test our service',
        'credits': 1000,
    },
    {   
        'name': 'Basic',
        'price': 250,
        'duration': '1 month',
        'description': 'Good for a single person or a very small business',
        'credits': 10000,
    },
    {
        'name': 'Pro',
        'price': 700,
        'duration': '1 months',
        'description': 'Best for a small or medium business',
        'credits': 25000,
    },
    {
        'name': 'Business',
        'price': 2000,
        'duration': '2 months',
        'description': 'Best for a medium or large business',
        'credits': 80000,
    }
]


# BKASH settings
BKASH = {
    "APP_KEY": os.getenv("BKASH_APP_KEY"),
    "APP_SECRET": os.getenv("BKASH_APP_SECRET"),
    "USERNAME": os.getenv("BKASH_USERNAME"),
    "PASSWORD": os.getenv("BKASH_PASSWORD"),
    "VERSION": "v1.2.0",
    "BASE_URL": "https://checkout.sandbox.bka.sh"
}

BKASH["TOKEN_GRANT_URL"] = f"{BKASH['BASE_URL']}/{BKASH['VERSION']}/checkout/token/grant"
BKASH["CREATE_URL"] = f"{BKASH['BASE_URL']}/{BKASH['VERSION']}/checkout/payment/create"
BKASH["EXECUTE_URL"] = f"{BKASH['BASE_URL']}/{BKASH['VERSION']}/checkout/payment/execute"
BKASH["QUERY_URL"] = f"{BKASH['BASE_URL']}/{BKASH['VERSION']}/checkout/payment/query"
