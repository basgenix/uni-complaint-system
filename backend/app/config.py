"""
Application Configuration Module
================================
This module contains all configuration classes for different environments.
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """
    Base configuration class.
    Contains settings common to all environments.
    """
    
    # Flask Core Settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'fallback-secret-key-for-development')
    
    # Database Settings
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///complaints.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False  # Set to True to see SQL queries in console
    
    # JWT Settings
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'fallback-jwt-secret-key')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        hours=int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES_HOURS', 24))
    )
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(
        days=int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES_DAYS', 30))
    )
    JWT_TOKEN_LOCATION = ['headers']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'
    
    # Application Settings
    APP_NAME = os.getenv('APP_NAME', 'University Complaints System')
    
    # File Upload Settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max file size
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'uploads')
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx'}
    
    # Pagination Settings
    ITEMS_PER_PAGE = 10
    MAX_ITEMS_PER_PAGE = 100


class DevelopmentConfig(Config):
    """
    Development environment configuration.
    """
    DEBUG = True
    SQLALCHEMY_ECHO = True  # Show SQL queries in development


class ProductionConfig(Config):
    """
    Production environment configuration.
    """
    DEBUG = False
    SQLALCHEMY_ECHO = False
    
    # In production, ensure these are set via environment variables
    @classmethod
    def init_app(cls, app):
        # Verify critical settings are configured
        assert os.getenv('SECRET_KEY'), 'SECRET_KEY environment variable must be set'
        assert os.getenv('JWT_SECRET_KEY'), 'JWT_SECRET_KEY environment variable must be set'


class TestingConfig(Config):
    """
    Testing environment configuration.
    """
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


# Configuration dictionary for easy access
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config():
    """
    Returns the appropriate configuration based on FLASK_ENV.
    """
    env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, config['default'])