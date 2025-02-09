import os
import sys
import traceback
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),  # Print to console
        logging.FileHandler('database_init.log')  # Log to file
    ]
)
logger = logging.getLogger(__name__)

# Ensure the project root is in the Python path
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

# Set environment variables for database configuration
os.environ['DATABASE_URL'] = os.getenv('DATABASE_URL', 'sqlite:///servicios_abonados.db')

def init_database():
    try:
        # Import required modules
        from flask import Flask
        from flask_sqlalchemy import SQLAlchemy
        from flask_migrate import Migrate
        from config import get_config
        from models import model_registry

        # Create a new Flask application
        app = Flask(__name__)
        
        # Configure the application
        app.config.from_object(get_config())
        
        # Explicitly set SQLALCHEMY_BINDS to an empty dictionary
        app.config['SQLALCHEMY_BINDS'] = {}
        
        # Initialize database
        db = SQLAlchemy(app)
        migrate = Migrate(app, db)
        
        # Initialize models using the registry
        User, Registro = model_registry.init_app(db)
        
        logger.info(" Iniciando inicialización de base de datos...")
        logger.info(f" Ruta del proyecto: {project_root}")
        
        # Determine database type
        db_url = os.getenv('DATABASE_URL', 'sqlite:///servicios_abonados.db')
        logger.info(f" URL de base de datos: {db_url}")
        
        is_postgres = 'postgresql' in db_url.lower()
        
        with app.app_context():
            # Detailed logging about database initialization
            logger.info(" Intentando crear tablas de base de datos...")
            
            # For PostgreSQL, use create_all() without dropping
            if is_postgres:
                logger.info(" Base de datos PostgreSQL detectada...")
                db.create_all()
            else:
                # For SQLite, drop and recreate
                logger.info(" Base de datos SQLite detectada...")
                db.drop_all()
                db.create_all()
            
            # Verify table creation
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            logger.info(f" Tablas existentes: {tables}")
            
            # Detailed table column inspection
            for table in tables:
                columns = [col['name'] for col in inspector.get_columns(table)]
                logger.info(f" Columnas en {table}: {columns}")
            
            # Create a default admin user if not exists
            logger.info(" Verificando usuario administrador...")
            existing_user = User.query.filter_by(username='marcos').first()
            if not existing_user:
                logger.info(" Creando usuario administrador predeterminado...")
                admin_user = User(
                    username='marcos', 
                    email='marcos@example.com', 
                    is_admin=True
                )
                admin_user.set_password('your_secure_password')  # Replace with a secure password
                
                db.session.add(admin_user)
                db.session.commit()
                logger.info(" Usuario administrador creado exitosamente!")
            else:
                logger.info(" Usuario administrador ya existe.")
            
            logger.info(" Inicialización de base de datos completada con éxito!")
    
    except Exception as e:
        logger.error(" Error crítico durante la inicialización de la base de datos:")
        logger.error(f" Detalles del error: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == '__main__':
    init_database()
