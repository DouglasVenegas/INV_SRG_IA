"""
Sistema de Inventario de Reactivos Químicos
=============================================
Aplicación completa para gestionar inventario de reactivos en laboratorios

INSTALACIÓN DE DEPENDENCIAS:
pip install pandas openpyxl

INSTRUCCIONES DE USO:
1. Al iniciar, si no existe el archivo Excel base, se creará automáticamente con datos de ejemplo
2. Usa los botones de la interfaz para realizar las operaciones
3. Todos los cambios se guardan automáticamente en el archivo Excel
4. El log histórico se mantiene en un archivo separado

Autor: Sistema de Gestión de Laboratorio
Versión: 1.0
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import pandas as pd
from datetime import datetime, timedelta
import os
from pathlib import Path

# ============================================================================
# CONFIGURACIÓN GLOBAL
# ============================================================================

ARCHIVO_INVENTARIO = "inventario_reactivos.xlsx"
ARCHIVO_LOG = "log_movimientos.xlsx"

# ============================================================================
# CLASE PRINCIPAL DEL SISTEMA
# ============================================================================

class SistemaInventarioReactivos:
    """Clase principal que gestiona el inventario de reactivos químicos"""
    
    def __init__(self):
        """Inicializa el sistema y carga/crea los archivos necesarios"""
        self.df_inventario = None
        self.df_log = None
        self.cargar_o_crear_archivos()
    
    def cargar_o_crear_archivos(self):
        """Carga los archivos Excel o los crea si no existen"""
        # Cargar o crear inventario
        if os.path.exists(ARCHIVO_INVENTARIO):
            try:
                self.df_inventario = pd.read_excel(ARCHIVO_INVENTARIO)
                print(f"✓ Inventario cargado: {len(self.df_inventario)} reactivos")
            except Exception as e:
                print(f"Error al cargar inventario: {e}")
                self.crear_inventario_inicial()
        else:
            self.crear_inventario_inicial()
        
        # Cargar o crear log
        if os.path.exists(ARCHIVO_LOG):
            try:
                self.df_log = pd.read_excel(ARCHIVO_LOG)
                print(f"✓ Log cargado: {len(self.df_log)} movimientos")
            except Exception as e:
                print(f"Error al cargar log: {e}")
                self.crear_log_inicial()
        else:
            self.crear_log_inicial()
    
    def crear_inventario_inicial(self):
        """Crea un archivo de inventario inicial con datos de ejemplo"""
        datos_ejemplo = {
            'Reactivo': [
                'Ácido Sulfúrico 98%',
                'Hidróxido de Sodio',
                'Etanol 96%',
                'Cloruro de Sodio',
                'Acetona',
                'Ácido Clorhídrico 37%',
                'Glucosa',
                'Permanganato de Potasio'
            ],
            'Cantidad': [2.5, 5.0, 10.0, 15.0, 8.0, 3.0, 20.0, 1.5],
            'Unidad': ['L', 'kg', 'L', 'kg', 'L', 'L', 'kg', 'kg'],
            'Estado': ['disponible', 'disponible', 'disponible', 'disponible', 
                      'disponible', 'en uso', 'disponible', 'disponible'],
            'FechaVencimiento': [
                '2026-12-31', '2027-06-30', '2025-11-15', '2028-01-31',
                '2025-10-20', '2026-08-15', '2027-03-31', '2025-09-30'
            ],
            'FechaIngreso': [
                '2024-01-15', '2024-02-20', '2024-03-10', '2024-01-05',
                '2024-04-12', '2024-05-08', '2024-02-28', '2024-06-01'
            ],
            'Notas': [
                'Manipular con precaución - Corrosivo',
                'Almacenar en lugar seco',
                'Inflamable - Mantener alejado del fuego',
                'Grado analítico',
                'Inflamable - Buena ventilación',
                'Corrosivo - Usar en campana',
                'Almacenar en lugar fresco',
                'Oxidante - Riesgo de incendio'
            ]
        }
        
        self.df_inventario = pd.DataFrame(datos_ejemplo)
        self.guardar_inventario()
        print(f"✓ Inventario inicial creado con {len(self.df_inventario)} reactivos de ejemplo")
    
    def crear_log_inicial(self):
        """Crea un archivo de log inicial vacío"""
        self.df_log = pd.DataFrame(columns=[
            'Fecha', 'Hora', 'TipoMovimiento', 'Reactivo', 
            'Cantidad', 'Unidad', 'Usuario', 'ProyectoCurso', 'Notas'
        ])
        self.guardar_log()
        print("✓ Log de movimientos inicializado")
    
    def guardar_inventario(self):
        """Guarda el inventario en el archivo Excel"""
        try:
            self.df_inventario.to_excel(ARCHIVO_INVENTARIO, index=False)
            return True
        except Exception as e:
            print(f"Error al guardar inventario: {e}")
            return False
    
    def guardar_log(self):
        """Guarda el log de movimientos en el archivo Excel"""
        try:
            self.df_log.to_excel(ARCHIVO_LOG, index=False)
            return True
        except Exception as e:
            print(f"Error al guardar log: {e}")
            return False
    
    def buscar_reactivo(self, termino_busqueda):
        """
        Busca reactivos por nombre (búsqueda parcial)
        
        Args:
            termino_busqueda (str): Término a buscar en el nombre del reactivo
        
        Returns:
            DataFrame: Reactivos que coinciden con la búsqueda
        """
        if termino_busqueda.strip() == "":
            return self.df_inventario
        
        mascara = self.df_inventario['Reactivo'].str.contains(
            termino_busqueda, case=False, na=False
        )
        return self.df_inventario[mascara]
    
    def registrar_salida(self, nombre_reactivo, cantidad, usuario, proyecto_curso, notas=""):
        """
        Registra una salida de reactivo del inventario
        
        Args:
            nombre_reactivo (str): Nombre exacto del reactivo
            cantidad (float): Cantidad a retirar
            usuario (str): Usuario que solicita
            proyecto_curso (str): Proyecto o curso asociado
            notas (str): Notas adicionales
        
        Returns:
            tuple: (éxito, mensaje)
        """
        # Buscar el reactivo exacto
        mascara = self.df_inventario['Reactivo'] == nombre_reactivo
        
        if not mascara.any():
            return False, f"Reactivo '{nombre_reactivo}' no encontrado"
        
        idx = self.df_inventario[mascara].index[0]
        cantidad_actual = self.df_inventario.loc[idx, 'Cantidad']
        unidad = self.df_inventario.loc[idx, 'Unidad']
        
        # Verificar stock suficiente
        if cantidad > cantidad_actual:
            return False, f"Stock insuficiente. Disponible: {cantidad_actual} {unidad}"
        
        # Actualizar inventario
        nueva_cantidad = cantidad_actual - cantidad
        self.df_inventario.loc[idx, 'Cantidad'] = nueva_cantidad
        
        # Si se agota, cambiar estado
        if nueva_cantidad == 0:
            self.df_inventario.loc[idx, 'Estado'] = 'agotado'
        
        # Registrar en log
        ahora = datetime.now()
        nuevo_movimiento = {
            'Fecha': ahora.strftime('%Y-%m-%d'),
            'Hora': ahora.strftime('%H:%M:%S'),
            'TipoMovimiento': 'SALIDA',
            'Reactivo': nombre_reactivo,
            'Cantidad': cantidad,
            'Unidad': unidad,
            'Usuario': usuario,
            'ProyectoCurso': proyecto_curso,
            'Notas': notas
        }
        
        self.df_log = pd.concat([self.df_log, pd.DataFrame([nuevo_movimiento])], 
                                ignore_index=True)
        
        # Guardar cambios
        self.guardar_inventario()
        self.guardar_log()
        
        return True, f"Salida registrada: {cantidad} {unidad} de {nombre_reactivo}"
    
    def registrar_entrada(self, nombre_reactivo, cantidad, usuario, proyecto_curso, 
                         fecha_vencimiento=None, notas=""):
        """
        Registra una entrada de reactivo al inventario
        
        Args:
            nombre_reactivo (str): Nombre del reactivo
            cantidad (float): Cantidad a agregar
            usuario (str): Usuario que registra la entrada
            proyecto_curso (str): Proyecto o curso asociado
            fecha_vencimiento (str): Fecha de vencimiento (YYYY-MM-DD)
            notas (str): Notas adicionales
        
        Returns:
            tuple: (éxito, mensaje)
        """
        # Buscar si el reactivo ya existe
        mascara = self.df_inventario['Reactivo'] == nombre_reactivo
        
        if mascara.any():
            # Reactivo existente: actualizar cantidad
            idx = self.df_inventario[mascara].index[0]
            cantidad_actual = self.df_inventario.loc[idx, 'Cantidad']
            nueva_cantidad = cantidad_actual + cantidad
            self.df_inventario.loc[idx, 'Cantidad'] = nueva_cantidad
            
            # Actualizar estado si estaba agotado
            if self.df_inventario.loc[idx, 'Estado'] == 'agotado':
                self.df_inventario.loc[idx, 'Estado'] = 'disponible'
            
            # Actualizar fecha de vencimiento si se proporciona
            if fecha_vencimiento:
                self.df_inventario.loc[idx, 'FechaVencimiento'] = fecha_vencimiento
            
            unidad = self.df_inventario.loc[idx, 'Unidad']
            mensaje = f"Entrada registrada: +{cantidad} {unidad}. Nuevo stock: {nueva_cantidad} {unidad}"
        else:
            # Reactivo nuevo: agregar al inventario
            if not fecha_vencimiento:
                fecha_vencimiento = (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')
            
            nuevo_reactivo = {
                'Reactivo': nombre_reactivo,
                'Cantidad': cantidad,
                'Unidad': 'L',  # Unidad por defecto
                'Estado': 'disponible',
                'FechaVencimiento': fecha_vencimiento,
                'FechaIngreso': datetime.now().strftime('%Y-%m-%d'),
                'Notas': notas
            }
            
            self.df_inventario = pd.concat([self.df_inventario, 
                                           pd.DataFrame([nuevo_reactivo])], 
                                          ignore_index=True)
            
            unidad = 'L'
            mensaje = f"Nuevo reactivo agregado: {cantidad} {unidad} de {nombre_reactivo}"
        
        # Registrar en log
        ahora = datetime.now()
        nuevo_movimiento = {
            'Fecha': ahora.strftime('%Y-%m-%d'),
            'Hora': ahora.strftime('%H:%M:%S'),
            'TipoMovimiento': 'ENTRADA',
            'Reactivo': nombre_reactivo,
            'Cantidad': cantidad,
            'Unidad': unidad,
            'Usuario': usuario,
            'ProyectoCurso': proyecto_curso,
            'Notas': notas
        }
        
        self.df_log = pd.concat([self.df_log, pd.DataFrame([nuevo_movimiento])], 
                                ignore_index=True)
        
        # Guardar cambios
        self.guardar_inventario()
        self.guardar_log()
        
        return True, mensaje
    
    def verificar_vencimientos(self, dias_alerta=30):
        """
        Verifica reactivos vencidos o próximos a vencer
        
        Args:
            dias_alerta (int): Días de anticipación para alertar
        
        Returns:
            dict: Diccionario con reactivos vencidos y por vencer
        """
        hoy = datetime.now()
        fecha_limite = hoy + timedelta(days=dias_alerta)
        
        # Convertir columna a datetime
        self.df_inventario['FechaVencimiento'] = pd.to_datetime(
            self.df_inventario['FechaVencimiento']
        )
        
        # Reactivos vencidos
        vencidos = self.df_inventario[
            self.df_inventario['FechaVencimiento'] < hoy
        ]
        
        # Reactivos próximos a vencer
        proximos_vencer = self.df_inventario[
            (self.df_inventario['FechaVencimiento'] >= hoy) &
            (self.df_inventario['FechaVencimiento'] <= fecha_limite)
        ]
        
        return {
            'vencidos': vencidos,
            'proximos_vencer': proximos_vencer
        }
    
    def obtener_reactivos_problematicos(self):
        """
        Obtiene lista de reactivos con problemas (vencidos, dañados, agotados)
        
        Returns:
            DataFrame: Reactivos con problemas
        """
        estados_problema = ['vencido', 'dañado', 'agotado']
        return self.df_inventario[
            self.df_inventario['Estado'].isin(estados_problema)
        ]
    
    def generar_reporte_stock(self):
        """
        Genera reporte completo del estado del inventario
        
        Returns:
            str: Reporte en formato texto
        """
        total_reactivos = len(self.df_inventario)
        disponibles = len(self.df_inventario[self.df_inventario['Estado'] == 'disponible'])
        en_uso = len(self.df_inventario[self.df_inventario['Estado'] == 'en uso'])
        
        vencimientos = self.verificar_vencimientos()
        
        reporte = f"""
╔══════════════════════════════════════════════════════════════╗
║           REPORTE DE INVENTARIO DE REACTIVOS                 ║
╚══════════════════════════════════════════════════════════════╝

Fecha del reporte: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

RESUMEN GENERAL:
  • Total de reactivos: {total_reactivos}
  • Disponibles: {disponibles}
  • En uso: {en_uso}
  • Vencidos: {len(vencimientos['vencidos'])}
  • Próximos a vencer (30 días): {len(vencimientos['proximos_vencer'])}

ALERTAS:
"""
        
        if len(vencimientos['vencidos']) > 0:
            reporte += "\n⚠️  REACTIVOS VENCIDOS:\n"
            for _, row in vencimientos['vencidos'].iterrows():
                reporte += f"  - {row['Reactivo']}: Vencido el {row['FechaVencimiento'].strftime('%Y-%m-%d')}\n"
        
        if len(vencimientos['proximos_vencer']) > 0:
            reporte += "\n⚠️  PRÓXIMOS A VENCER (30 días):\n"
            for _, row in vencimientos['proximos_vencer'].iterrows():
                dias = (row['FechaVencimiento'] - datetime.now()).days
                reporte += f"  - {row['Reactivo']}: Vence en {dias} días ({row['FechaVencimiento'].strftime('%Y-%m-%d')})\n"
        
        # Reactivos con bajo stock (menos de 1 unidad)
        bajo_stock = self.df_inventario[self.df_inventario['Cantidad'] < 1]
        if len(bajo_stock) > 0:
            reporte += "\n⚠️  STOCK BAJO (< 1 unidad):\n"
            for _, row in bajo_stock.iterrows():
                reporte += f"  - {row['Reactivo']}: {row['Cantidad']} {row['Unidad']}\n"
        
        return reporte


# ============================================================================
# INTERFAZ GRÁFICA
# ============================================================================

class InterfazInventario:
    """Interfaz gráfica para el sistema de inventario"""
    
    def __init__(self, root):
        """Inicializa la interfaz gráfica"""
        self.root = root
        self.root.title("Sistema de Inventario de Reactivos Químicos")
        self.root.geometry("1200x700")
        
        # Inicializar sistema
        self.sistema = SistemaInventarioReactivos()
        
        # Crear interfaz
        self.crear_widgets()
        
        # Actualizar tabla inicial
        self.actualizar_tabla()
        
        # Verificar vencimientos al iniciar
        self.verificar_alertas_inicio()
    
    def crear_widgets(self):
        """Crea todos los widgets de la interfaz"""
        # Frame superior con título
        frame_titulo = tk.Frame(self.root, bg='#2c3e50', height=60)
        frame_titulo.pack(fill=tk.X)
        
        titulo = tk.Label(frame_titulo, text="🧪 SISTEMA DE INVENTARIO DE REACTIVOS QUÍMICOS",
                         font=('Arial', 18, 'bold'), bg='#2c3e50', fg='white')
        titulo.pack(pady=15)
        
        # Frame principal con notebook (pestañas)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Pestaña 1: Inventario
        self.crear_pestana_inventario()
        
        # Pestaña 2: Movimientos
        self.crear_pestana_movimientos()
        
        # Pestaña 3: Alertas
        self.crear_pestana_alertas()
        
        # Pestaña 4: Reportes
        self.crear_pestana_reportes()
    
    def crear_pestana_inventario(self):
        """Crea la pestaña de inventario"""
        frame_inventario = ttk.Frame(self.notebook)
        self.notebook.add(frame_inventario, text='📦 Inventario')
        
        # Frame de búsqueda
        frame_busqueda = tk.Frame(frame_inventario)
        frame_busqueda.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(frame_busqueda, text="Buscar reactivo:", font=('Arial', 10)).pack(side=tk.LEFT, padx=5)
        self.entry_busqueda = tk.Entry(frame_busqueda, width=40, font=('Arial', 10))
        self.entry_busqueda.pack(side=tk.LEFT, padx=5)
        
        tk.Button(frame_busqueda, text="🔍 Buscar", command=self.buscar_reactivo,
                 bg='#3498db', fg='white', font=('Arial', 10)).pack(side=tk.LEFT, padx=5)
        
        tk.Button(frame_busqueda, text="🔄 Mostrar Todos", command=self.actualizar_tabla,
                 bg='#95a5a6', fg='white', font=('Arial', 10)).pack(side=tk.LEFT, padx=5)
        
        # Tabla de inventario
        frame_tabla = tk.Frame(frame_inventario)
        frame_tabla.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Scrollbars
        scroll_y = tk.Scrollbar(frame_tabla, orient=tk.VERTICAL)
        scroll_x = tk.Scrollbar(frame_tabla, orient=tk.HORIZONTAL)
        
        # Tabla
        columnas = ('Nombre', 'Cantidad', 'Unidad', 'Estado', 'Vencimiento', 'Ingreso', 'Notas')
        self.tabla_inventario = ttk.Treeview(frame_tabla, columns=columnas, show='headings',
                                            yscrollcommand=scroll_y.set,
                                            xscrollcommand=scroll_x.set)
        
        scroll_y.config(command=self.tabla_inventario.yview)
        scroll_x.config(command=self.tabla_inventario.xview)
        
        # Configurar columnas
        anchos = [250, 80, 60, 100, 100, 100, 300]
        for col, ancho in zip(columnas, anchos):
            self.tabla_inventario.heading(col, text=col)
            self.tabla_inventario.column(col, width=ancho)
        
        # Empaquetar
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.tabla_inventario.pack(fill=tk.BOTH, expand=True)
        
        # Botones de acción
        frame_botones = tk.Frame(frame_inventario)
        frame_botones.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Button(frame_botones, text="➕ Nueva Entrada", command=self.ventana_nueva_entrada,
                 bg='#27ae60', fg='white', font=('Arial', 10, 'bold'), 
                 width=15, height=2).pack(side=tk.LEFT, padx=5)
        
        tk.Button(frame_botones, text="➖ Registrar Salida", command=self.ventana_registrar_salida,
                 bg='#e74c3c', fg='white', font=('Arial', 10, 'bold'),
                 width=15, height=2).pack(side=tk.LEFT, padx=5)
    
    def crear_pestana_movimientos(self):
        """Crea la pestaña de movimientos"""
        frame_movimientos = ttk.Frame(self.notebook)
        self.notebook.add(frame_movimientos, text='📋 Movimientos')
        
        # Título
        tk.Label(frame_movimientos, text="Historial de Movimientos",
                font=('Arial', 14, 'bold')).pack(pady=10)
        
        # Tabla de movimientos
        frame_tabla = tk.Frame(frame_movimientos)
        frame_tabla.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        scroll_y = tk.Scrollbar(frame_tabla, orient=tk.VERTICAL)
        scroll_x = tk.Scrollbar(frame_tabla, orient=tk.HORIZONTAL)
        
        columnas = ('Fecha', 'Hora', 'Tipo', 'Reactivo', 'Cantidad', 'Unidad', 
                   'Usuario', 'Proyecto/Curso', 'Notas')
        self.tabla_movimientos = ttk.Treeview(frame_tabla, columns=columnas, show='headings',
                                             yscrollcommand=scroll_y.set,
                                             xscrollcommand=scroll_x.set)
        
        scroll_y.config(command=self.tabla_movimientos.yview)
        scroll_x.config(command=self.tabla_movimientos.xview)
        
        anchos = [100, 80, 80, 200, 80, 60, 120, 150, 200]
        for col, ancho in zip(columnas, anchos):
            self.tabla_movimientos.heading(col, text=col)
            self.tabla_movimientos.column(col, width=ancho)
        
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.tabla_movimientos.pack(fill=tk.BOTH, expand=True)
        
        # Botón actualizar
        tk.Button(frame_movimientos, text="🔄 Actualizar", command=self.actualizar_tabla_movimientos,
                 bg='#3498db', fg='white', font=('Arial', 10)).pack(pady=10)
    
    def crear_pestana_alertas(self):
        """Crea la pestaña de alertas"""
        frame_alertas = ttk.Frame(self.notebook)
        self.notebook.add(frame_alertas, text='⚠️ Alertas')
        
        # Título
        tk.Label(frame_alertas, text="Alertas y Advertencias",
                font=('Arial', 14, 'bold')).pack(pady=10)
        
        # Área de texto para alertas
        self.texto_alertas = scrolledtext.ScrolledText(frame_alertas, 
                                                       font=('Courier', 10),
                                                       height=25)
        self.texto_alertas.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Botón actualizar
        tk.Button(frame_alertas, text="🔄 Verificar Alertas", command=self.actualizar_alertas,
                 bg='#e67e22', fg='white', font=('Arial', 10, 'bold')).pack(pady=10)
    
    def crear_pestana_reportes(self):
        """Crea la pestaña de reportes"""
        frame_reportes = ttk.Frame(self.notebook)
        self.notebook.add(frame_reportes, text='📊 Reportes')
        
        # Título
        tk.Label(frame_reportes, text="Reportes del Sistema",
                font=('Arial', 14, 'bold')).pack(pady=10)
        
        # Área de texto para reportes
        self.texto_reportes = scrolledtext.ScrolledText(frame_reportes,
                                                        font=('Courier', 10),
                                                        height=25)
        self.texto_reportes.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Botones
        frame_botones = tk.Frame(frame_reportes)
        frame_botones.pack(pady=10)
        
        tk.Button(frame_botones, text="📊 Generar Reporte Stock", 
                 command=self.generar_reporte_stock,
                 bg='#9b59b6', fg='white', font=('Arial', 10)).pack(side=tk.LEFT, padx=5)
        
        tk.Button(frame_botones, text="💾 Exportar a TXT",
                 command=self.exportar_reporte,
                 bg='#34495e', fg='white', font=('Arial', 10)).pack(side=tk.LEFT, padx=5)
    
    def actualizar_tabla(self):
        """Actualiza la tabla de inventario con todos los reactivos"""
        # Limpiar tabla
        for item in self.tabla_inventario.get_children():
            self.tabla_inventario.delete(item)
        
        # Insertar datos
        for _, row in self.sistema.df_inventario.iterrows():
            valores = (
                row['Reactivo'],
                f"{row['Cantidad']:.2f}",
                row['Unidad'],
                row['Estado'],
                row['FechaVencimiento'],
                row['FechaIngreso'],
                row['Notas']
            )
            self.tabla_inventario.insert('', tk.END, values=valores)
    
    def buscar_reactivo(self):
        """Busca reactivos según el término ingresado"""
        termino = self.entry_busqueda.get()
        resultados = self.sistema.buscar_reactivo(termino)
        
        # Limpiar tabla
        for item in self.tabla_inventario.get_children():
            self.tabla_inventario.delete(item)
        
        # Mostrar resultados
        if len(resultados) == 0:
            messagebox.showinfo("Búsqueda", f"No se encontraron reactivos con '{termino}'")
        else:
            for _, row in resultados.iterrows():
                valores = (
                    row['Reactivo'],
                    f"{row['Cantidad']:.2f}",
                    row['Unidad'],
                    row['Estado'],
                    row['FechaVencimiento'],
                    row['FechaIngreso'],
                    row['Notas']
                )
                self.tabla_inventario.insert('', tk.END, values=valores)
    
    def ventana_nueva_entrada(self):
        """Abre ventana para registrar una nueva entrada"""
        ventana = tk.Toplevel(self.root)
        ventana.title("Nueva Entrada de Reactivo")
        ventana.geometry("500x450")
        
        # Campos
        campos = [
            ("Nombre del Reactivo:", "nombre"),
            ("Cantidad:", "cantidad"),
            ("Unidad (L/kg/g/mL):", "unidad"),
            ("Usuario:", "usuario"),
            ("Proyecto/Curso:", "proyecto"),
            ("Fecha Vencimiento (YYYY-MM-DD):", "vencimiento"),
            ("Notas:", "notas")
        ]
        
        entries = {}
        for i, (label, key) in enumerate(campos):
            tk.Label(ventana, text=label, font=('Arial', 10)).grid(row=i, column=0, 
                                                                    sticky='e', padx=10, pady=8)
            if key == "notas":
                entries[key] = tk.Text(ventana, width=30, height=4, font=('Arial', 10))
                entries[key].grid(row=i, column=1, padx=10, pady=8)
            else:
                entries[key] = tk.Entry(ventana, width=35, font=('Arial', 10))
                entries[key].grid(row=i, column=1, padx=10, pady=8)
        
        # Valores por defecto
        entries['unidad'].insert(0, 'L')
        entries['vencimiento'].insert(0, (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d'))
        
        def registrar():
            try:
                nombre = entries['nombre'].get().strip()
                cantidad = float(entries['cantidad'].get())
                usuario = entries['usuario'].get().strip()
                proyecto = entries['proyecto'].get().strip()
                vencimiento = entries['vencimiento'].get().strip()
                notas = entries['notas'].get('1.0', tk.END).strip()
                
                if not nombre or not usuario or not proyecto:
                    messagebox.showerror("Error", "Complete todos los campos obligatorios")
                    return
                
                # Actualizar unidad en el inventario si es reactivo existente
                mascara = self.sistema.df_inventario['Reactivo'] == nombre
                if mascara.any():
                    idx = self.sistema.df_inventario[mascara].index[0]
                    unidad_actual = self.sistema.df_inventario.loc[idx, 'Unidad']
                else:
                    unidad_actual = entries['unidad'].get().strip()
                    # Actualizar la unidad en el DataFrame antes de registrar
                    if mascara.any():
                        pass  # Ya existe
                    else:
                        # Se actualizará en registrar_entrada
                        pass
                
                exito, mensaje = self.sistema.registrar_entrada(
                    nombre, cantidad, usuario, proyecto, vencimiento, notas
                )
                
                # Si es nuevo reactivo, actualizar la unidad especificada
                mascara = self.sistema.df_inventario['Reactivo'] == nombre
                if mascara.any():
                    idx = self.sistema.df_inventario[mascara].index[0]
                    unidad_nueva = entries['unidad'].get().strip()
                    if unidad_nueva:
                        self.sistema.df_inventario.loc[idx, 'Unidad'] = unidad_nueva
                        self.sistema.guardar_inventario()
                
                if exito:
                    messagebox.showinfo("Éxito", mensaje)
                    self.actualizar_tabla()
                    self.actualizar_tabla_movimientos()
                    ventana.destroy()
                else:
                    messagebox.showerror("Error", mensaje)
            except ValueError:
                messagebox.showerror("Error", "La cantidad debe ser un número válido")
            except Exception as e:
                messagebox.showerror("Error", f"Error inesperado: {str(e)}")
        
        # Botones
        frame_botones = tk.Frame(ventana)
        frame_botones.grid(row=len(campos), column=0, columnspan=2, pady=20)
        
        tk.Button(frame_botones, text="✓ Registrar Entrada", command=registrar,
                 bg='#27ae60', fg='white', font=('Arial', 11, 'bold'),
                 width=18).pack(side=tk.LEFT, padx=5)
        
        tk.Button(frame_botones, text="✗ Cancelar", command=ventana.destroy,
                 bg='#95a5a6', fg='white', font=('Arial', 11),
                 width=12).pack(side=tk.LEFT, padx=5)
    
    def ventana_registrar_salida(self):
        """Abre ventana para registrar una salida"""
        ventana = tk.Toplevel(self.root)
        ventana.title("Registrar Salida de Reactivo")
        ventana.geometry("500x400")
        
        # Campos
        tk.Label(ventana, text="Nombre del Reactivo:", 
                font=('Arial', 10)).grid(row=0, column=0, sticky='e', padx=10, pady=8)
        
        # Combobox con lista de reactivos
        nombres_reactivos = self.sistema.df_inventario['Reactivo'].tolist()
        combo_reactivo = ttk.Combobox(ventana, values=nombres_reactivos, 
                                     width=33, font=('Arial', 10))
        combo_reactivo.grid(row=0, column=1, padx=10, pady=8)
        
        campos = [
            ("Cantidad a retirar:", "cantidad"),
            ("Usuario que solicita:", "usuario"),
            ("Proyecto/Curso:", "proyecto"),
            ("Notas:", "notas")
        ]
        
        entries = {}
        for i, (label, key) in enumerate(campos, start=1):
            tk.Label(ventana, text=label, font=('Arial', 10)).grid(row=i, column=0,
                                                                    sticky='e', padx=10, pady=8)
            if key == "notas":
                entries[key] = tk.Text(ventana, width=30, height=4, font=('Arial', 10))
                entries[key].grid(row=i, column=1, padx=10, pady=8)
            else:
                entries[key] = tk.Entry(ventana, width=35, font=('Arial', 10))
                entries[key].grid(row=i, column=1, padx=10, pady=8)
        
        def registrar():
            try:
                nombre = combo_reactivo.get().strip()
                cantidad = float(entries['cantidad'].get())
                usuario = entries['usuario'].get().strip()
                proyecto = entries['proyecto'].get().strip()
                notas = entries['notas'].get('1.0', tk.END).strip()
                
                if not nombre or not usuario or not proyecto:
                    messagebox.showerror("Error", "Complete todos los campos obligatorios")
                    return
                
                if cantidad <= 0:
                    messagebox.showerror("Error", "La cantidad debe ser mayor a 0")
                    return
                
                exito, mensaje = self.sistema.registrar_salida(
                    nombre, cantidad, usuario, proyecto, notas
                )
                
                if exito:
                    messagebox.showinfo("Éxito", mensaje)
                    self.actualizar_tabla()
                    self.actualizar_tabla_movimientos()
                    ventana.destroy()
                else:
                    messagebox.showerror("Error", mensaje)
            except ValueError:
                messagebox.showerror("Error", "La cantidad debe ser un número válido")
            except Exception as e:
                messagebox.showerror("Error", f"Error inesperado: {str(e)}")
        
        # Botones
        frame_botones = tk.Frame(ventana)
        frame_botones.grid(row=len(campos)+1, column=0, columnspan=2, pady=20)
        
        tk.Button(frame_botones, text="✓ Registrar Salida", command=registrar,
                 bg='#e74c3c', fg='white', font=('Arial', 11, 'bold'),
                 width=18).pack(side=tk.LEFT, padx=5)
        
        tk.Button(frame_botones, text="✗ Cancelar", command=ventana.destroy,
                 bg='#95a5a6', fg='white', font=('Arial', 11),
                 width=12).pack(side=tk.LEFT, padx=5)
    
    def actualizar_tabla_movimientos(self):
        """Actualiza la tabla de movimientos"""
        # Limpiar tabla
        for item in self.tabla_movimientos.get_children():
            self.tabla_movimientos.delete(item)
        
        # Insertar datos (últimos 100 movimientos)
        df_reciente = self.sistema.df_log.tail(100).iloc[::-1]  # Invertir para mostrar más recientes primero
        
        for _, row in df_reciente.iterrows():
            valores = (
                row['Fecha'],
                row['Hora'],
                row['TipoMovimiento'],
                row['Reactivo'],
                f"{row['Cantidad']:.2f}",
                row['Unidad'],
                row['Usuario'],
                row['ProyectoCurso'],
                row['Notas']
            )
            
            # Colorear según tipo de movimiento
            item_id = self.tabla_movimientos.insert('', tk.END, values=valores)
            if row['TipoMovimiento'] == 'ENTRADA':
                self.tabla_movimientos.item(item_id, tags=('entrada',))
            else:
                self.tabla_movimientos.item(item_id, tags=('salida',))
        
        # Configurar colores
        self.tabla_movimientos.tag_configure('entrada', background='#d5f4e6')
        self.tabla_movimientos.tag_configure('salida', background='#fadbd8')
    
    def actualizar_alertas(self):
        """Actualiza el panel de alertas"""
        self.texto_alertas.delete('1.0', tk.END)
        
        # Verificar vencimientos
        vencimientos = self.sistema.verificar_vencimientos(dias_alerta=30)
        
        texto = "═" * 70 + "\n"
        texto += "           ALERTAS Y ADVERTENCIAS DEL SISTEMA\n"
        texto += "═" * 70 + "\n\n"
        texto += f"Fecha de verificación: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # Reactivos vencidos
        if len(vencimientos['vencidos']) > 0:
            texto += "🔴 REACTIVOS VENCIDOS (ACCIÓN INMEDIATA REQUERIDA):\n"
            texto += "─" * 70 + "\n"
            for _, row in vencimientos['vencidos'].iterrows():
                dias_vencido = (datetime.now() - row['FechaVencimiento']).days
                texto += f"  • {row['Reactivo']}\n"
                texto += f"    Stock: {row['Cantidad']:.2f} {row['Unidad']}\n"
                texto += f"    Fecha de vencimiento: {row['FechaVencimiento'].strftime('%Y-%m-%d')}\n"
                texto += f"    Días vencido: {dias_vencido} días\n"
                texto += f"    Notas: {row['Notas']}\n\n"
        else:
            texto += "✓ No hay reactivos vencidos\n\n"
        
        # Próximos a vencer
        if len(vencimientos['proximos_vencer']) > 0:
            texto += "🟡 REACTIVOS PRÓXIMOS A VENCER (30 días):\n"
            texto += "─" * 70 + "\n"
            for _, row in vencimientos['proximos_vencer'].iterrows():
                dias_restantes = (row['FechaVencimiento'] - datetime.now()).days
                texto += f"  • {row['Reactivo']}\n"
                texto += f"    Stock: {row['Cantidad']:.2f} {row['Unidad']}\n"
                texto += f"    Fecha de vencimiento: {row['FechaVencimiento'].strftime('%Y-%m-%d')}\n"
                texto += f"    Días restantes: {dias_restantes} días\n"
                texto += f"    Notas: {row['Notas']}\n\n"
        else:
            texto += "✓ No hay reactivos próximos a vencer en los próximos 30 días\n\n"
        
        # Stock bajo
        bajo_stock = self.sistema.df_inventario[self.sistema.df_inventario['Cantidad'] < 1]
        if len(bajo_stock) > 0:
            texto += "🟠 REACTIVOS CON STOCK BAJO (< 1 unidad):\n"
            texto += "─" * 70 + "\n"
            for _, row in bajo_stock.iterrows():
                texto += f"  • {row['Reactivo']}: {row['Cantidad']:.2f} {row['Unidad']}\n"
                if row['Estado'] == 'agotado':
                    texto += "    ⚠️ AGOTADO - Necesita reposición urgente\n"
                texto += "\n"
        else:
            texto += "✓ Todos los reactivos tienen stock adecuado\n\n"
        
        # Reactivos dañados
        danados = self.sistema.df_inventario[self.sistema.df_inventario['Estado'] == 'dañado']
        if len(danados) > 0:
            texto += "🔴 REACTIVOS DAÑADOS:\n"
            texto += "─" * 70 + "\n"
            for _, row in danados.iterrows():
                texto += f"  • {row['Reactivo']}: {row['Cantidad']:.2f} {row['Unidad']}\n"
                texto += f"    Notas: {row['Notas']}\n\n"
        
        texto += "\n" + "═" * 70 + "\n"
        texto += "Fin del reporte de alertas\n"
        
        self.texto_alertas.insert('1.0', texto)
        
        # Colorear texto según nivel de alerta
        self.texto_alertas.tag_configure('vencido', foreground='red', font=('Courier', 10, 'bold'))
        self.texto_alertas.tag_configure('alerta', foreground='orange', font=('Courier', 10, 'bold'))
    
    def generar_reporte_stock(self):
        """Genera el reporte completo de stock"""
        self.texto_reportes.delete('1.0', tk.END)
        reporte = self.sistema.generar_reporte_stock()
        self.texto_reportes.insert('1.0', reporte)
    
    def exportar_reporte(self):
        """Exporta el reporte actual a un archivo de texto"""
        contenido = self.texto_reportes.get('1.0', tk.END)
        
        if contenido.strip() == "":
            messagebox.showwarning("Advertencia", "No hay reporte para exportar. Genere uno primero.")
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        nombre_archivo = f"reporte_inventario_{timestamp}.txt"
        
        try:
            with open(nombre_archivo, 'w', encoding='utf-8') as f:
                f.write(contenido)
            messagebox.showinfo("Éxito", f"Reporte exportado a:\n{nombre_archivo}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar el reporte:\n{str(e)}")
    
    def verificar_alertas_inicio(self):
        """Verifica alertas al iniciar y muestra notificación si hay problemas"""
        vencimientos = self.sistema.verificar_vencimientos(dias_alerta=30)
        
        alertas = []
        
        if len(vencimientos['vencidos']) > 0:
            alertas.append(f"⚠️ {len(vencimientos['vencidos'])} reactivo(s) vencido(s)")
        
        if len(vencimientos['proximos_vencer']) > 0:
            alertas.append(f"⚠️ {len(vencimientos['proximos_vencer'])} reactivo(s) por vencer")
        
        bajo_stock = self.sistema.df_inventario[self.sistema.df_inventario['Cantidad'] < 1]
        if len(bajo_stock) > 0:
            alertas.append(f"⚠️ {len(bajo_stock)} reactivo(s) con stock bajo")
        
        if alertas:
            mensaje = "ALERTAS DEL SISTEMA:\n\n" + "\n".join(alertas)
            mensaje += "\n\nRevise la pestaña 'Alertas' para más detalles."
            messagebox.showwarning("Alertas del Sistema", mensaje)


# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

def main():
    """Función principal que inicia la aplicación"""
    root = tk.Tk()
    app = InterfazInventario(root)
    root.mainloop()


if __name__ == "__main__":
    print("=" * 70)
    print("  SISTEMA DE INVENTARIO DE REACTIVOS QUÍMICOS")
    print("=" * 70)
    print("\nIniciando aplicación...")
    print("\nREQUISITOS:")
    print("  • Python 3.7 o superior")
    print("  • pandas: pip install pandas")
    print("  • openpyxl: pip install openpyxl")
    print("\nARCHIVOS GENERADOS:")
    print(f"  • {ARCHIVO_INVENTARIO} - Base de datos principal")
    print(f"  • {ARCHIVO_LOG} - Historial de movimientos")
    print("\n" + "=" * 70 + "\n")
    
    main()