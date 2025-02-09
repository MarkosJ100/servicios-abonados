import os
import sys
import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from flask import request, current_app

def configure_logging(app):
    """
    Configure logging for the Flask application.
    Supports file logging and stdout logging based on configuration.
    """
    # Ensure logs directory exists
    log_dir = os.path.join(os.getcwd(), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Log file configuration
    log_file = os.path.join(log_dir, 'servicios_abonados.log')
    
    # Create formatters
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File Handler (Rotating)
    file_handler = RotatingFileHandler(
        log_file, 
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    
    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if app.debug else logging.WARNING)
    console_handler.setFormatter(formatter)
    
    # Application Logger
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    
    # Set logging level based on app configuration
    app.logger.setLevel(logging.DEBUG if app.debug else logging.INFO)
    
    # Prevent duplicate log entries
    app.logger.propagate = False

def log_startup_info(app):
    """Log application startup information."""
    app.logger.info(f"Application Starting")
    app.logger.info(f"Environment: {app.config.get('ENV', 'Not Set')}")
    app.logger.info(f"Debug Mode: {app.debug}")
    app.logger.info(f"Database URI: {app.config.get('SQLALCHEMY_DATABASE_URI', 'Not Configured')}")

def log_request_info(app):
    """
    Add request logging middleware.
    Logs basic information about each request.
    """
    @app.before_request
    def log_request_details():
        try:
            # Use current_app to ensure we have the correct application context
            current_app.logger.info(
                f"Request: {request.method} {request.path} "
                f"from {request.remote_addr}"
            )
        except Exception as e:
            # Fallback logging in case of any request logging issues
            print(f"Could not log request details: {e}")

def setup_application_logging(app):
    """
    Complete logging setup for the application.
    """
    configure_logging(app)
    log_startup_info(app)
    log_request_info(app)
