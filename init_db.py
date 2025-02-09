import os
import sys
import traceback

# Ensure the project root is in the Python path
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

from app import app, db
from models import User, Registro  # Import all models

def init_database():
    try:
        with app.app_context():
            # Ensure all tables are created
            print("Starting database initialization...")
            
            # Drop all existing tables (use carefully in production)
            db.drop_all()
            
            # Create all tables defined in models
            db.create_all()
            
            # Verify table creation
            print("Checking table existence...")
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"Existing tables: {tables}")
            
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
