import os
import sys
import logging
from datetime import datetime, timedelta

from app import app, db
from flask_migrate import Migrate, upgrade, init, migrate as migrate_cmd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('migration.log', mode='w')
    ]
)
logger = logging.getLogger(__name__)

migrate = Migrate(app, db)

def backup_database():
    """
    Create a backup of the current database before migration
    This is a basic implementation and might need adaptation based on your database type
    """
    try:
        from datetime import datetime
        import shutil
        
        # SQLite backup
        if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']:
            db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
            backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            logger.info(f"Creating SQLite database backup: {backup_path}")
            shutil.copy2(db_path, backup_path)
        
        logger.info("Database backup completed successfully")
    except Exception as e:
        logger.error(f"Database backup failed: {str(e)}", exc_info=True)

def run_migrations():
    try:
        logger.info("Starting database migrations...")
        
        # Log environment variables
        logger.info(f"DATABASE_URL: {os.environ.get('DATABASE_URL', 'Not set')}")
        
        # Backup existing database
        backup_database()
        
        with app.app_context():
            # Check if migrations folder exists
            if not os.path.exists('migrations'):
                logger.info("Initializing migrations...")
                init()
            
            # Prepare migration
            logger.info("Creating migration...")
            migration_message = f"Enhanced Registro model - {datetime.now()}"
            migrate_cmd(message=migration_message)
            
            # Upgrade database
            logger.info("Upgrading database...")
            upgrade()
            
            # Perform any necessary data migrations or transformations
            perform_data_migrations()
        
        logger.info("Migrations completed successfully.")
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}", exc_info=True)
        
        # Additional error context
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Log database connection details
        try:
            from sqlalchemy import create_engine
            engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
            with engine.connect() as connection:
                logger.info("Database connection successful")
        except Exception as conn_error:
            logger.error(f"Database connection error: {str(conn_error)}")
        
        sys.exit(1)

def perform_data_migrations():
    """
    Perform any necessary data transformations or migrations
    """
    from app import db
    from app import Registro, User
    
    try:
        # Example: Add default values for new columns
        logger.info("Performing data migrations...")
        
        # Update existing records with default values
        registros = Registro.query.all()
        for registro in registros:
            # Set created_at and updated_at if not already set
            if not registro.created_at:
                registro.created_at = datetime.utcnow()
            if not registro.updated_at:
                registro.updated_at = datetime.utcnow()
            
            # Set is_deleted to False for existing records
            if not hasattr(registro, 'is_deleted'):
                registro.is_deleted = False
        
        # Commit changes
        db.session.commit()
        
        logger.info("Data migrations completed successfully")
    except Exception as e:
        logger.error(f"Data migration failed: {str(e)}", exc_info=True)
        db.session.rollback()
        raise

if __name__ == '__main__':
    run_migrations()
