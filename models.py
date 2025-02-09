from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
import hashlib

# Create a global database instance
db = SQLAlchemy()

class ServiceProvider(db.Model):
    """
    Represent different service providers in the telecommunications ecosystem
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    contact_email = db.Column(db.String(120), unique=True)
    phone_number = db.Column(db.String(20))
    
    # Relationship with services
    services = relationship('ServiceType', back_populates='provider')
    
    def generate_provider_report(self, start_date, end_date):
        """
        Generate comprehensive provider-specific report
        """
        total_services = sum(
            service.count_services(start_date, end_date) 
            for service in self.services
        )
        total_revenue = sum(
            service.calculate_revenue(start_date, end_date) 
            for service in self.services
        )
        
        return {
            'provider_name': self.name,
            'total_services': total_services,
            'total_revenue': total_revenue,
            'average_service_value': total_revenue / total_services if total_services > 0 else 0
        }

class ServiceType(db.Model):
    """
    Detailed service type with advanced tracking
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    
    # Provider relationship
    provider_id = db.Column(
        db.Integer, 
        db.ForeignKey('service_provider.id'),
        nullable=False
    )
    provider = relationship('ServiceProvider', back_populates='services')
    
    # Pricing and configuration
    base_rate = db.Column(db.Float, nullable=False)
    pricing_model = db.Column(db.String(50))  # flat, per_unit, tiered
    
    # Service-specific metadata
    description = db.Column(db.Text)
    service_category = db.Column(db.String(50))
    
    def count_services(self, start_date, end_date):
        """
        Count services for this specific service type
        """
        return Registro.query.filter(
            Registro.service_type_id == self.id,
            Registro.fecha.between(start_date, end_date)
        ).count()
    
    def calculate_revenue(self, start_date, end_date):
        """
        Calculate total revenue for this service type
        """
        return db.session.query(
            db.func.sum(Registro.total_amount)
        ).filter(
            Registro.service_type_id == self.id,
            Registro.fecha.between(start_date, end_date),
            Registro.estado_pago == True
        ).scalar() or 0

class User(UserMixin, db.Model):
    """
    Enhanced user model for service management
    """
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Enhanced user roles
    is_admin = db.Column(db.Boolean, default=False)
    is_accountant = db.Column(db.Boolean, default=False)
    
    # Company-specific details
    company_name = db.Column(db.String(100), nullable=True)
    phone_number = db.Column(db.String(20), nullable=True)
    
    # Relationship with service records
    registros = relationship('Registro', 
        back_populates='user',
        cascade='all, delete-orphan',
        lazy='dynamic'
    )
    
    def set_password(self, password):
        """
        Set the password securely
        """
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """
        Check the provided password
        """
        return check_password_hash(self.password_hash, password)
    
    def can_access_registro(self, registro):
        """
        Advanced access control
        """
        return (
            self.is_admin or 
            self.is_accountant or 
            registro.user_id == self.id
        )
    
    def generate_monthly_report(self, year, month):
        """
        Generate a comprehensive monthly report
        """
        from sqlalchemy import extract
        
        monthly_registros = self.registros.filter(
            extract('year', Registro.fecha) == year,
            extract('month', Registro.fecha) == month
        )
        
        return {
            'total_services': monthly_registros.count(),
            'total_revenue': sum(registro.total_amount for registro in monthly_registros),
            'unpaid_services': monthly_registros.filter(Registro.estado_pago == False).count()
        }

class Registro(db.Model):
    """
    Comprehensive service record with advanced billing
    """
    __tablename__ = 'registros'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Service identification
    numero_despacho = db.Column(db.String(50), unique=True, nullable=False)
    fecha = db.Column(db.Date, nullable=False, default=datetime.now().date)
    
    # Relationships
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = relationship('User', back_populates='registros')
    
    service_type_id = db.Column(
        db.Integer, 
        db.ForeignKey('service_type.id'),
        nullable=False
    )
    service_type = relationship('ServiceType')
    
    # Financial details
    base_price = db.Column(db.Float, nullable=False)
    additional_charges = db.Column(db.Float, default=0)
    discount_percentage = db.Column(db.Float, default=0)
    
    # Billing and payment tracking
    billing_cycle = db.Column(db.String(20))  # monthly, quarterly, annual
    estado_pago = db.Column(db.Boolean, default=False)
    fecha_pago = db.Column(db.Date, nullable=True)
    
    # Service-specific details
    nombre_compania = db.Column(db.String(100), nullable=False)
    tipo_servicio = db.Column(db.String(50), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    
    # Audit and tracking
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    
    @property
    def total_amount(self):
        """
        Dynamic total amount calculation
        """
        base_total = self.base_price + self.additional_charges
        discounted_total = base_total * (1 - self.discount_percentage)
        return discounted_total * (1 + 0.16)  # 16% tax rate
    
    def mark_as_paid(self, payment_method='efectivo', notas=None):
        """
        Advanced payment marking
        """
        if self.estado_pago:
            raise ValueError("Este registro ya ha sido pagado")
        
        self.estado_pago = True
        self.fecha_pago = datetime.now().date()
        
        # Create payment record
        payment = PagoRegistro(
            registro_id=self.id,
            monto=self.total_amount,
            metodo_pago=payment_method,
            notas=notas
        )
        
        db.session.add(payment)
        db.session.commit()
        
        return payment
    
    @classmethod
    def get_overdue_services(cls, days_overdue=30):
        """
        Identify overdue services
        """
        threshold_date = datetime.now().date() - timedelta(days=days_overdue)
        return cls.query.filter(
            cls.estado_pago == False,
            cls.created_at < threshold_date
        ).all()

class PagoRegistro(db.Model):
    """
    Detailed payment tracking
    """
    id = db.Column(db.Integer, primary_key=True)
    registro_id = db.Column(db.Integer, db.ForeignKey('registros.id'))
    
    # Payment details
    monto = db.Column(db.Float, nullable=False)
    fecha_pago = db.Column(db.DateTime, default=datetime.utcnow)
    metodo_pago = db.Column(db.String(50), nullable=False)
    notas = db.Column(db.Text, nullable=True)
    
    # Relationship with Registro
    registro = relationship('Registro', backref='pagos')

# Create a model registry to manage models
model_registry = {
    'ServiceProvider': ServiceProvider,
    'ServiceType': ServiceType,
    'User': User,
    'Registro': Registro,
    'PagoRegistro': PagoRegistro
}
