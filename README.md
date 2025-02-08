# Servicios de Abonados

## Descripción
Aplicación web para gestión de registros de servicios y seguimiento de pagos.

## Características
- Registro de servicios
- Importación de PDFs
- Gestión de estado de pago
- Exportación a Excel y PDF
- Resúmenes diarios y mensuales

## Requisitos
- Python 3.8+
- Flask
- SQLAlchemy
- Pandas
- PyPDF2
- Tabula-py
- Pytesseract

## Instalación
1. Clonar repositorio
2. Crear entorno virtual
3. Instalar dependencias:
   ```
   pip install -r requirements.txt
   ```

## Ejecución Local
```
python app.py
```

## Despliegue en Render.com

### Pasos para Desplegar
1. Crear cuenta en [Render](https://render.com/)
2. Conectar repositorio de GitHub
3. Crear un nuevo servicio web
4. Configurar:
   - Entorno: Python
   - Rama: main/master
   - Comando de construcción: `pip install -r requirements.txt`
   - Comando de inicio: `gunicorn app:app`

### Variables de Entorno
- `DATABASE_URL`: URL de base de datos PostgreSQL
- `SECRET_KEY`: Clave secreta para la aplicación

### Base de Datos
- Crear base de datos PostgreSQL gratuita en Render
- Copiar cadena de conexión en `DATABASE_URL`

## Solución de Problemas
- Verificar logs de despliegue
- Comprobar versiones de dependencias
- Asegurar permisos de base de datos

## Licencia
MIT
