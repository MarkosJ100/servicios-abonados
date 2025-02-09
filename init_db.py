import os
import sys
import traceback
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Ensure the project root is in the Python path
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

# Set environment variables for database configuration
os.environ['DATABASE_URL'] = os.getenv('DATABASE_URL', 'sqlite:///servicios_abonados.db')

from app import app, db
from models import User, Registro  # Import all models
from sqlalchemy import inspect

def init_database():
    try:
        logger.info("Starting comprehensive database initialization...")
        
        # Determine database type
        db_url = os.getenv('DATABASE_URL', 'sqlite:///servicios_abonados.db')
        logger.info(f"Database URL: {db_url}")
        
        is_postgres = 'postgresql' in db_url.lower()
        
        with app.app_context():
            # Detailed logging about database initialization
            logger.info("Attempting to create database tables...")
            
            # For PostgreSQL, use create_all() without dropping
            if is_postgres:
                logger.info("Detected PostgreSQL database...")
                db.create_all()
            else:
                # For SQLite, drop and recreate
                logger.info("Detected SQLite database...")
                db.drop_all()
                db.create_all()
            
            # Verify table creation
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            logger.info(f"Existing tables: {tables}")
            
            # Detailed table column inspection
            for table in tables:
                columns = [col['name'] for col in inspector.get_columns(table)]
                logger.info(f"Columns in {table}: {columns}")
            
            # Create a default admin user if not exists
            existing_user = User.query.filter_by(username='marcos').first()
            if not existing_user:
                logger.info("Creating default admin user...")
                admin_user = User(
                    username='marcos', 
                    email='marcos@example.com', 
                    is_admin=True
                )
                admin_user.set_password('your_secure_password')  # Replace with a secure password
                
                db.session.add(admin_user)
                db.session.commit()
                logger.info("Default admin user created successfully!")
            else:
                logger.info("Admin user already exists.")
            
            logger.info("Database initialization completed successfully!")
    
    except Exception as e:
        logger.error("Critical error during database initialization:")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == '__main__':
    init_database()
