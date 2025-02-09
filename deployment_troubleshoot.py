import os
import platform
import subprocess
import importlib
import secrets
import sys

def check_system_environment():
    print("System Environment Check:")
    print(f"- OS: {platform.system()} {platform.release()}")
    print(f"- Python Version: {sys.version}")
    print(f"- Python Implementation: {platform.python_implementation()}")
    print(f"- Python Executable: {sys.executable}")

def check_dependencies():
    print("\nDependency Check:")
    dependencies = ['numpy', 'pandas', 'flask', 'sqlalchemy', 'flask_migrate', 'flask_login', 'gunicorn']
    
    for dep in dependencies:
        try:
            module = importlib.import_module(dep)
            ver = getattr(module, '__version__', 'Unknown')
            print(f"✓ {dep} is installed (Version: {ver})")
        except ImportError:
            print(f"✗ {dep} is NOT installed")

def check_environment_variables():
    print("\nEnvironment Variables:")
    critical_vars = ['DATABASE_URL', 'SECRET_KEY']
    
    for var in critical_vars:
        value = os.environ.get(var)
        if value:
            print(f"✓ {var} is set")
        else:
            print(f"✗ {var} is NOT set")

def setup_environment_variables():
    # Set DATABASE_URL if not already set
    if 'DATABASE_URL' not in os.environ:
        os.environ['DATABASE_URL'] = 'sqlite:///servicios_abonados.db'
        print("✓ Set default DATABASE_URL to SQLite database")
    
    # Set SECRET_KEY if not already set
    if 'SECRET_KEY' not in os.environ:
        secret_key = secrets.token_hex(16)
        os.environ['SECRET_KEY'] = secret_key
        print(f"✓ Generated and set SECRET_KEY: {secret_key}")

def test_database_connection():
    print("\nDatabase Connection Test:")
    try:
        # Dynamically import app and db to handle potential import errors
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        import app
        with app.app.app_context():
            app.db.engine.connect()
            print("✓ Database connection successful")
    except ImportError as e:
        print(f"✗ Could not import app module: {e}")
    except Exception as e:
        print(f"✗ Database connection failed: {e}")

def initialize_and_upgrade_migrations():
    print("\nMigration Test:")
    try:
        from flask import Flask
        from flask_sqlalchemy import SQLAlchemy
        from flask_migrate import Migrate, init, upgrade

        # Import your app and models
        sys.path.append(os.getcwd())
        from app import app, db  # Adjust this import based on your project structure

        # Ensure migrations directory exists
        if not os.path.exists('migrations'):
            print("Initializing database migrations...")
            with app.app_context():
                Migrate(app, db)
                init()
                print("✓ Migrations initialized")

        # Upgrade database
        with app.app_context():
            try:
                upgrade()
                print("✓ Database migrations upgraded successfully")
            except Exception as migration_error:
                print(f"✗ Migration upgrade failed: {migration_error}")
                import traceback
                traceback.print_exc()
        
    except Exception as e:
        print(f"✗ Migration process failed: {e}")
        import traceback
        traceback.print_exc()

def main():
    print("Deployment Troubleshooting Diagnostic")
    print("=====================================")
    
    setup_environment_variables()
    check_system_environment()
    check_dependencies()
    check_environment_variables()
    test_database_connection()
    initialize_and_upgrade_migrations()

if __name__ == '__main__':
    main()
