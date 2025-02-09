from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta

# Create a global database instance
db = SQLAlchemy()

class ModelRegistry:
    """
    A centralized registry for managing model creation and initialization.
    This helps avoid circular import issues and provides a clean way to 
    manage model relationships.
    """
    User = None
    Registro = None

    @classmethod
    def init_app(cls, db_instance):
        """
        Initialize models with the given database instance.
        
        :param db_instance: SQLAlchemy database instance
        :return: Tuple of User and Registro models
        """
        # Define User model
        class User(UserMixin, db_instance.Model):
            __tablename__ = 'users'
            
            id = db_instance.Column(db_instance.Integer, primary_key=True)
            username = db_instance.Column(db_instance.String(50), unique=True, nullable=False)
            email = db_instance.Column(db_instance.String(120), unique=True, nullable=False)
            password_hash = db_instance.Column(db_instance.String(255), nullable=False)
            is_admin = db_instance.Column(db_instance.Boolean, default=False)
            
            # Relationship with Registro
            registros = relationship('Registro', back_populates='user', cascade='all, delete-orphan')
            
            def set_password(self, password):
                """
                Set the password for the user by generating a secure hash.
                
                :param password: Plain text password
                """
                self.password_hash = generate_password_hash(password)
            
            def check_password(self, password):
                """
                Check if the provided password matches the stored hash.
                
                :param password: Plain text password to check
                :return: Boolean indicating password match
                """
                return check_password_hash(self.password_hash, password)
        
        # Define Registro model
        class Registro(db_instance.Model):
            __tablename__ = 'registros'
            
            id = db_instance.Column(db_instance.Integer, primary_key=True)
            fecha = db_instance.Column(db_instance.Date, nullable=False)
            numero_despacho = db_instance.Column(db_instance.String(50), unique=True, nullable=False)
            importe = db_instance.Column(db_instance.Float, nullable=False)
            nombre_compania = db_instance.Column(db_instance.String(100), nullable=False)
            estado_pago = db_instance.Column(db_instance.Boolean, default=False)
            pagado = db_instance.Column(db_instance.Boolean, default=False, nullable=False)
            created_at = db_instance.Column(db_instance.DateTime, default=datetime.utcnow)
            updated_at = db_instance.Column(db_instance.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
            fecha_pago = db_instance.Column(db_instance.Date, nullable=True)
            notas = db_instance.Column(db_instance.Text, nullable=True)
            user_id = db_instance.Column(db_instance.Integer, db_instance.ForeignKey('users.id'), nullable=True)
            user = relationship('User', back_populates='registros')
            is_deleted = db_instance.Column(db_instance.Boolean, default=False)

            def mark_as_paid(self, fecha_pago=None, notas=None):
                """
                Mark the record as paid.
                
                :param fecha_pago: Optional date of payment
                :param notas: Optional payment notes
                """
                self.pagado = True
                self.estado_pago = True
                self.fecha_pago = fecha_pago or datetime.now().date()
                if notas:
                    self.notas = notas
                db_instance.session.commit()

            def soft_delete(self):
                """
                Soft delete the record by marking it as deleted.
                """
                self.is_deleted = True
                db_instance.session.commit()

        # Store models in the registry
        cls.User = User
        cls.Registro = Registro
        
        return User, Registro

# Create a model registry instance
model_registry = ModelRegistry()
