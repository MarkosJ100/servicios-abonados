import os
import sys
import traceback
from flask import Flask, render_template, request, redirect, url_for, send_file, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from email_validator import validate_email, EmailNotValidError
from datetime import datetime, timedelta
import pandas as pd
import tabula
import pytesseract
from pdf2image import convert_from_path
import re
import subprocess
from PyPDF2 import PdfReader
from sqlalchemy import func

# Import our new configuration and logging modules
from config import get_config
from logging_config import setup_application_logging
from health_check import create_health_routes

# Create Flask application with configuration
app = Flask(__name__)
app.config.from_object(get_config())

# Setup logging
setup_application_logging(app)

# Error handling
@app.errorhandler(Exception)
def handle_exception(e):
    # Log the error
    app.logger.error(f"Unhandled Exception: {str(e)}")
    app.logger.error(traceback.format_exc())
    
    # Return a user-friendly error response
    return jsonify({
        'error': 'Internal Server Error',
        'message': str(e),
        'trace': traceback.format_exc()
    }), 500

# Inicializar base de datos y migración
try:
    db = SQLAlchemy(app)
    migrate = Migrate(app, db)
except Exception as db_init_error:
    app.logger.error(f"Database Initialization Error: {db_init_error}")
    raise

# Configuración de Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Add health check routes
create_health_routes(app)

# Modelos de base de datos
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Registro(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.Date, nullable=False)
    numero_despacho = db.Column(db.String(50), nullable=False, unique=True, index=True)
    importe = db.Column(db.Float, nullable=False)
    nombre_compania = db.Column(db.String(100), nullable=False, index=True)
    estado = db.Column(db.String(20), default='Pendiente')
    pagado = db.Column(db.Boolean, default=False, nullable=False)
    
    # New fields for enhanced tracking
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    fecha_pago = db.Column(db.Date, nullable=True)
    notas = db.Column(db.Text, nullable=True)
    
    # Optional: Link to user who created the record
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    user = db.relationship('User', backref=db.backref('registros', lazy=True))
    
    # Soft delete
    is_deleted = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<Registro {self.numero_despacho}>'
    
    @classmethod
    def get_overdue_payments(cls, days=30):
        """
        Retrieve overdue payments not yet settled
        :param days: Number of days to consider a payment overdue
        :return: List of overdue registros
        """
        threshold_date = datetime.now().date() - timedelta(days=days)
        return cls.query.filter(
            cls.fecha < threshold_date,
            cls.pagado == False,
            cls.is_deleted == False
        ).all()
    
    @classmethod
    def get_company_summary(cls, company_name=None):
        """
        Generate financial summary for a company or all companies
        :param company_name: Optional company name to filter
        :return: Dictionary with summary statistics
        """
        query = cls.query.filter(cls.is_deleted == False)
        
        if company_name:
            query = query.filter(cls.nombre_compania == company_name)
        
        total_importe = db.session.query(func.sum(cls.importe)).scalar() or 0
        total_registros = query.count()
        pagados = query.filter(cls.pagado == True).count()
        pendientes = query.filter(cls.pagado == False).count()
        
        return {
            'total_importe': total_importe,
            'total_registros': total_registros,
            'pagados': pagados,
            'pendientes': pendientes,
            'porcentaje_pagado': (pagados / total_registros * 100) if total_registros > 0 else 0
        }
    
    def mark_as_paid(self, fecha_pago=None, notas=None):
        """
        Mark the registro as paid
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
        Soft delete the registro
        """
        self.is_deleted = True
        db.session.commit()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Rutas de autenticación
@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            user = User.query.filter_by(username=username).first()
            
            if user and user.check_password(password):
                login_user(user)
                flash('Inicio de sesión exitoso', 'success')
                return redirect(url_for('index'))
            else:
                flash('Nombre de usuario o contraseña incorrectos', 'error')
        
        return render_template('login.html')
    except Exception as e:
        app.logger.error(f"Error in login route: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(e),
            'trace': traceback.format_exc()
        }), 500

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    try:
        if request.method == 'POST':
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']
            
            # Validar email
            try:
                valid = validate_email(email)
                email = valid.email
            except EmailNotValidError:
                flash('Correo electrónico inválido', 'error')
                return redirect(url_for('registro'))
            
            # Verificar si el usuario ya existe
            if User.query.filter_by(username=username).first():
                flash('Nombre de usuario ya existe', 'error')
                return redirect(url_for('registro'))
            
            if User.query.filter_by(email=email).first():
                flash('Correo electrónico ya registrado', 'error')
                return redirect(url_for('registro'))
            
            # Crear nuevo usuario
            new_user = User(username=username, email=email)
            new_user.set_password(password)
            
            db.session.add(new_user)
            db.session.commit()
            
            flash('Registro exitoso. Por favor, inicia sesión.', 'success')
            return redirect(url_for('login'))
        
        return render_template('registro.html')
    except Exception as e:
        app.logger.error(f"Error in registro route: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(e),
            'trace': traceback.format_exc()
        }), 500

@app.route('/logout')
@login_required
def logout():
    try:
        logout_user()
        flash('Sesión cerrada exitosamente', 'success')
        return redirect(url_for('login'))
    except Exception as e:
        app.logger.error(f"Error in logout route: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(e),
            'trace': traceback.format_exc()
        }), 500

# Resto de las rutas existentes requieren login
@app.route('/')
@login_required
def index():
    try:
        # Ordenar registros por fecha de manera descendente (más reciente primero)
        registros = Registro.query.order_by(Registro.fecha.desc()).all()
        
        # Calcular totales
        total_importe = sum(registro.importe for registro in registros)
        total_registros = len(registros)
        
        # Agrupar por compañía
        companias = {}
        for registro in registros:
            if registro.nombre_compania not in companias:
                companias[registro.nombre_compania] = {
                    'total_importe': 0,
                    'total_registros': 0
                }
            companias[registro.nombre_compania]['total_importe'] += registro.importe
            companias[registro.nombre_compania]['total_registros'] += 1
        
        return render_template('index.html', 
                               registros=registros, 
                               total_importe=total_importe, 
                               total_registros=total_registros,
                               companias=companias)
    except Exception as e:
        app.logger.error(f"Error in index route: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(e),
            'trace': traceback.format_exc()
        }), 500

@app.route('/registrar', methods=['POST'])
@login_required
def registrar():
    try:
        fecha = datetime.strptime(request.form['fecha'], '%Y-%m-%d').date()
        numero_despacho = request.form['numero_despacho']
        importe = float(request.form['importe'])
        nombre_compania = request.form['nombre_compania']
        estado = 'Pagado' if request.form.get('estado') else 'Pendiente'

        nuevo_registro = Registro(
            fecha=fecha, 
            numero_despacho=numero_despacho, 
            importe=importe, 
            nombre_compania=nombre_compania, 
            estado=estado
        )
        db.session.add(nuevo_registro)
        db.session.commit()
        return redirect(url_for('index'))
    except Exception as e:
        app.logger.error(f"Error in registrar route: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(e),
            'trace': traceback.format_exc()
        }), 500

@app.route('/borrar/<int:id>')
@login_required
def borrar(id):
    try:
        registro = Registro.query.get_or_404(id)
        db.session.delete(registro)
        db.session.commit()
        return redirect(url_for('index'))
    except Exception as e:
        app.logger.error(f"Error in borrar route: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(e),
            'trace': traceback.format_exc()
        }), 500

@app.route('/cambiar_estado/<int:id>')
@login_required
def cambiar_estado(id):
    try:
        registro = Registro.query.get_or_404(id)
        registro.estado = 'Pagado' if registro.estado == 'Pendiente' else 'Pendiente'
        db.session.commit()
        return redirect(url_for('index'))
    except Exception as e:
        app.logger.error(f"Error in cambiar_estado route: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(e),
            'trace': traceback.format_exc()
        }), 500

@app.route('/eliminar/<int:id>', methods=['GET'])
@login_required
def eliminar(id):
    try:
        # Buscar el registro por ID
        registro = Registro.query.get_or_404(id)
        
        # Eliminar el registro
        db.session.delete(registro)
        db.session.commit()
        
        # Mensaje de éxito
        flash(f'Registro {id} eliminado exitosamente', 'success')
    except Exception as e:
        # Revertir cambios en caso de error
        db.session.rollback()
        flash(f'Error al eliminar el registro: {str(e)}', 'error')
    
    # Redirigir a la página principal
    return redirect(url_for('index'))

@app.route('/resumen_diario', methods=['GET', 'POST'])
@login_required
def resumen_diario():
    try:
        if request.method == 'POST':
            fecha = datetime.strptime(request.form['fecha'], '%Y-%m-%d').date()
            registros = Registro.query.filter_by(fecha=fecha).all()
            total = sum(registro.importe for registro in registros)
            return render_template('resumen_diario.html', registros=registros, fecha=fecha, total=total)
        return render_template('resumen_diario.html')
    except Exception as e:
        app.logger.error(f"Error in resumen_diario route: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(e),
            'trace': traceback.format_exc()
        }), 500

@app.route('/resumen_mensual', methods=['GET', 'POST'])
@login_required
def resumen_mensual():
    try:
        if request.method == 'POST':
            fecha = datetime.strptime(request.form['fecha'], '%Y-%m-%d').date()
            registros = Registro.query.filter(
                db.extract('year', Registro.fecha) == fecha.year,
                db.extract('month', Registro.fecha) == fecha.month
            ).all()
            total = sum(registro.importe for registro in registros)
            return render_template('resumen_mensual.html', registros=registros, fecha=fecha, total=total)
        return render_template('resumen_mensual.html')
    except Exception as e:
        app.logger.error(f"Error in resumen_mensual route: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(e),
            'trace': traceback.format_exc()
        }), 500

@app.route('/exportar_excel')
@login_required
def exportar_excel():
    try:
        registros = Registro.query.all()
        df = pd.DataFrame([(r.id, r.fecha, r.numero_despacho, r.importe, r.nombre_compania, r.estado) 
                           for r in registros], 
                          columns=['ID', 'Fecha', 'Número de Despacho', 'Importe', 'Compañía', 'Estado'])
        ruta_excel = 'servicios_abonados.xlsx'
        df.to_excel(ruta_excel, index=False)
        return send_file(ruta_excel, as_attachment=True)
    except Exception as e:
        app.logger.error(f"Error in exportar_excel route: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(e),
            'trace': traceback.format_exc()
        }), 500

@app.route('/exportar_pdf')
@login_required
def exportar_pdf():
    try:
        registros = Registro.query.all()
        ruta_pdf = 'servicios_abonados.pdf'
        
        doc = SimpleDocTemplate(ruta_pdf, pagesize=letter)
        styles = getSampleStyleSheet()
        title_style = styles['Title']
        
        elementos = []
        elementos.append(Paragraph("Registro de Servicios de Abonados", title_style))
        
        datos = [['ID', 'Fecha', 'Número de Despacho', 'Importe', 'Compañía', 'Estado']]
        datos.extend([(str(r.id), str(r.fecha), r.numero_despacho, f"€{r.importe:.2f}", r.nombre_compania, r.estado) for r in registros])
        
        tabla = Table(datos)
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elementos.append(tabla)
        doc.build(elementos)
        
        return send_file(ruta_pdf, as_attachment=True)
    except Exception as e:
        app.logger.error(f"Error in exportar_pdf route: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(e),
            'trace': traceback.format_exc()
        }), 500

@app.route('/importar_pdf', methods=['GET', 'POST'])
@login_required
def importar_pdf():
    try:
        if request.method == 'POST':
            if 'archivo' not in request.files:
                flash('No se ha seleccionado ningún archivo', 'error')
                return redirect(request.url)
            
            archivo = request.files['archivo']
            
            if archivo.filename == '':
                flash('No se ha seleccionado ningún archivo', 'error')
                return redirect(request.url)
            
            if archivo and archivo.filename.lower().endswith('.pdf'):
                # Guardar el archivo temporalmente
                ruta_pdf = os.path.join('uploads', archivo.filename)
                os.makedirs('uploads', exist_ok=True)
                archivo.save(ruta_pdf)
                
                try:
                    # Verificar dependencias
                    if not is_java_installed():
                        flash('Java no está instalado. La extracción de tablas no funcionará.', 'warning')
                    
                    tablas = []
                    texto_completo = ""
                    
                    # Intentar extraer tablas con tabula si Java está instalado
                    if is_java_installed():
                        try:
                            tablas = tabula.read_pdf(ruta_pdf, pages='all', multiple_tables=True)
                        except Exception as e:
                            flash(f'Error al extraer tablas: {str(e)}', 'warning')
                    
                    # Intentar extraer texto con métodos alternativos
                    if not tablas:
                        # Método 1: Usar PyPDF2 para extraer texto
                        try:
                            from PyPDF2 import PdfReader
                            reader = PdfReader(ruta_pdf)
                            for page in reader.pages:
                                texto_completo += page.extract_text()
                        except Exception as e:
                            flash(f'Error al extraer texto con PyPDF2: {str(e)}', 'warning')
                        
                        # Método 2: Usar OCR si Poppler y Tesseract están disponibles
                        if not texto_completo and is_poppler_installed() and pytesseract is not None:
                            try:
                                imagenes = convert_from_path(ruta_pdf)
                                for imagen in imagenes:
                                    texto_completo += pytesseract.image_to_string(imagen)
                            except Exception as e:
                                flash(f'Error al usar OCR: {str(e)}', 'warning')
                    
                    # Extraer registros del texto
                    if texto_completo:
                        # Usar expresiones regulares para extraer datos
                        patron = r'(\d{4}-\d{2}-\d{2})\s+(\w+)\s+(\d+\.\d{2})\s+(\w+)'
                        registros_encontrados = re.findall(patron, texto_completo)
                        
                        # Insertar registros encontrados
                        for registro in registros_encontrados:
                            nuevo_registro = Registro(
                                fecha=datetime.strptime(registro[0], '%Y-%m-%d').date(),
                                numero_despacho=registro[1],
                                importe=float(registro[2]),
                                nombre_compania=registro[3]
                            )
                            db.session.add(nuevo_registro)
                    
                    # Procesar tablas de Tabula si existen
                    if tablas:
                        for tabla in tablas:
                            for _, fila in tabla.iterrows():
                                nuevo_registro = Registro(
                                    fecha=datetime.strptime(fila['Fecha'], '%Y-%m-%d').date(),
                                    numero_despacho=fila['Número de Despacho'],
                                    importe=float(fila['Importe']),
                                    nombre_compania=fila['Compañía']
                                )
                                db.session.add(nuevo_registro)
                    
                    db.session.commit()
                    
                    if registros_encontrados or tablas:
                        flash('Registros importados exitosamente', 'success')
                    else:
                        flash('No se pudieron extraer registros del PDF', 'warning')
                
                except Exception as e:
                    db.session.rollback()
                    flash(f'Error al importar el PDF: {str(e)}', 'error')
                    print(traceback.format_exc())  # Imprimir traza completa para depuración
                
                # Eliminar archivo temporal
                os.remove(ruta_pdf)
                
                return redirect(url_for('index'))
            
            flash('Formato de archivo no válido. Solo se permiten PDFs', 'error')
            return redirect(request.url)
        
        return render_template('importar_pdf.html')
    except Exception as e:
        app.logger.error(f"Error in importar_pdf route: {e}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': str(e),
            'trace': traceback.format_exc()
        }), 500

@app.route('/cambiar_estado/<int:id>', methods=['GET'])
@login_required
def cambiar_estado_pago(id):
    try:
        # Buscar el registro por ID
        registro = Registro.query.get_or_404(id)
        
        # Cambiar el estado de pago
        registro.pagado = not registro.pagado
        db.session.commit()
        
        # Mensaje de éxito
        estado = "pagado" if registro.pagado else "pendiente"
        flash(f'Registro {id} marcado como {estado}', 'success')
    except Exception as e:
        # Revertir cambios en caso de error
        db.session.rollback()
        flash(f'Error al cambiar el estado del registro: {str(e)}', 'error')
    
    # Redirigir a la página principal
    return redirect(url_for('index'))

@app.route('/cambiar_estado_multiple', methods=['POST'])
@login_required
def cambiar_estado_multiple():
    try:
        # Obtener los IDs de los registros seleccionados
        registro_ids = request.form.getlist('registros')
        
        if not registro_ids:
            flash('No se seleccionaron registros', 'warning')
            return redirect(url_for('index'))
        
        # Obtener el estado desde la URL (por defecto 'pagado')
        estado = request.args.get('estado', 'pagado')
        
        # Buscar los registros
        registros = Registro.query.filter(Registro.id.in_(registro_ids)).all()
        
        # Cambiar el estado de los registros
        for registro in registros:
            registro.pagado = (estado == 'pagado')
        
        # Guardar cambios
        db.session.commit()
        
        # Mensaje de éxito
        mensaje = f'Se han marcado {len(registros)} registros como {estado}.'
        flash(mensaje, 'success')
    
    except Exception as e:
        # Revertir cambios en caso de error
        db.session.rollback()
        flash(f'Error al cambiar el estado de los registros: {str(e)}', 'error')
    
    # Redirigir a la página principal
    return redirect(url_for('index'))

if __name__ == '__main__':
    # Ensure database is created
    with app.app_context():
        try:
            db.create_all()
            app.logger.info("Database tables created successfully")
        except Exception as db_create_error:
            app.logger.error(f"Error creating database tables: {db_create_error}")
            raise

    # Log startup information
    app.logger.info("Aplicación iniciada")
    try:
        app.run(
            host='0.0.0.0', 
            port=5000, 
            debug=app.config.get('DEBUG', True)
        )
    except Exception as e:
        app.logger.error(f"Error starting application: {e}")
        app.logger.error(traceback.format_exc())
        raise
