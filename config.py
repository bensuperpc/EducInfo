import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-prod'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///educinfo.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    
    # Application configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    
    # Logging
    LOG_FILE = 'logs/educinfo.log'
    LOG_LEVEL = 'INFO'
    
    # Admin par défaut
    DEFAULT_ADMIN_ID = os.environ.get('DEFAULT_ADMIN_ID', 'admin')
    DEFAULT_ADMIN_PASSWORD = os.environ.get('DEFAULT_ADMIN_PASSWORD', 'admin123')
    
    # OpenWeather API configuration
    WEATHER_API_KEY = '0b0b32c21c0e7a28f8dc6711e0c2e86b'
    WEATHER_CITY = os.environ.get('WEATHER_CITY', 'Paris')
    
    # CTS API configuration (la clé personnalisable sera enregistrée dans la base via WidgetConfig)
    CTS_BASE_URL = 'https://api.cts-strasbourg.eu'
    CTS_API_TOKEN = os.environ.get('CTS_API_TOKEN', '')  # Ajoutez cette ligne
    CTS_API_TIMEOUT = 10  # timeout en secondes

class DevelopmentConfig(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False

class ProductionConfig(Config):
    DEBUG = False
    @classmethod
    def init_app(cls, app):
        pass

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}