@echo off
echo Preparando entorno para crear ejecutable de Servicios Abonados

REM Crear entorno virtual
python -m venv venv
call venv\Scripts\activate

REM Instalar dependencias
pip install -r requirements.txt

REM Crear ejecutable con PyInstaller
pyinstaller --onefile --windowed --name "Servicios_Abonados" --icon=icon.ico app_windows.py

REM Mover ejecutable a carpeta de distribución
mkdir dist 2>nul
move "dist\Servicios_Abonados.exe" "dist\Servicios_Abonados.exe"

echo Ejecutable creado en la carpeta dist
pause
