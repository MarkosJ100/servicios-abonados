import tkinter as tk
from tkinter import messagebox, filedialog, ttk
from tkcalendar import Calendar  # Importar calendario
import platform
import os
import datetime
import csv
import os.path
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
import subprocess  # Para ejecutar comandos de sistema
import io
import re
from tkcalendar import DateEntry
import logging

# Configurar logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class WindowsApp:
    def __init__(self, master):
        self.master = master
        master.title("Servicios Abonados")
        master.geometry("1200x700")  # Reducir tamaño de la ventana
        
        # Protocolo de cierre personalizado
        master.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Bandera para rastrear cambios sin guardar
        self.cambios_sin_guardar = False
        
        # Frame principal
        self.main_frame = tk.Frame(master)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Frame izquierdo para campos de entrada
        self.left_frame = tk.Frame(self.main_frame)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
        
        # Frame derecho para botones
        self.right_frame = tk.Frame(self.main_frame)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10)
        
        # Título más grande y centrado
        self.label = tk.Label(
            self.left_frame, 
            text="Servicios Abonados", 
            font=("Arial", 20, "bold"),  # Reducir tamaño de fuente
            fg="navy"  # Color más llamativo
        )
        self.label.pack(pady=15)  # Reducir espaciado
        
        # Eliminar información del sistema
        
        # Frame para campos de entrada
        self.input_frame = tk.Frame(self.left_frame)
        self.input_frame.pack(fill=tk.X, padx=20)
        
        # Campos de entrada con etiquetas alineadas verticalmente
        campos = [
            ("Fecha:", "date"),
            ("Número de Despacho:", "despacho"),
            ("Nombre del Abonado:", "abonado"),
            ("Importe (€):", "importe")
        ]
        
        for i, (label_text, attr_name) in enumerate(campos):
            # Frame para cada campo
            campo_frame = tk.Frame(self.input_frame)
            campo_frame.pack(fill=tk.X, pady=8, padx=20)  # Reducir espaciado
            
            # Etiqueta
            label = tk.Label(
                campo_frame, 
                text=label_text, 
                font=("Arial", 11), 
                width=20, 
                anchor='w'
            )
            label.pack(side=tk.LEFT, padx=(0, 10))
            
            # Campo de entrada o botón especial para fecha
            if attr_name == 'date':
                # Botón para abrir calendario
                date_button = tk.Button(
                    campo_frame, 
                    text="Seleccionar Fecha", 
                    command=self.open_calendar, 
                    width=20, 
                    height=1,
                    font=("Arial", 9)
                )
                date_button.pack(side=tk.LEFT, padx=(0, 10))
                
                # Campo de entrada de fecha
                self.date_entry = tk.Entry(
                    campo_frame, 
                    width=30, 
                    state='readonly', 
                    font=("Arial", 11)
                )
                self.date_entry.pack(side=tk.LEFT)
                
                # Establecer fecha actual por defecto
                self.selected_date = datetime.datetime.now().date()
                self.update_date_display()
            elif attr_name == 'despacho':
                self.despacho_entry = tk.Entry(
                    campo_frame, 
                    width=50, 
                    font=("Arial", 11)
                )
                self.despacho_entry.pack(side=tk.LEFT)
            elif attr_name == 'abonado':
                self.abonado_entry = tk.Entry(
                    campo_frame, 
                    width=50, 
                    font=("Arial", 11)
                )
                self.abonado_entry.pack(side=tk.LEFT)
            elif attr_name == 'importe':
                self.importe_entry = tk.Entry(
                    campo_frame, 
                    width=50, 
                    validate="key", 
                    font=("Arial", 11)
                )
                self.importe_entry.config(validatecommand=(self.importe_entry.register(self.validate_decimal), '%P'))
                self.importe_entry.pack(side=tk.LEFT)
        
        # Frame para botón de guardado centrado
        boton_guardar_frame = tk.Frame(self.left_frame)
        boton_guardar_frame.pack(pady=10)
        
        # Botón de guardado centrado
        boton_guardar = tk.Button(
            boton_guardar_frame, 
            text="Guardar Despacho", 
            command=self.save_despacho, 
            bg="blue", 
            fg="white", 
            font=("Arial", 10, "bold"),
            width=20
        )
        boton_guardar.pack()
        
        # Frame para botones con alineación vertical
        self.buttons_frame = tk.Frame(self.right_frame)
        self.buttons_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=10)
        
        # Configuración de botones
        botones = [
            ("Guardar Todos los Datos", self.guardar_todos_datos, "purple"),
            ("Exportar Base de Datos", self.exportar_base_datos, "red"),
            ("Importar Archivos", self.importar_archivos, "brown"),
            ("Gestionar Pagos", self.abrir_gestor_pagos, "navy")
        ]
        
        # Distribuir botones verticalmente
        for texto, comando, color in botones:
            boton = tk.Button(
                self.buttons_frame, 
                text=texto, 
                command=comando, 
                bg=color, 
                fg="white", 
                font=("Arial", 10, "bold"),  
                width=35  
            )
            boton.pack(fill=tk.X, pady=7)  

        self.crear_menu()

    def get_system_info(self):
        """Obtener información básica del sistema"""
        return f"Sistema: {platform.system()}\nVersión: {platform.version()}\nComputadora: {platform.node()}"

    def get_formatted_date(self):
        """Obtener fecha actual en formato día, mes, año"""
        now = datetime.datetime.now()
        return now.strftime("%d %B %Y")

    def save_despacho(self):
        """Guardar información del despacho"""
        fecha = self.selected_date.strftime('%d/%m/%Y')  # Formatear fecha
        despacho = self.despacho_entry.get().strip()
        abonado = self.abonado_entry.get().strip()
        
        # Validar campos no vacíos
        if not despacho or not abonado:
            messagebox.showerror("Error", "Despacho y Abonado no pueden estar vacíos.")
            return
        
        try:
            importe = float(self.importe_entry.get())
        except ValueError:
            messagebox.showerror("Error", "El importe debe ser un número válido.")
            return
        
        try:
            # Crear directorio de datos si no existe
            datos_dir = os.path.join(os.path.expanduser("~"), "Servicios_Abonados")
            os.makedirs(datos_dir, exist_ok=True)
            
            # Nombre de archivo maestro
            filename = os.path.join(datos_dir, "servicios_abonados.csv")
            
            # Verificar si el archivo existe
            archivo_existe = os.path.exists(filename)
            
            # Escribir en el archivo CSV
            with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Escribir encabezados solo si el archivo no existe
                if not archivo_existe:
                    writer.writerow(['Fecha', 'Despacho', 'Abonado', 'Importe', 'Pagado'])
                
                # Escribir datos con estado de pago por defecto
                writer.writerow([fecha, despacho, abonado, f"{importe:.2f}", False])
            
            # Mensaje de éxito
            messagebox.showinfo("Guardado Exitoso", f"Despacho guardado en:\n{filename}")
            
            # Limpiar campos después de guardar
            self.despacho_entry.delete(0, tk.END)
            self.abonado_entry.delete(0, tk.END)
            self.importe_entry.delete(0, tk.END)
        
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el despacho: {str(e)}")
        
        # Marcar que hay cambios guardados
        self.marcar_cambios_pendientes()

    def save_abonado(self):
        """Guardar la información del abonado"""
        abonado_nombre = self.abonado_entry.get()
        if abonado_nombre:
            messagebox.showinfo("Abonado", f"Abonado guardado: {abonado_nombre}")
        else:
            messagebox.showwarning("Abonado", "Por favor, ingrese el nombre del abonado.")

    def validate_decimal(self, value):
        """Validar entrada decimal para importe"""
        if value == "":
            return True
        try:
            float(value)
            return True
        except ValueError:
            return False

    def save_importe(self):
        """Guardar el importe"""
        importe_str = self.importe_entry.get()
        try:
            importe = float(importe_str)
            messagebox.showinfo("Importe", f"Importe guardado: {importe:.2f} €")
        except ValueError:
            messagebox.showwarning("Importe", "Por favor, ingrese un número válido.")

    def guardar_todos_datos(self):
        """Guardar todos los datos en un archivo CSV"""
        # Validar que todos los campos estén llenos
        fecha = self.selected_date
        despacho = self.despacho_entry.get()
        abonado = self.abonado_entry.get()

        try:
            importe = float(self.importe_entry.get())
        except ValueError:
            messagebox.showwarning("Error", "Por favor, ingrese un importe válido.")
            return

        # Validar campos obligatorios
        if not (fecha and despacho and abonado):
            messagebox.showwarning("Error", "Por favor, complete todos los campos.")
            return

        # Elegir ubicación para guardar el archivo
        try:
            # Crear directorio de datos si no existe
            datos_dir = os.path.join(os.path.expanduser("~"), "Servicios_Abonados")
            os.makedirs(datos_dir, exist_ok=True)
            
            # Nombre de archivo basado en la fecha
            filename = os.path.join(datos_dir, f"servicios_abonados_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
            
            # Escribir en el archivo CSV
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                # Escribir encabezados
                writer.writerow(['Fecha', 'Despacho', 'Abonado', 'Importe'])
                # Escribir datos
                writer.writerow([fecha, despacho, abonado, f"{importe:.2f}"])
            
            # Mensaje de éxito
            messagebox.showinfo("Guardado Exitoso", f"Datos guardados en:\n{filename}")
            
            # Limpiar campos después de guardar
            self.despacho_entry.delete(0, tk.END)
            self.abonado_entry.delete(0, tk.END)
            self.importe_entry.delete(0, tk.END)

        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron guardar los datos: {str(e)}")
        
        # Resetear la bandera de cambios sin guardar
        self.cambios_sin_guardar = False
        
        # Mostrar mensaje de éxito
        messagebox.showinfo("Guardado", "Todos los datos han sido guardados correctamente.")

    def obtener_archivos_csv(self):
        """Obtener todos los archivos CSV en el directorio de datos"""
        datos_dir = os.path.join(os.path.expanduser("~"), "Servicios_Abonados")

        # Si el directorio no existe, retornar lista vacía
        if not os.path.exists(datos_dir):
            return []

        # Filtrar solo archivos CSV
        archivos_csv = [
            os.path.join(datos_dir, f)
            for f in os.listdir(datos_dir)
            if f.startswith("servicios_abonados_") and f.endswith(".csv")
        ]

        return archivos_csv

    def exportar_base_datos(self, formato=None):
        """Exportar base de datos a PDF o Excel"""
        # Obtener todos los archivos CSV
        archivos_csv = self.obtener_archivos_csv()

        if not archivos_csv:
            messagebox.showwarning("Exportar", "No hay datos para exportar.")
            return

        # Combinar todos los archivos CSV
        dataframes = [pd.read_csv(archivo, encoding='utf-8') for archivo in archivos_csv]
        df_combinado = pd.concat(dataframes, ignore_index=True)

        # Si no se especifica formato, mostrar diálogo de selección
        if not formato:
            formato = messagebox.askquestion("Exportar", "¿Desea exportar a PDF? (Cancelar para Excel)")
            formato = "pdf" if formato == "yes" else "xlsx"

        try:
            # Elegir ubicación para guardar
            if formato == "pdf":
                filename = filedialog.asksaveasfilename(
                    defaultextension=".pdf",
                    filetypes=[("PDF files", "*.pdf")]
                )
                if filename:
                    # Exportar a PDF
                    doc = SimpleDocTemplate(filename, pagesize=letter)
                    elementos = []

                    # Convertir DataFrame a lista para ReportLab
                    datos = [list(df_combinado.columns)] + df_combinado.values.tolist()

                    # Crear tabla
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
            else:
                filename = filedialog.asksaveasfilename(
                    defaultextension=".xlsx",
                    filetypes=[("Excel files", "*.xlsx")]
                )
                if filename:
                    # Exportar a Excel
                    df_combinado.to_excel(filename, index=False, engine='openpyxl')

            if filename:
                messagebox.showinfo("Exportar", f"Datos exportados exitosamente a {filename}")

        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron exportar los datos: {str(e)}")

    def importar_archivos(self):
        """Importar archivos Excel o PDF"""
        # Tipos de archivos permitidos
        filetypes = [
            ("Archivos Excel", "*.xlsx *.xls"),
            ("Archivos PDF", "*.pdf"),
            ("Archivos CSV", "*.csv"),
            ("Todos los archivos", "*.*")
        ]
        
        # Abrir diálogo de selección de archivos
        archivos = filedialog.askopenfilenames(
            title="Seleccionar archivos para importar",
            filetypes=filetypes
        )

        if not archivos:
            return

        # Contador de importaciones
        importaciones_exitosas = 0
        errores = []
        archivos_importados = []  # Lista para guardar rutas de archivos importados

        # Directorio para guardar
        datos_dir = os.path.join(os.path.expanduser("~"), "Servicios_Abonados")
        os.makedirs(datos_dir, exist_ok=True)

        for archivo in archivos:
            try:
                # Determinar tipo de archivo
                extension = os.path.splitext(archivo)[1].lower()

                # Leer archivo según su tipo
                if extension in ['.xlsx', '.xls', '.csv']:
                    # Importar Excel o CSV con opciones más flexibles
                    try:
                        if extension == '.csv':
                            # Leer CSV
                            df = pd.read_csv(
                                archivo, 
                                encoding='utf-8',
                                dtype=str,  # Leer todas las columnas como cadenas
                                engine='python'  # Motor más flexible
                            )
                        else:
                            # Leer Excel
                            df = pd.read_excel(
                                archivo, 
                                engine='openpyxl' if extension == '.xlsx' else 'xlrd',
                                dtype=str  # Leer todas las columnas como cadenas
                            )
                    except Exception as e:
                        # Intentar leer con diferentes parámetros
                        df = pd.read_csv(
                            archivo, 
                            encoding='latin-1',  # Probar otra codificación
                            dtype=str,
                            engine='python'
                        )
                
                elif extension == '.pdf':
                    # Importar PDF como texto plano
                    try:
                        # Leer contenido del PDF como texto
                        with open(archivo, 'rb') as file:
                            texto_completo = file.read().decode('utf-8', errors='ignore')
                        
                        # Intentar encontrar líneas que parezcan datos
                        import re
                        lineas_datos = []
                        # Patrón para buscar líneas con fecha, texto y número
                        patron = r'(\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4})\s*(.+?)\s*(\d+[.,]?\d*)'
                        
                        for linea in texto_completo.split('\n'):
                            match = re.search(patron, linea)
                            if match:
                                lineas_datos.append(match.groups())
                        
                        # Convertir a DataFrame
                        df = pd.DataFrame(
                            lineas_datos, 
                            columns=['Fecha', 'Despacho', 'Importe']
                        )
                        
                        if df.empty:
                            raise ValueError("No se pudieron extraer datos del PDF")
                    
                    except Exception as e:
                        # Método de extracción de texto alternativo
                        texto_completo = ""
                        with open(archivo, 'rb') as file:
                            texto_completo = file.read().decode('utf-8', errors='ignore')
                        
                        # Intentar convertir texto a DataFrame
                        import io
                        texto_io = io.StringIO(texto_completo)
                        df = pd.read_csv(
                            texto_io, 
                            sep='\s+',  # Separar por espacios
                            header=None, 
                            names=['Fecha', 'Despacho', 'Abonado', 'Importe']
                        )
                
                else:
                    raise ValueError(f"Tipo de archivo no soportado: {extension}")

                # Normalizar columnas
                columnas_esperadas = ['Fecha', 'Despacho', 'Abonado', 'Importe']
                
                # Renombrar columnas si no coinciden
                df.columns = [col.strip().title() for col in df.columns]
                
                # Verificar y ajustar columnas
                for col_esperada in columnas_esperadas:
                    if col_esperada not in df.columns:
                        # Buscar columna similar o agregar columna vacía
                        similar = [col for col in df.columns if col_esperada.lower() in col.lower()]
                        if similar:
                            df = df.rename(columns={similar[0]: col_esperada})
                        else:
                            df[col_esperada] = ''

                # Seleccionar solo las columnas necesarias
                df = df[columnas_esperadas]

                # Convertir tipos de datos
                df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce').dt.strftime('%d/%m/%Y')
                df['Importe'] = pd.to_numeric(
                    df['Importe'].str.replace(',', '.').str.replace('€', '').str.replace(' ', ''), 
                    errors='coerce'
                ).fillna(0)

                # Eliminar filas completamente vacías
                df = df.dropna(how='all')

                # Añadir columna de estado de pago
                df['Pagado'] = False

                # Guardar como CSV
                nombre_archivo = f"servicios_abonados_importado_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.csv"
                ruta_archivo = os.path.join(datos_dir, nombre_archivo)
                df.to_csv(ruta_archivo, index=False, encoding='utf-8')

                importaciones_exitosas += 1
                archivos_importados.append(ruta_archivo)

            except Exception as e:
                # Registrar error detallado
                error_msg = f"Error importando {archivo}: {str(e)}"
                errores.append(error_msg)
                logging.error(error_msg)  # Registrar en logs

        # Mostrar resumen de importación
        if importaciones_exitosas > 0:
            # Abrir tabla de registros con los archivos importados
            self.abrir_tabla_registros(archivos_importados)
            
            mensaje_exito = f"Se importaron {importaciones_exitosas} archivo(s) exitosamente."
            if errores:
                mensaje_exito += "\n\nDetalles de errores:"
                for error in errores:
                    mensaje_exito += f"\n- {error}"
            messagebox.showinfo("Importar Archivos", mensaje_exito)
        else:
            mensaje_error = "No se pudo importar ningún archivo."
            if errores:
                mensaje_error += "\n\nDetalles de errores:"
                for error in errores:
                    mensaje_error += f"\n- {error}"
            messagebox.showerror("Error de Importación", mensaje_error)

    def abrir_tabla_registros(self, archivos_especificos=None):
        """Abrir ventana con tabla de registros y opción de marcar como pagados"""
        # Crear ventana de registros
        tabla_window = tk.Toplevel(self.master)
        tabla_window.title("Registros de Servicios")
        tabla_window.geometry("1000x600")

        # Cargar datos de CSV
        try:
            # Buscar directorio de datos
            datos_dir = os.path.join(os.path.expanduser("~"), "Servicios_Abonados")
            
            # Ruta del archivo CSV principal
            filename = os.path.join(datos_dir, "servicios_abonados.csv")
            
            # Verificar si el archivo existe
            if not os.path.exists(filename):
                messagebox.showinfo("Información", "No hay registros para mostrar.")
                tabla_window.destroy()
                return

            # Leer archivo CSV
            df = pd.read_csv(filename)
            
            # Convertir columna de fecha a datetime para ordenación
            df['Fecha'] = pd.to_datetime(df['Fecha'], format='%d/%m/%Y', errors='coerce')
            
            # Añadir columna de estado de pago si no existe
            if 'Pagado' not in df.columns:
                df['Pagado'] = False
            
            # Añadir columna de selección
            df['Seleccionar'] = False

        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar los registros: {str(e)}")
            tabla_window.destroy()
            return

        # Frame para la tabla
        frame_tabla = tk.Frame(tabla_window)
        frame_tabla.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Scrollbars
        scrollbar_y = tk.Scrollbar(frame_tabla)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        scrollbar_x = tk.Scrollbar(frame_tabla, orient=tk.HORIZONTAL)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)

        # Crear tabla usando Treeview
        tabla = ttk.Treeview(
            frame_tabla, 
            columns=list(df.columns), 
            show='headings',
            yscrollcommand=scrollbar_y.set,
            xscrollcommand=scrollbar_x.set,
            selectmode='extended'  # Permitir selección múltiple
        )

        # Configurar scrollbars
        scrollbar_y.config(command=tabla.yview)
        scrollbar_x.config(command=tabla.xview)

        # Configurar columnas con capacidad de ordenación
        column_widths = {
            'Fecha': 100,
            'Despacho': 80,
            'Abonado': 100,
            'Importe': 80,
            'Pagado': 80,
            'Seleccionar': 50
        }
        
        for col in df.columns:
            tabla.heading(col, text=col)
            tabla.column(col, width=column_widths.get(col, 100), anchor='center')

        # Personalizar columna de Pagado y Seleccionar
        tabla.column('Pagado', width=50, anchor='center')
        tabla.column('Seleccionar', width=50, anchor='center')

        # Insertar datos
        for index, row in df.sort_values('Fecha').iterrows():
            valores = list(row)
            valores[df.columns.get_loc('Fecha')] = valores[df.columns.get_loc('Fecha')].strftime('%d/%m/%Y')
            valores[df.columns.get_loc('Pagado')] = '✓' if row['Pagado'] else '✗'
            valores[df.columns.get_loc('Seleccionar')] = '☐'
            tabla.insert('', 'end', values=valores, tags=(index,))

        # Permitir edición de estado de pago
        def toggle_pago(event):
            # Obtener la fila seleccionada
            item_seleccionado = tabla.selection()[0]
            index = tabla.item(item_seleccionado, 'tags')[0]
            
            # Cambiar estado de pago
            df.loc[int(index), 'Pagado'] = not df.loc[int(index), 'Pagado']
            
            # Actualizar visualización
            valores = list(df.loc[int(index)])
            valores[df.columns.get_loc('Fecha')] = valores[df.columns.get_loc('Fecha')].strftime('%d/%m/%Y')
            valores[df.columns.get_loc('Pagado')] = '✓' if df.loc[int(index), 'Pagado'] else '✗'
            valores[df.columns.get_loc('Seleccionar')] = '☐'
            tabla.item(item_seleccionado, values=valores)

        # Permitir edición de estado de selección
        def toggle_seleccion(event):
            # Obtener la fila seleccionada
            item_seleccionado = tabla.selection()[0]
            index = tabla.item(item_seleccionado, 'tags')[0]
            
            # Cambiar estado de selección
            df.loc[int(index), 'Seleccionar'] = not df.loc[int(index), 'Seleccionar']
            
            # Actualizar visualización
            valores = list(df.loc[int(index)])
            valores[df.columns.get_loc('Fecha')] = valores[df.columns.get_loc('Fecha')].strftime('%d/%m/%Y')
            valores[df.columns.get_loc('Pagado')] = '✓' if df.loc[int(index), 'Pagado'] else '✗'
            valores[df.columns.get_loc('Seleccionar')] = '☑' if df.loc[int(index), 'Seleccionar'] else '☐'
            tabla.item(item_seleccionado, values=valores)

        # Bind doble clic para cambiar estado de pago y selección
        tabla.bind('<Double-1>', lambda event: toggle_seleccion(event))
        tabla.bind('<Control-Double-1>', lambda event: toggle_pago(event))

        # Función para ordenar columnas
        def ordenar_columna(tv, col, reverso):
            # Obtener los datos de la columna
            l = [(tv.set(k, col), k) for k in tv.get_children('')]
            
            # Intentar convertir a número o fecha si es posible
            try:
                l = [(float(x[0].replace(',', '.')), x[1]) for x in l]
            except (ValueError, TypeError):
                try:
                    l = [(pd.to_datetime(x[0], format='%d/%m/%Y'), x[1]) for x in l]
                except (ValueError, TypeError):
                    pass
            
            # Ordenar
            l.sort(reverse=reverso)
            
            # Reordenar elementos en la tabla
            for index, (val, k) in enumerate(l):
                tv.move(k, '', index)
            
            # Cambiar la dirección de ordenación para la próxima vez
            tv.heading(col, command=lambda: ordenar_columna(tv, col, not reverso))

        # Botones de acción
        frame_botones = tk.Frame(tabla_window)
        frame_botones.pack(fill=tk.X, padx=10, pady=5)

        def guardar_cambios():
            try:
                # Guardar cambios en el archivo CSV principal
                df.to_csv(filename, index=False)
                
                messagebox.showinfo("Éxito", "Cambios guardados correctamente.")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudieron guardar los cambios: {str(e)}")

        def exportar_pagados():
            try:
                # Filtrar solo pagados
                df_pagados = df[df['Pagado'] == True]
                
                # Nombre de archivo para exportación
                nombre_archivo = f"servicios_pagados_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                ruta_archivo = filedialog.asksaveasfilename(
                    defaultextension=".csv",
                    filetypes=[("Archivos CSV", "*.csv")],
                    initialfile=nombre_archivo
                )
                
                if ruta_archivo:
                    df_pagados.to_csv(ruta_archivo, index=False)
                    messagebox.showinfo("Éxito", f"Servicios pagados exportados a {ruta_archivo}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudieron exportar los servicios pagados: {str(e)}")

        def borrar_seleccion():
            # Preguntar si está seguro
            respuesta = messagebox.askyesno("Confirmar", "¿Está seguro de que desea borrar los registros seleccionados?")
            
            if respuesta:
                # Filtrar filas no seleccionadas
                df_filtrado = df[df['Seleccionar'] == False]
                
                # Guardar en archivo CSV
                df_filtrado.to_csv(filename, index=False)
                
                # Actualizar tabla
                for item in tabla.get_children():
                    if tabla.item(item)['values'][df.columns.get_loc('Seleccionar')] == '☑':
                        tabla.delete(item)
                
                messagebox.showinfo("Éxito", "Registros seleccionados borrados correctamente.")

        # Botón de guardar cambios
        btn_guardar = tk.Button(
            frame_botones, 
            text="Guardar Cambios", 
            command=guardar_cambios
        )
        btn_guardar.pack(side=tk.LEFT, padx=5)

        # Botón de exportar pagados
        btn_exportar = tk.Button(
            frame_botones, 
            text="Exportar Pagados", 
            command=exportar_pagados
        )
        btn_exportar.pack(side=tk.LEFT, padx=5)

        # Botón de borrar selección
        btn_borrar_seleccion = tk.Button(
            frame_botones, 
            text="Borrar Seleccionados", 
            command=borrar_seleccion
        )
        btn_borrar_seleccion.pack(side=tk.LEFT, padx=5)

        # Instrucciones de uso
        lbl_instrucciones = tk.Label(
            frame_botones, 
            text="Doble clic: Marcar/Desmarcar | Ctrl+Doble clic: Marcar como Pagado", 
            font=("Arial", 8)
        )
        lbl_instrucciones.pack(side=tk.LEFT, padx=10)

        # Mostrar tabla
        tabla.pack(fill=tk.BOTH, expand=True)

    def abrir_gestor_pagos(self):
        """Abrir ventana de gestión de pagos"""
        # Crear ventana de gestión de pagos
        gestor_window = tk.Toplevel(self.master)
        gestor_window.title("Gestión de Pagos")
        gestor_window.geometry("1000x600")

        # Cargar datos de CSV
        try:
            # Buscar directorio de datos
            datos_dir = os.path.join(os.path.expanduser("~"), "Servicios_Abonados")
            logging.debug(f"Directorio de datos: {datos_dir}")  # Debug logging
            
            # Ruta del archivo CSV principal
            filename = os.path.join(datos_dir, "servicios_abonados.csv")
            logging.debug(f"Ruta del archivo CSV: {filename}")  # Debug logging
            
            # Verificar si el directorio existe
            if not os.path.exists(datos_dir):
                logging.error(f"ERROR: El directorio {datos_dir} no existe.")  # Debug logging
                messagebox.showerror("Error", f"El directorio {datos_dir} no existe.")
                gestor_window.destroy()
                return
            
            # Verificar si el archivo existe
            if not os.path.exists(filename):
                logging.error(f"ERROR: No se encontró el archivo {filename}")  # Debug logging
                messagebox.showinfo("Información", f"No se encontró el archivo {filename}.")
                gestor_window.destroy()
                return

            # Leer archivo CSV con manejo de errores
            try:
                df = pd.read_csv(filename, encoding='utf-8')
                logging.debug(f"Columnas del DataFrame: {list(df.columns)}")  # Debug logging
                logging.debug(f"Número de filas: {len(df)}")  # Debug logging
            except pd.errors.EmptyDataError:
                logging.error("ERROR: El archivo CSV está vacío.")  # Debug logging
                messagebox.showerror("Error", "El archivo CSV está vacío.")
                gestor_window.destroy()
                return
            except pd.errors.ParserError as e:
                logging.error(f"ERROR al parsear el archivo CSV: {str(e)}")  # Debug logging
                messagebox.showerror("Error", f"Error al parsear el archivo CSV: {str(e)}")
                gestor_window.destroy()
                return
            
            # Verificar columnas requeridas
            required_columns = ['Fecha', 'Despacho', 'Abonado', 'Importe', 'Pagado']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                logging.error(f"ERROR: Columnas faltantes: {', '.join(missing_columns)}")  # Debug logging
                messagebox.showerror("Error", f"Columnas faltantes: {', '.join(missing_columns)}")
                gestor_window.destroy()
                return
            
            # Filtrar solo servicios pagados
            df_pagados = df.copy()  # Mostrar todos los registros
            logging.debug(f"Número de servicios: {len(df_pagados)}")  # Debug logging

            # Añadir columna de selección
            df_pagados['Seleccionar'] = False

        except Exception as e:
            logging.error(f"ERROR inesperado al cargar registros: {str(e)}")  # Debug logging
            messagebox.showerror("Error", f"Error inesperado al cargar registros: {str(e)}")
            gestor_window.destroy()
            return

        # Frame para la tabla
        frame_tabla = tk.Frame(gestor_window)
        frame_tabla.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Scrollbars
        scrollbar_y = tk.Scrollbar(frame_tabla)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        scrollbar_x = tk.Scrollbar(frame_tabla, orient=tk.HORIZONTAL)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)

        # Crear tabla usando Treeview
        tabla = ttk.Treeview(
            frame_tabla, 
            columns=list(df_pagados.columns), 
            show='headings',
            yscrollcommand=scrollbar_y.set,
            xscrollcommand=scrollbar_x.set,
            selectmode='extended'  # Permitir selección múltiple
        )

        # Configurar scrollbars
        scrollbar_y.config(command=tabla.yview)
        scrollbar_x.config(command=tabla.xview)

        # Configurar columnas
        column_widths = {
            'Fecha': 100,
            'Despacho': 80,
            'Abonado': 100,
            'Importe': 80,
            'Pagado': 80,
            'Seleccionar': 50
        }
        
        for col in df_pagados.columns:
            tabla.heading(col, text=col)
            tabla.column(col, width=column_widths.get(col, 100), anchor='center')

        # Personalizar columna de Seleccionar
        tabla.column('Seleccionar', width=50, anchor='center')

        # Insertar datos con color según estado de pago
        for index, row in df_pagados.iterrows():
            valores = list(row)
            valores[df_pagados.columns.get_loc('Seleccionar')] = '☐'
            item = tabla.insert('', 'end', values=valores, tags=(index,))
            
            # Color coding for payment status
            if not row['Pagado']:
                tabla.tag_configure(index, background='#FFCCCC')  # Light red for unpaid
            else:
                tabla.tag_configure(index, background='#CCFFCC')  # Light green for paid

        # Permitir edición de estado de selección
        def toggle_seleccion(event):
            # Obtener la fila seleccionada
            item_seleccionado = tabla.selection()[0]
            index = tabla.item(item_seleccionado, 'tags')[0]
            
            # Cambiar estado de selección
            df_pagados.loc[int(index), 'Seleccionar'] = not df_pagados.loc[int(index), 'Seleccionar']
            
            # Actualizar visualización
            valores = list(df_pagados.loc[int(index)])
            valores[df_pagados.columns.get_loc('Seleccionar')] = '☑' if df_pagados.loc[int(index), 'Seleccionar'] else '☐'
            tabla.item(item_seleccionado, values=valores)

        # Bind doble clic para cambiar estado de selección
        tabla.bind('<Double-1>', toggle_seleccion)

        # Botones de acción
        frame_botones = tk.Frame(gestor_window)
        frame_botones.pack(fill=tk.X, padx=10, pady=5)

        def marcar_no_pagado():
            # Obtener filas seleccionadas
            seleccionados = tabla.selection()
            
            if not seleccionados:
                messagebox.showwarning("Advertencia", "Seleccione al menos un registro.")
                return
            
            # Preguntar si está seguro
            respuesta = messagebox.askyesno("Confirmar", "¿Está seguro de que desea marcar los registros seleccionados como no pagados?")
            
            if respuesta:
                # Cambiar estado de pago en el DataFrame original
                for item in seleccionados:
                    index = tabla.item(item, 'tags')[0]
                    df.loc[int(index), 'Pagado'] = False
                    tabla.delete(item)
                
                # Guardar cambios en archivo CSV
                df.to_csv(filename, index=False)
                
                messagebox.showinfo("Éxito", "Registros marcados como no pagados correctamente.")

        # Botón de marcar como no pagado
        btn_no_pagado = tk.Button(
            frame_botones, 
            text="Marcar como No Pagado", 
            command=marcar_no_pagado
        )
        btn_no_pagado.pack(side=tk.LEFT, padx=5)

        # Instrucciones de uso
        lbl_instrucciones = tk.Label(
            frame_botones, 
            text="Doble clic: Marcar/Desmarcar", 
            font=("Arial", 8)
        )
        lbl_instrucciones.pack(side=tk.LEFT, padx=10)

        # Mostrar tabla
        tabla.pack(fill=tk.BOTH, expand=True)

    def open_calendar(self):
        """Abrir calendario para seleccionar fecha"""
        # Crear ventana de calendario
        calendar_window = tk.Toplevel(self.master)
        calendar_window.title("Calendario")

        # Crear calendario
        calendar = Calendar(calendar_window, selectmode='day', year=datetime.datetime.now().year, month=datetime.datetime.now().month, day=datetime.datetime.now().day)
        calendar.pack(fill='both', expand=True)

        # Botón para seleccionar fecha
        def select_date():
            fecha_seleccionada = calendar.selection_get()
            self.selected_date = fecha_seleccionada
            self.update_date_display()
            calendar_window.destroy()

        btn_select = tk.Button(calendar_window, text="Seleccionar Fecha", command=select_date)
        btn_select.pack(pady=10)

    def update_date_display(self):
        """Actualizar la fecha en el campo de entrada"""
        self.date_entry.config(state='normal')
        self.date_entry.delete(0, tk.END)
        self.date_entry.insert(0, self.selected_date.strftime("%d/%m/%Y"))
        self.date_entry.config(state='readonly')

    def crear_menu(self):
        """Crear menú de la aplicación"""
        # Barra de menú principal
        self.barra_menu = tk.Menu(self.master)
        self.master.config(menu=self.barra_menu)

        # Menú de Archivo
        self.menu_archivo = tk.Menu(self.barra_menu, tearoff=0)
        self.barra_menu.add_cascade(label="Archivo", menu=self.menu_archivo)
        self.menu_archivo.add_command(
            label="Importar Archivos", 
            command=self.importar_archivos
        )
        self.menu_archivo.add_separator()
        self.menu_archivo.add_command(
            label="Salir", 
            command=self.master.quit
        )

        # Menú de Registros
        self.menu_registros = tk.Menu(self.barra_menu, tearoff=0)
        self.barra_menu.add_cascade(label="Registros", menu=self.menu_registros)
        self.menu_registros.add_command(
            label="Ver Tabla de Registros", 
            command=self.abrir_tabla_registros
        )

        # Menú de Gestión
        self.menu_gestion = tk.Menu(self.barra_menu, tearoff=0)
        self.barra_menu.add_cascade(label="Gestión", menu=self.menu_gestion)
        self.menu_gestion.add_command(
            label="Gestor de Pagos", 
            command=self.abrir_gestor_pagos
        )
        self.menu_gestion.add_command(
            label="Exportar Datos", 
            command=self.exportar_base_datos
        )

    def marcar_cambios_pendientes(self):
        """Método para marcar que hay cambios sin guardar"""
        self.cambios_sin_guardar = True

    def on_closing(self):
        """Método para manejar el cierre de la aplicación"""
        if not self.cambios_sin_guardar:
            # Si no hay cambios sin guardar, cerrar directamente
            self.master.destroy()
            return

        # Si hay cambios sin guardar, mostrar diálogo de confirmación
        respuesta = messagebox.askyesnocancel(
            "Guardar Cambios", 
            "Hay cambios sin guardar. ¿Desea guardarlos antes de salir?",
            icon='warning'
        )
        
        if respuesta is None:  # Cancelar
            return
        elif respuesta:  # Sí, guardar
            try:
                self.guardar_todos_datos()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudieron guardar los datos: {str(e)}")
                return
        
        # Cerrar la aplicación
        self.master.destroy()

def main():
    root = tk.Tk()
    app = WindowsApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
