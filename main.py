import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import sqlite3
import datetime
import pandas as pd
import os
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER

class DatePickerDialog(simpledialog.Dialog):
    def body(self, master):
        self.result = None
        
        tk.Label(master, text="Año:").grid(row=0, column=0)
        self.year_var = tk.StringVar(value=str(datetime.date.today().year))
        self.year_entry = tk.Entry(master, textvariable=self.year_var, width=10)
        self.year_entry.grid(row=0, column=1)
        
        tk.Label(master, text="Mes (1-12):").grid(row=1, column=0)
        self.month_var = tk.StringVar(value=str(datetime.date.today().month))
        self.month_entry = tk.Entry(master, textvariable=self.month_var, width=10)
        self.month_entry.grid(row=1, column=1)
        
        tk.Label(master, text="Día (1-31):").grid(row=2, column=0)
        self.day_var = tk.StringVar(value=str(datetime.date.today().day))
        self.day_entry = tk.Entry(master, textvariable=self.day_var, width=10)
        self.day_entry.grid(row=2, column=1)
        
        return self.year_entry

    def apply(self):
        try:
            year = int(self.year_var.get())
            month = int(self.month_var.get())
            day = int(self.day_var.get())
            
            self.result = datetime.date(year, month, day).strftime('%Y-%m-%d')
        except ValueError:
            messagebox.showerror("Error", "Fecha inválida. Use formato AAAA-MM-DD")
            self.result = None

class DateEntry(tk.Entry):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.bind('<Button-1>', self.show_date_picker)
        self.insert(0, datetime.date.today().strftime('%Y-%m-%d'))
        
    def show_date_picker(self, event):
        d = DatePickerDialog(self.master, title="Seleccionar Fecha")
        if d.result:
            self.delete(0, tk.END)
            self.insert(0, d.result)

class ServiciosAbonados:
    def __init__(self, db_name='servicios_abonados.db'):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.crear_tabla()
        self.actualizar_tabla()

    def crear_tabla(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS registros (
                id INTEGER PRIMARY KEY,
                fecha TEXT,
                numero_despacho TEXT,
                importe REAL,
                nombre_compania TEXT,
                estado TEXT DEFAULT 'Pendiente'
            )
        ''')
        self.conn.commit()

    def actualizar_tabla(self):
        try:
            # Intentar agregar columna estado si no existe
            self.cursor.execute("ALTER TABLE registros ADD COLUMN estado TEXT DEFAULT 'Pendiente'")
            self.conn.commit()
        except sqlite3.OperationalError:
            # La columna ya existe
            pass

    def insertar_registro(self, fecha, numero_despacho, importe, nombre_compania, estado='Pendiente'):
        try:
            self.cursor.execute('''
                INSERT INTO registros (fecha, numero_despacho, importe, nombre_compania, estado)
                VALUES (?, ?, ?, ?, ?)
            ''', (fecha, numero_despacho, importe, nombre_compania, estado))
            self.conn.commit()
        except sqlite3.OperationalError:
            # Si hay un error, intentar insertar sin la columna estado
            self.cursor.execute('''
                INSERT INTO registros (fecha, numero_despacho, importe, nombre_compania)
                VALUES (?, ?, ?, ?)
            ''', (fecha, numero_despacho, importe, nombre_compania))
            self.conn.commit()

    def obtener_registros(self, fecha=None):
        try:
            if fecha:
                self.cursor.execute('SELECT * FROM registros WHERE fecha = ?', (fecha,))
            else:
                self.cursor.execute('SELECT * FROM registros')
            return self.cursor.fetchall()
        except sqlite3.OperationalError:
            # Si hay un error, obtener registros sin la columna estado
            if fecha:
                self.cursor.execute('SELECT id, fecha, numero_despacho, importe, nombre_compania FROM registros WHERE fecha = ?', (fecha,))
            else:
                self.cursor.execute('SELECT id, fecha, numero_despacho, importe, nombre_compania FROM registros')
            return self.cursor.fetchall()

    def cambiar_estado_registro(self, id_registro, nuevo_estado):
        try:
            self.cursor.execute('''
                UPDATE registros 
                SET estado = ? 
                WHERE id = ?
            ''', (nuevo_estado, id_registro))
            self.conn.commit()
        except sqlite3.OperationalError:
            # Si no existe la columna estado, no hacer nada
            pass

    def obtener_resumen_diario(self, fecha=None):
        if not fecha:
            fecha = datetime.datetime.now().strftime('%Y-%m-%d')
        
        try:
            self.cursor.execute('''
                SELECT 
                    SUM(importe) as total_importe, 
                    COUNT(*) as total_registros,
                    SUM(CASE WHEN estado = 'Pagado' THEN importe ELSE 0 END) as total_pagado,
                    SUM(CASE WHEN estado = 'Pendiente' THEN importe ELSE 0 END) as total_pendiente
                FROM registros 
                WHERE fecha = ?
            ''', (fecha,))
            return self.cursor.fetchone()
        except sqlite3.OperationalError:
            # Si no existe la columna estado, devolver resumen sin estado
            self.cursor.execute('''
                SELECT 
                    SUM(importe) as total_importe, 
                    COUNT(*) as total_registros,
                    0 as total_pagado,
                    0 as total_pendiente
                FROM registros 
                WHERE fecha = ?
            ''', (fecha,))
            return self.cursor.fetchone()

    def obtener_resumen_mensual(self, fecha=None):
        if not fecha:
            fecha = datetime.datetime.now().strftime('%Y-%m')
        
        try:
            self.cursor.execute('''
                SELECT 
                    SUM(importe) as total_importe, 
                    COUNT(*) as total_registros,
                    SUM(CASE WHEN estado = 'Pagado' THEN importe ELSE 0 END) as total_pagado,
                    SUM(CASE WHEN estado = 'Pendiente' THEN importe ELSE 0 END) as total_pendiente
                FROM registros 
                WHERE strftime('%Y-%m', fecha) = ?
            ''', (fecha,))
            return self.cursor.fetchone()
        except sqlite3.OperationalError:
            # Si no existe la columna estado, devolver resumen sin estado
            self.cursor.execute('''
                SELECT 
                    SUM(importe) as total_importe, 
                    COUNT(*) as total_registros,
                    0 as total_pagado,
                    0 as total_pendiente
                FROM registros 
                WHERE strftime('%Y-%m', fecha) = ?
            ''', (fecha,))
            return self.cursor.fetchone()

    def borrar_registro(self, id_registro):
        self.cursor.execute('DELETE FROM registros WHERE id = ?', (id_registro,))
        self.conn.commit()

    def cerrar_conexion(self):
        self.conn.close()

class ServiciosAbonadosApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Servicios de Abonados")
        self.master.geometry("1200x800")
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.servicio = ServiciosAbonados()

        self.notebook = ttk.Notebook(master)
        self.notebook.pack(expand=True, fill='both')

        self.registro_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.registro_frame, text='Registro')

        campos = [
            ("Fecha:", "fecha"),
            ("Número de Despacho:", "numero_despacho"),
            ("Importe (€):", "importe"),
            ("Nombre de Compañía:", "nombre_compania")
        ]

        self.entradas = {}
        for i, (etiqueta, nombre) in enumerate(campos):
            ttk.Label(self.registro_frame, text=etiqueta).grid(row=i, column=0, padx=10, pady=5)
            
            if nombre == 'fecha':
                entrada = DateEntry(
                    self.registro_frame, 
                    width=50, 
                    background='white', 
                    foreground='black', 
                    borderwidth=2
                )
            else:
                entrada = ttk.Entry(self.registro_frame, width=50)
            
            entrada.grid(row=i, column=1, padx=10, pady=5)
            self.entradas[nombre] = entrada

        self.estado_var = tk.BooleanVar()
        self.estado_check = ttk.Checkbutton(self.registro_frame, text="Pagado", variable=self.estado_var)
        self.estado_check.grid(row=len(campos), column=0, columnspan=2, pady=10)

        ttk.Button(self.registro_frame, text="Registrar", command=self.registrar_servicio).grid(row=len(campos)+1, column=0, columnspan=2, pady=10)

        self.tabla = ttk.Treeview(self.registro_frame, columns=('ID', 'Fecha', 'Despacho', 'Importe', 'Compañía', 'Estado'), show='headings')
        for col in self.tabla['columns']:
            self.tabla.heading(col, text=col)
        self.tabla.grid(row=len(campos)+2, column=0, columnspan=2, padx=10, pady=10)

        ttk.Button(self.registro_frame, text="Borrar Seleccionado", command=self.borrar_registro_seleccionado).grid(row=len(campos)+3, column=0, columnspan=2, pady=10)

        ttk.Button(self.registro_frame, text="Cambiar Estado Seleccionado", command=self.cambiar_estado_registro_seleccionado).grid(row=len(campos)+4, column=0, columnspan=2, pady=10)

        self.resumenes_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.resumenes_frame, text='Resúmenes')

        ttk.Label(self.resumenes_frame, text="Resumen Diario").grid(row=0, column=0, columnspan=2, pady=10)
        
        ttk.Label(self.resumenes_frame, text="Fecha:").grid(row=1, column=0, padx=10, pady=5)
        self.fecha_resumen_diario = DateEntry(
            self.resumenes_frame, 
            width=50, 
            background='white', 
            foreground='black', 
            borderwidth=2
        )
        self.fecha_resumen_diario.grid(row=1, column=1, padx=10, pady=5)
        
        ttk.Button(self.resumenes_frame, text="Generar Resumen Diario", command=self.generar_resumen_diario).grid(row=2, column=0, columnspan=2, pady=10)

        ttk.Label(self.resumenes_frame, text="Resumen Mensual").grid(row=3, column=0, columnspan=2, pady=10)
        
        ttk.Label(self.resumenes_frame, text="Fecha:").grid(row=4, column=0, padx=10, pady=5)
        self.fecha_resumen_mensual = DateEntry(
            self.resumenes_frame, 
            width=50, 
            background='white', 
            foreground='black', 
            borderwidth=2
        )
        self.fecha_resumen_mensual.grid(row=4, column=1, padx=10, pady=5)
        
        ttk.Button(self.resumenes_frame, text="Generar Resumen Mensual", command=self.generar_resumen_mensual).grid(row=5, column=0, columnspan=2, pady=10)

        self.exportacion_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.exportacion_frame, text='Exportación')

        ttk.Button(self.exportacion_frame, text="Exportar a Excel", command=self.exportar_excel).grid(row=0, column=0, padx=10, pady=10)
        ttk.Button(self.exportacion_frame, text="Exportar a PDF", command=self.exportar_pdf).grid(row=0, column=1, padx=10, pady=10)

        self.actualizar_tabla()

    def registrar_servicio(self):
        try:
            fecha = self.entradas['fecha'].get()
            numero_despacho = self.entradas['numero_despacho'].get()
            importe = float(self.entradas['importe'].get())
            nombre_compania = self.entradas['nombre_compania'].get()
            
            # Intentar insertar con estado, pero manejar si no existe la columna
            try:
                estado = 'Pagado' if self.estado_var.get() else 'Pendiente'
                self.servicio.insertar_registro(fecha, numero_despacho, importe, nombre_compania, estado)
            except sqlite3.OperationalError:
                # Si no existe la columna estado, insertar sin ella
                self.servicio.insertar_registro(fecha, numero_despacho, importe, nombre_compania)
            
            for entrada in self.entradas.values():
                entrada.delete(0, tk.END)
            self.estado_var.set(False)
            
            self.actualizar_tabla()
            
            messagebox.showinfo("Éxito", "Registro añadido correctamente")
        except ValueError:
            messagebox.showerror("Error", "Por favor, introduzca un importe válido")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def actualizar_tabla(self):
        for i in self.tabla.get_children():
            self.tabla.delete(i)
        
        registros = self.servicio.obtener_registros()
        
        # Manejar registros con o sin columna estado
        for registro in registros:
            # Si el registro tiene 5 columnas (sin estado), agregar 'Pendiente' como estado por defecto
            if len(registro) == 5:
                registro = list(registro) + ['Pendiente']
            self.tabla.insert('', 'end', values=registro)

    def borrar_registro_seleccionado(self):
        seleccion = self.tabla.selection()
        
        if not seleccion:
            messagebox.showwarning("Advertencia", "Seleccione un registro para borrar")
            return
        
        registro = self.tabla.item(seleccion[0])['values']
        id_registro = registro[0]
        
        if messagebox.askyesno("Confirmar", "¿Está seguro de que desea borrar este registro?"):
            self.servicio.borrar_registro(id_registro)
            self.actualizar_tabla()

    def cambiar_estado_registro_seleccionado(self):
        seleccion = self.tabla.selection()
        
        if not seleccion:
            messagebox.showwarning("Advertencia", "Seleccione un registro para cambiar su estado")
            return
        
        registro = self.tabla.item(seleccion[0])['values']
        id_registro = registro[0]
        estado_actual = registro[-1]
        
        if estado_actual == 'Pagado':
            nuevo_estado = 'Pendiente'
        else:
            nuevo_estado = 'Pagado'
        
        if messagebox.askyesno("Confirmar", f"¿Está seguro de que desea cambiar el estado de '{estado_actual}' a '{nuevo_estado}'?"):
            self.servicio.cambiar_estado_registro(id_registro, nuevo_estado)
            self.actualizar_tabla()

    def generar_resumen_diario(self):
        fecha = self.fecha_resumen_diario.get()
        resumen = self.servicio.obtener_resumen_diario(fecha)
        
        if resumen:
            mensaje = (
                f"Resumen Diario para {fecha}\n"
                f"Total Diario: {resumen[0] or 0}€\n"
                f"Total Registros: {resumen[1] or 0}\n"
                f"Total Pagado: {resumen[2] or 0}€\n"
                f"Total Pendiente: {resumen[3] or 0}€"
            )
            messagebox.showinfo("Resumen Diario", mensaje)
        else:
            messagebox.showinfo("Resumen Diario", "No hay registros para la fecha seleccionada")

    def generar_resumen_mensual(self):
        fecha = self.fecha_resumen_mensual.get()[:7]
        resumen = self.servicio.obtener_resumen_mensual(fecha)
        
        if resumen:
            mensaje = (
                f"Resumen Mensual para {fecha}\n"
                f"Total Mensual: {resumen[0] or 0}€\n"
                f"Total Registros: {resumen[1] or 0}\n"
                f"Total Pagado: {resumen[2] or 0}€\n"
                f"Total Pendiente: {resumen[3] or 0}€"
            )
            messagebox.showinfo("Resumen Mensual", mensaje)
        else:
            messagebox.showinfo("Resumen Mensual", "No hay registros para el mes seleccionado")

    def exportar_excel(self):
        try:
            registros = self.servicio.obtener_registros()
            
            df = pd.DataFrame(registros, columns=['ID', 'Fecha', 'Número de Despacho', 'Importe', 'Nombre de Compañía', 'Estado'])
            
            archivo = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
            
            if archivo:
                df.to_excel(archivo, index=False)
                messagebox.showinfo("Éxito", f"Datos exportados a {archivo}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def exportar_pdf(self):
        try:
            registros = self.servicio.obtener_registros()
            
            archivo = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
            
            if archivo:
                doc = SimpleDocTemplate(archivo, pagesize=letter)
                elementos = []
                
                estilos = getSampleStyleSheet()
                titulo = estilos['Title']
                titulo.alignment = TA_CENTER
                
                elementos.append(Paragraph("Registro de Servicios", titulo))
                
                datos = [['ID', 'Fecha', 'Número de Despacho', 'Importe', 'Nombre de Compañía', 'Estado']]
                datos.extend(registros)
                
                tabla = Table(datos)
                tabla.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.grey),
                    ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0,0), (-1,0), 12),
                    ('BOTTOMPADDING', (0,0), (-1,0), 12),
                    ('BACKGROUND', (0,1), (-1,-1), colors.beige),
                    ('GRID', (0,0), (-1,-1), 1, colors.black)
                ]))
                
                elementos.append(tabla)
                
                doc.build(elementos)
                
                messagebox.showinfo("Éxito", f"Datos exportados a {archivo}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def on_closing(self):
        if messagebox.askokcancel("Salir", "¿Desea salir de la aplicación?"):
            self.servicio.cerrar_conexion()
            self.master.destroy()

def main():
    root = tk.Tk()
    app = ServiciosAbonadosApp(root)
    root.mainloop()

if __name__ == '__main__':
    main()
