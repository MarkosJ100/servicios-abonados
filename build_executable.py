import os
import sys
import subprocess
import shutil
import traceback

def run_command(command, capture_output=True, shell=True, print_output=True):
    """
    Ejecuta un comando en el sistema y muestra la salida.
    """
    print(f"Ejecutando: {command}")
    try:
        result = subprocess.run(
            command,
            shell=shell,
            capture_output=capture_output,
            text=True,
            check=True
        )
        if result.stdout and print_output:
            print(result.stdout)
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"Error al ejecutar el comando: {e}")
        return e.returncode
    except Exception as e:
        print(f"Error inesperado: {e}")
        traceback.print_exc()
        return 1

def main():
    try:
        print(f"Python versión: {sys.version}")
        print(f"Plataforma: {sys.platform}")
        print(f"Directorio actual: {os.getcwd()}")

        # Rutas absolutas
        base_dir = r"c:\Users\marti\Dropbox\Proyectos\servicios_abonados"
        app_script = os.path.join(base_dir, "app_windows.py")
        icon_file = os.path.join(base_dir, "icon.ico")
        dist_dir = os.path.join(base_dir, "dist")
        exe_name = "Servicios_Abonados.exe"

        # Verificar que el script principal exista
        if not os.path.exists(app_script):
            print(f"Error: El archivo '{app_script}' no existe.")
            return 1

        # Limpiar directorio de distribución anterior
        if os.path.exists(dist_dir):
            try:
                shutil.rmtree(dist_dir)
            except Exception as e:
                print(f"Error al limpiar directorio {dist_dir}: {e}")
        os.makedirs(dist_dir)

        # Verificar archivos
        print(f"Archivos en el directorio base:")
        for f in os.listdir(base_dir):
            print(f)

        # Verificar existencia de archivos específicos
        print(f"Verificando archivos:")
        print(f"Script principal: {app_script} - Existe: {os.path.exists(app_script)}")
        print(f"Ícono: {icon_file} - Existe: {os.path.exists(icon_file)}")

        # Comando PyInstaller
        pyinstaller_cmd = (
            "pyinstaller "
            "--onefile "
            "--windowed "
            f"--name \"{os.path.splitext(exe_name)[0]}\" "
            f"--icon=\"{icon_file}\" "
            "--hidden-import=pandas "
            "--hidden-import=tkinter "
            "--hidden-import=reportlab "
            "--hidden-import=openpyxl "
            "--hidden-import=tkcalendar "  
            f"\"{app_script}\""
        )

        print("Creando ejecutable con PyInstaller...")
        print(f"Comando: {pyinstaller_cmd}")
        result = run_command(pyinstaller_cmd, capture_output=False)
        
        if result != 0:
            print("Error al generar el ejecutable.")
            return 1

        # Verificar si el ejecutable se creó correctamente
        exe_path = os.path.join(dist_dir, exe_name)
        if os.path.exists(exe_path):
            print(f"Ejecutable creado en: {exe_path}")
            print(f"Tamaño: {os.path.getsize(exe_path)} bytes")
        else:
            print("Error: No se encontró el ejecutable.")
            return 1

        return 0
    except Exception as e:
        print(f"Error inesperado en la compilación: {e}")
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
