# Servicios de Abonados

## Descripción
Aplicación web para gestión de registros de servicios y seguimiento de pagos.

## Estado de Despliegue
[![Render](https://img.shields.io/badge/Render-Deployed-green)](https://servicios-abonados.onrender.com)

🌐 **URL del Servicio**: https://servicios-abonados.onrender.com

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

## Instalación Local
1. Clonar repositorio
2. Crear entorno virtual
3. Instalar dependencias:
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

## Ejecución Local
```bash
python app.py
```

## Despliegue en Render.com

### Configuración
- **Plataforma**: Render
- **Tipo de Servicio**: Web Service
- **Entorno**: Python 3.8
- **Rama**: main

### Variables de Entorno Necesarias
- `DATABASE_URL`: Generado automáticamente por Render
- `SECRET_KEY`: Clave secreta para la aplicación

### Pasos de Despliegue
1. Conectar repositorio de GitHub
2. Configurar build command: `pip install -r requirements.txt`
3. Configurar start command: `gunicorn app:app`

## Consideraciones de Despliegue
- Plan gratuito con "spin down" después de inactividad
- Tiempo de inicio inicial puede ser hasta 50 segundos
- Recomendado usar servicio de monitoreo

## Solución de Problemas
- Verificar logs de despliegue
- Comprobar versiones de dependencias
- Asegurar permisos de base de datos

## Licencia
MIT License
