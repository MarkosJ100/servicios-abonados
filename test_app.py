import os
import sys
import unittest
from flask_login import login_user, current_user

# Ensure the project root is in the Python path
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

# Import the application and models
from app import create_app, db
from models import model_registry
from config import Config

class TestConfig(Config):
    """Configuration for testing."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class AppTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test environment once for the entire test class."""
        # Create a test application
        cls.app = create_app(TestConfig)
        
        # Create a test client
        cls.client = cls.app.test_client()
        
        # Create application context
        cls.app_context = cls.app.app_context()
        cls.app_context.push()
        
        # Get the models
        cls.User = model_registry.User
        cls.Registro = model_registry.Registro
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests are done."""
        # Drop all tables
        db.session.remove()
        db.drop_all()
        
        # Pop the application context
        cls.app_context.pop()
    
    def setUp(self):
        """Set up test environment before each test."""
        # Create all tables
        db.create_all()
    
    def tearDown(self):
        """Clean up after each test."""
        # Drop all tables
        db.session.remove()
        db.drop_all()
    
    def test_database_initialization(self):
        """Test that the database is initialized correctly."""
        # Check that the User model exists
        self.assertIsNotNone(self.User, "User model should be created")
        
        # Check that the Registro model exists
        self.assertIsNotNone(self.Registro, "Registro model should be created")
    
    def test_user_creation(self):
        """Test creating a new user."""
        # Create a test user
        test_user = self.User(
            username='testuser', 
            email='test@example.com', 
            is_admin=False
        )
        test_user.set_password('testpassword')
        
        # Add user to the database
        db.session.add(test_user)
        db.session.commit()
        
        # Retrieve the user
        retrieved_user = self.User.query.filter_by(username='testuser').first()
        
        # Assertions
        self.assertIsNotNone(retrieved_user, "User should be created in the database")
        self.assertEqual(retrieved_user.username, 'testuser', "Username should match")
        self.assertTrue(retrieved_user.check_password('testpassword'), "Password should be set correctly")
    
    def test_registro_creation(self):
        """Test creating a new registro."""
        from datetime import date
        
        # Create a test user first
        test_user = self.User(
            username='registrouser', 
            email='registro@example.com', 
            is_admin=False
        )
        test_user.set_password('testpassword')
        
        # Create a test registro
        test_registro = self.Registro(
            fecha=date.today(),
            numero_despacho='TEST001',
            importe=100.50,
            nombre_compania='Test Company',
            user=test_user
        )
        
        # Add to database
        db.session.add(test_user)
        db.session.add(test_registro)
        db.session.commit()
        
        # Retrieve the registro
        retrieved_registro = self.Registro.query.filter_by(numero_despacho='TEST001').first()
        
        # Assertions
        self.assertIsNotNone(retrieved_registro, "Registro should be created in the database")
        self.assertEqual(retrieved_registro.importe, 100.50, "Registro importe should match")
        self.assertEqual(retrieved_registro.user, test_user, "Registro should be associated with the user")
    
    def test_user_authentication(self):
        """Test user authentication mechanism."""
        # Create a test user
        test_user = self.User(
            username='authuser', 
            email='auth@example.com', 
            is_admin=False
        )
        test_user.set_password('correctpassword')
        
        # Add user to the database
        db.session.add(test_user)
        db.session.commit()
        
        # Test correct password
        self.assertTrue(test_user.check_password('correctpassword'), "Correct password should be verified")
        
        # Test incorrect password
        self.assertFalse(test_user.check_password('wrongpassword'), "Incorrect password should be rejected")

if __name__ == '__main__':
    unittest.main()
