import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///chatgpt_orders.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Payment Gateway (Midtrans)
    MIDTRANS_SERVER_KEY = os.environ.get('MIDTRANS_SERVER_KEY')
    MIDTRANS_CLIENT_KEY = os.environ.get('MIDTRANS_CLIENT_KEY')
    MIDTRANS_IS_PRODUCTION = os.environ.get('MIDTRANS_IS_PRODUCTION', 'false').lower() == 'true'
    
    # ChatGPT Admin Credentials
    CHATGPT_ADMIN_EMAIL = os.environ.get('CHATGPT_ADMIN_EMAIL')
    CHATGPT_ADMIN_PASSWORD = os.environ.get('CHATGPT_ADMIN_PASSWORD')
    # Use admin URL instead of team URL based on interface
    CHATGPT_ADMIN_URL = os.environ.get('CHATGPT_ADMIN_URL') or 'https://chatgpt.com/admin?tab=members'
    
    # Redis Configuration
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    
    # Celery Configuration
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_ACCEPT_CONTENT = ['json']
    CELERY_TIMEZONE = 'UTC'
    CELERY_ENABLE_UTC = True
    
    # Email Configuration
    SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
    FROM_EMAIL = os.environ.get('FROM_EMAIL') or 'noreply@yourdomain.com'
    
    # Admin Notifications
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL')
    ADMIN_TELEGRAM_BOT_TOKEN = os.environ.get('ADMIN_TELEGRAM_BOT_TOKEN')
    ADMIN_TELEGRAM_CHAT_ID = os.environ.get('ADMIN_TELEGRAM_CHAT_ID')
    
    # Security
    WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET')
    ALLOWED_WEBHOOK_IPS = os.environ.get('ALLOWED_WEBHOOK_IPS', '').split(',')
    
    # Selenium Configuration
    CHROME_BINARY_PATH = os.environ.get('CHROME_BINARY_PATH')
    CHROMEDRIVER_PATH = os.environ.get('CHROMEDRIVER_PATH')
    SELENIUM_HEADLESS = os.environ.get('SELENIUM_HEADLESS', 'true').lower() == 'true'
    SELENIUM_TIMEOUT = int(os.environ.get('SELENIUM_TIMEOUT', '30'))
    
    # Rate Limiting
    RATELIMIT_STORAGE_URL = os.environ.get('RATE_LIMIT_STORAGE_URL') or 'redis://localhost:6379/1'
    
    # Package Configuration
    PACKAGES = {
        'chatgpt_plus_1_month': {
            'name': 'Individual Plan',
            'price': 250000,
            'duration': '1 Bulan',
            'description': 'Akses GPT-4 Unlimited dengan email pribadi sebagai Member'
        },
        'team_package': {
            'name': 'Team Plan',
            'price': 800000,
            'duration': '1 Bulan',
            'description': 'Sampai 5 akun tim sebagai Member dengan akses penuh'
        }
    }

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = True

class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_ECHO = False

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}