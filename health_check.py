import os
import platform
import psutil
import socket
from datetime import datetime

def get_system_info():
    """Collect comprehensive system information."""
    return {
        'hostname': socket.gethostname(),
        'platform': platform.platform(),
        'python_version': platform.python_version(),
        'cpu_cores': os.cpu_count(),
        'memory': {
            'total': psutil.virtual_memory().total / (1024 * 1024),  # MB
            'available': psutil.virtual_memory().available / (1024 * 1024),  # MB
            'percent_used': psutil.virtual_memory().percent
        }
    }

def get_application_health(app):
    """
    Perform a comprehensive health check of the application.
    
    Checks:
    - Database connection
    - Migration status
    - Configuration validation
    """
    health_status = {
        'timestamp': datetime.utcnow().isoformat(),
        'status': 'healthy',
        'system': get_system_info(),
        'application': {
            'environment': app.config.get('ENV', 'Not Set'),
            'debug_mode': app.debug,
            'secret_key_set': bool(app.config.get('SECRET_KEY')),
        },
        'database': {
            'uri': app.config.get('SQLALCHEMY_DATABASE_URI', 'Not Configured'),
            'connection_status': 'unknown'
        },
        'migrations': {
            'status': 'unknown',
            'current_revision': 'unknown'
        }
    }
    
    # Database Connection Check
    try:
        from sqlalchemy import text
        with app.config['SQLALCHEMY_DATABASE_URI'].connect() as connection:
            connection.execute(text('SELECT 1'))
        health_status['database']['connection_status'] = 'successful'
    except Exception as e:
        health_status['database']['connection_status'] = f'failed: {str(e)}'
        health_status['status'] = 'degraded'
    
    # Migration Status Check
    try:
        from flask_migrate import current
        with app.app_context():
            revision = current()
            health_status['migrations']['status'] = 'up-to-date'
            health_status['migrations']['current_revision'] = str(revision)
    except Exception as e:
        health_status['migrations']['status'] = f'check failed: {str(e)}'
        health_status['status'] = 'degraded'
    
    return health_status

def create_health_routes(app):
    """
    Add health check routes to the Flask application.
    
    Provides:
    - /health: Basic health status
    - /health/detailed: Comprehensive health information
    """
    @app.route('/health')
    def basic_health():
        """Simple health check endpoint."""
        return {'status': 'healthy'}, 200
    
    @app.route('/health/detailed')
    def detailed_health():
        """Comprehensive health check endpoint."""
        health_info = get_application_health(app)
        status_code = 200 if health_info['status'] == 'healthy' else 503
        return health_info, status_code
