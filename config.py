import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration class."""
    # Secret Key Management
    SECRET_KEY = os.getenv('SECRET_KEY', 'your_default_secret_key')
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL', 
        'sqlite:///servicios_abonados.db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_BINDS = {}  # Explicitly set to an empty dictionary
    
    # Application Settings
    DEBUG = os.getenv('FLASK_DEBUG', 'True') == 'True'
    TESTING = False
    
    # Security Settings
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True
    
    # Session Configuration
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'app.log')
    LOG_TO_STDOUT = os.getenv('LOG_TO_STDOUT', 'false').lower() == 'true'
    
    # Additional configuration options
    CSRF_ENABLED = True
    
    # Render-specific settings
    RENDER_ENVIRONMENT = os.getenv('RENDER_ENVIRONMENT', 'development')

class DevelopmentConfig(Config):
    """Development-specific configuration."""
    DEBUG = True
    SQLALCHEMY_ECHO = True  # Log SQL statements

class ProductionConfig(Config):
    """Production-specific configuration."""
    DEBUG = False
    
class TestingConfig(Config):
    """Testing-specific configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

def get_config():
    """
    Select configuration based on environment.
    Supports: development, production, testing
    """
    config_mapping = {
        'development': DevelopmentConfig,
        'production': ProductionConfig,
        'testing': TestingConfig
    }
    
    # Prioritize environment variable, default to development
    env = os.environ.get('FLASK_ENV', 'development').lower()
    return config_mapping.get(env, DevelopmentConfig)
