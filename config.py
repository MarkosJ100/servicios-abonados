import os
import secrets
from datetime import timedelta

class Config:
    """Base configuration class with sensible defaults."""
    # Secret Key Management
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///servicios_abonados.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Application Settings
    DEBUG = False
    TESTING = False
    
    # Security Settings
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True
    
    # Session Configuration
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # Logging Configuration
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT', 'false').lower() == 'true'

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
