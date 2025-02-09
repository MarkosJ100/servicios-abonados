from app import app, db
from models import User, Registro  # Import all models

def init_database():
    with app.app_context():
        # Drop all existing tables (optional, use carefully)
        db.drop_all()
        
        # Create all tables
        db.create_all()
        
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
        
        print("Database initialized successfully!")

if __name__ == '__main__':
    init_database()
