# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
.\venv\Scripts\Activate.ps1

# Instalar dependencias
pip install -r requirements.txt
pip install pyinstaller pillow

# Crear ícono
python create_icon.py

# Crear ejecutable
pyinstaller --onefile --windowed --name "Servicios_Abonados" --icon=icon.ico app_windows.py

# Crear carpeta dist si no existe
New-Item -ItemType Directory -Force -Path dist

# Copiar ejecutable a carpeta dist
Copy-Item -Path ".\Servicios_Abonados.exe" -Destination ".\dist\Servicios_Abonados.exe"

Write-Host "Ejecutable creado en la carpeta dist"
Pause
