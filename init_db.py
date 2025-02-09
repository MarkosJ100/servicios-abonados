import os
import sys
import traceback

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
        print("Starting database initialization...")
        
        # Determine database type
        db_url = os.getenv('DATABASE_URL', 'sqlite:///servicios_abonados.db')
        is_postgres = 'postgresql' in db_url.lower()
        
        with app.app_context():
            # For PostgreSQL, use create_all() without dropping
            if is_postgres:
                print("Detected PostgreSQL database...")
                db.create_all()
            else:
                # For SQLite, drop and recreate
                print("Detected SQLite database...")
                db.drop_all()
                db.create_all()
            
            # Verify table creation
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"Existing tables: {tables}")
            
            # Check if User table exists and has correct columns
            if 'user' in tables:
                columns = [col['name'] for col in inspector.get_columns('user')]
                print(f"User table columns: {columns}")
            
            # Create a default admin user if not exists
            existing_user = User.query.filter_by(username='marcos').first()
            if not existing_user:
                admin_user = User(
                    username='marcos', 
                    email='marcos@example.com', 
                    is_admin=True
                )
                admin_user.set_password('your_secure_password')  # Replace with a secure password
                
                db.session.add(admin_user)
                db.session.commit()
                print("Default admin user created successfully!")
            else:
                print("Admin user already exists.")
            
            print("Database initialization completed successfully!")
    
    except Exception as e:
        print("Error during database initialization:")
        print(traceback.format_exc())
        sys.exit(1)

if __name__ == '__main__':
    init_database()
