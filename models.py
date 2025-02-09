from datetime import datetime, timedelta
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class ModelRegistry:
    """
    A central registry to manage model creation and initialization.
    This helps avoid circular import issues and provides a flexible way to create models.
    """
    _db = None
    User = None
    Registro = None

    @classmethod
    def init_app(cls, db):
        """
        Initialize the model registry with a SQLAlchemy database instance.
        
        :param db: SQLAlchemy database instance
        """
        cls._db = db
        cls._create_models()
        return cls.User, cls.Registro

    @classmethod
    def _create_models(cls):
        """
        Create model classes dynamically using the database instance.
        """
        if not cls._db:
            raise ValueError("Database not initialized. Call init_app first.")

        class User(UserMixin, cls._db.Model):
            id = cls._db.Column(cls._db.Integer, primary_key=True)
            username = cls._db.Column(cls._db.String(50), unique=True, nullable=False)
            email = cls._db.Column(cls._db.String(120), unique=True, nullable=False)
            password_hash = cls._db.Column(cls._db.String(255), nullable=False)
            is_admin = cls._db.Column(cls._db.Boolean, default=False)
            registros = cls._db.relationship('Registro', backref='user', lazy=True)

            def set_password(self, password):
                """
                Set the password hash for the user.
                
                :param password: Plain text password to be hashed
                """
                self.password_hash = generate_password_hash(password)

            def check_password(self, password):
                """
                Check if the provided password matches the stored hash.
                
                :param password: Plain text password to check
                :return: Boolean indicating if password is correct
                """
                return check_password_hash(self.password_hash, password)

        class Registro(cls._db.Model):
            """
            Represents a record or transaction in the system.
            """
            id = cls._db.Column(cls._db.Integer, primary_key=True)
            fecha = cls._db.Column(cls._db.Date, nullable=False)
            numero_despacho = cls._db.Column(cls._db.String(50), nullable=False, unique=True, index=True)
            importe = cls._db.Column(cls._db.Float, nullable=False)
            nombre_compania = cls._db.Column(cls._db.String(100), nullable=False, index=True)
            estado = cls._db.Column(cls._db.String(20), default='Pendiente')
            pagado = cls._db.Column(cls._db.Boolean, default=False, nullable=False)
            created_at = cls._db.Column(cls._db.DateTime, default=datetime.utcnow)
            updated_at = cls._db.Column(cls._db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
            fecha_pago = cls._db.Column(cls._db.Date, nullable=True)
            notas = cls._db.Column(cls._db.Text, nullable=True)
            user_id = cls._db.Column(cls._db.Integer, cls._db.ForeignKey('user.id'), nullable=True)
            is_deleted = cls._db.Column(cls._db.Boolean, default=False)

            def mark_as_paid(self, fecha_pago=None, notas=None):
                """
                Mark the record as paid.
                
                :param fecha_pago: Optional date of payment
                :param notas: Optional payment notes
                """
                self.pagado = True
                self.estado = 'Pagado'
                self.fecha_pago = fecha_pago or datetime.now().date()
                if notas:
                    self.notas = notas
                cls._db.session.commit()

            def soft_delete(self):
                """
                Soft delete the record by marking it as deleted.
                """
                self.is_deleted = True
                cls._db.session.commit()

        # Store the created models in the registry
        cls.User = User
        cls.Registro = Registro

# Export the model registry for use in other modules
model_registry = ModelRegistry
