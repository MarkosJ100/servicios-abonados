import os
from flask import Flask, render_template, request, redirect, url_for, send_file, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
import pandas as pd
import tabula
import pytesseract
from pdf2image import convert_from_path
import re
import subprocess
import traceback
from PyPDF2 import PdfReader

# Configuración de la aplicación
app = Flask(__name__)

# Configuración de base de datos para producción
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL', 
    'sqlite:///servicios_abonados.db'
).replace('postgres://', 'postgresql://')  # Compatibilidad con Render
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get(
    'SECRET_KEY', 
    'clave_desarrollo_segura_2024'
)

# Inicializar base de datos y migración
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Configuración de Tesseract OCR con manejo de errores
try:
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
except Exception as e:
    print("Advertencia: Tesseract OCR no encontrado. La importación de PDFs sin tablas podría no funcionar.")
    pytesseract = None

print("Iniciando aplicación...")

class Registro(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.Date, nullable=False)
    numero_despacho = db.Column(db.String(50), nullable=False)
    importe = db.Column(db.Float, nullable=False)
    nombre_compania = db.Column(db.String(100), nullable=False)
    estado = db.Column(db.String(20), default='Pendiente')
    pagado = db.Column(db.Boolean, default=False, nullable=False)

    def __repr__(self):
        return f'<Registro {self.id}>'

# Funciones de verificación de dependencias
def is_java_installed():
    try:
        subprocess.run(['java', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def is_poppler_installed():
    try:
        subprocess.run(['pdftoppm', '-h'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def init_db():
    with app.app_context():
        # Eliminar todas las tablas existentes
        db.drop_all()
        
        # Crear todas las tablas
        db.create_all()
        
        # Commit para asegurar cambios
        db.session.commit()

init_db()

@app.route('/')
def index():
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

@app.route('/registrar', methods=['POST'])
def registrar():
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

@app.route('/borrar/<int:id>')
def borrar(id):
    registro = Registro.query.get_or_404(id)
    db.session.delete(registro)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/cambiar_estado/<int:id>')
def cambiar_estado(id):
    registro = Registro.query.get_or_404(id)
    registro.estado = 'Pagado' if registro.estado == 'Pendiente' else 'Pendiente'
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/eliminar/<int:id>', methods=['GET'])
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
def resumen_diario():
    if request.method == 'POST':
        fecha = datetime.strptime(request.form['fecha'], '%Y-%m-%d').date()
        registros = Registro.query.filter_by(fecha=fecha).all()
        total = sum(registro.importe for registro in registros)
        return render_template('resumen_diario.html', registros=registros, fecha=fecha, total=total)
    return render_template('resumen_diario.html')

@app.route('/resumen_mensual', methods=['GET', 'POST'])
def resumen_mensual():
    if request.method == 'POST':
        fecha = datetime.strptime(request.form['fecha'], '%Y-%m-%d').date()
        registros = Registro.query.filter(
            db.extract('year', Registro.fecha) == fecha.year,
            db.extract('month', Registro.fecha) == fecha.month
        ).all()
        total = sum(registro.importe for registro in registros)
        return render_template('resumen_mensual.html', registros=registros, fecha=fecha, total=total)
    return render_template('resumen_mensual.html')

@app.route('/exportar_excel')
def exportar_excel():
    registros = Registro.query.all()
    df = pd.DataFrame([(r.id, r.fecha, r.numero_despacho, r.importe, r.nombre_compania, r.estado) 
                       for r in registros], 
                      columns=['ID', 'Fecha', 'Número de Despacho', 'Importe', 'Compañía', 'Estado'])
    ruta_excel = 'servicios_abonados.xlsx'
    df.to_excel(ruta_excel, index=False)
    return send_file(ruta_excel, as_attachment=True)

@app.route('/exportar_pdf')
def exportar_pdf():
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

@app.route('/importar_pdf', methods=['GET', 'POST'])
def importar_pdf():
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

@app.route('/cambiar_estado/<int:id>', methods=['GET'])
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
    print("Aplicación iniciada. Abre http://localhost:5000 en tu navegador.")
    app.run(host='0.0.0.0', port=5000, debug=True)

except Exception as e:
    print("Error al iniciar la aplicación:")
    print(traceback.format_exc())
    sys.exit(1)
