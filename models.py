from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

def init_models(db):
    """
    Initialize models with the SQLAlchemy database instance.
    This helps avoid circular import issues.
    """
    class User(UserMixin, db.Model):
        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(50), unique=True, nullable=False)
        email = db.Column(db.String(120), unique=True, nullable=False)
        password_hash = db.Column(db.String(255), nullable=False)
        is_admin = db.Column(db.Boolean, default=False)
        registros = db.relationship('Registro', backref='user', lazy=True)

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

    class Registro(db.Model):
        """
        Represents a record or transaction in the system.
        """
        id = db.Column(db.Integer, primary_key=True)
        fecha = db.Column(db.Date, nullable=False)
        numero_despacho = db.Column(db.String(50), nullable=False, unique=True, index=True)
        importe = db.Column(db.Float, nullable=False)
        nombre_compania = db.Column(db.String(100), nullable=False, index=True)
        estado = db.Column(db.String(20), default='Pendiente')
        pagado = db.Column(db.Boolean, default=False, nullable=False)
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
        fecha_pago = db.Column(db.Date, nullable=True)
        notas = db.Column(db.Text, nullable=True)
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
        is_deleted = db.Column(db.Boolean, default=False)

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
            db.session.commit()

        def soft_delete(self):
            """
            Soft delete the record by marking it as deleted.
            """
            self.is_deleted = True
            db.session.commit()

    return User, Registro
