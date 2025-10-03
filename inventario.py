import gspread
from oauth2client.service_account import ServiceAccountCredentials
import streamlit as st

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# st.secrets["GOOGLE_SERVICE_ACCOUNT"] ya es un diccionario
creds = ServiceAccountCredentials.from_json_keyfile_dict(
    st.secrets["GOOGLE_SERVICE_ACCOUNT"],  # PASAR DIRECTO
    SCOPES
)

client = gspread.authorize(creds)

SHEET_ID = "1Z16IVvPiDIZ8UsNRSiAGX5eccW-ktoWXrZaxSRnGx4Y"

sheet_inventario = client.open_by_key(SHEET_ID).worksheet("Inventario")
sheet_log = client.open_by_key(SHEET_ID).worksheet("Log")


# ============================================================================
# CONFIGURACIÓN DE STREAMLIT
# ============================================================================

st.set_page_config(
    page_title="Sistema de Inventario de Reactivos",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🧪 Sistema de Inventario de Reactivos Químicos (Sheets)")

# ============================================================================
# CLASE PRINCIPAL DEL SISTEMA
# ============================================================================

class SistemaInventarioReactivos:
    """Gestión de inventario de reactivos químicos con respaldo en Google Sheets"""
    
    def __init__(self):
        self.df_inventario = None
        self.df_log = None
        self.cargar_o_crear_archivos()
    
    # ---------------------------
    # CARGA DE DATOS
    # ---------------------------
    
    def cargar_o_crear_archivos(self):
        """Carga datos desde Google Sheets"""
        try:
            inventario_data = sheet_inventario.get_all_records()
            self.df_inventario = pd.DataFrame(inventario_data)
        except Exception as e:
            st.error(f"Error al cargar inventario desde Sheets: {e}")
            self.crear_inventario_inicial()
        
        try:
            log_data = sheet_log.get_all_records()
            self.df_log = pd.DataFrame(log_data)
        except Exception as e:
            st.error(f"Error al cargar log desde Sheets: {e}")
            self.crear_log_inicial()
    
    # ---------------------------
    # CREAR DATOS INICIALES
    # ---------------------------
    
    def crear_inventario_inicial(self):
        datos_ejemplo = {
            'Reactivo': [
                'Ácido Sulfúrico 98%', 'Hidróxido de Sodio', 'Etanol 96%',
                'Cloruro de Sodio', 'Acetona', 'Ácido Clorhídrico 37%',
                'Glucosa', 'Permanganato de Potasio'
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
                'Manipular con precaución - Corrosivo', 'Almacenar en lugar seco',
                'Inflamable - Mantener alejado del fuego', 'Grado analítico',
                'Inflamable - Buena ventilación', 'Corrosivo - Usar en campana',
                'Almacenar en lugar fresco', 'Oxidante - Riesgo de incendio'
            ]
        }
        self.df_inventario = pd.DataFrame(datos_ejemplo)
        self.guardar_inventario()
    
    def crear_log_inicial(self):
        self.df_log = pd.DataFrame(columns=[
            'Fecha', 'Hora', 'TipoMovimiento', 'Reactivo', 
            'Cantidad', 'Unidad', 'Usuario', 'ProyectoCurso', 'Notas'
        ])
        self.guardar_log()
    
    # ---------------------------
    # GUARDAR DATOS EN SHEETS
    # ---------------------------
    
    def guardar_inventario(self):
        try:
            sheet_inventario.clear()
            sheet_inventario.update([self.df_inventario.columns.tolist()] + self.df_inventario.values.tolist())
            return True
        except Exception as e:
            st.error(f"Error al guardar inventario en Sheets: {e}")
            return False
    
    def guardar_log(self):
        try:
            sheet_log.clear()
            sheet_log.update([self.df_log.columns.tolist()] + self.df_log.values.tolist())
            return True
        except Exception as e:
            st.error(f"Error al guardar log en Sheets: {e}")
            return False
    
    # ---------------------------
    # BÚSQUEDA
    # ---------------------------
    
    def buscar_reactivo(self, termino_busqueda):
        if termino_busqueda.strip() == "":
            return self.df_inventario
        mascara = self.df_inventario['Reactivo'].str.contains(termino_busqueda, case=False, na=False)
        return self.df_inventario[mascara]
    
    # ---------------------------
    # REGISTRAR MOVIMIENTOS
    # ---------------------------
    
    def registrar_salida(self, nombre_reactivo, cantidad, usuario, proyecto_curso, notas=""):
        mascara = self.df_inventario['Reactivo'] == nombre_reactivo
        if not mascara.any():
            return False, f"Reactivo '{nombre_reactivo}' no encontrado"
        
        idx = self.df_inventario[mascara].index[0]
        cantidad_actual = self.df_inventario.loc[idx, 'Cantidad']
        unidad = self.df_inventario.loc[idx, 'Unidad']
        
        if cantidad > cantidad_actual:
            return False, f"Stock insuficiente. Disponible: {cantidad_actual} {unidad}"
        
        self.df_inventario.loc[idx, 'Cantidad'] -= cantidad
        if self.df_inventario.loc[idx, 'Cantidad'] == 0:
            self.df_inventario.loc[idx, 'Estado'] = 'agotado'
        
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
        self.df_log = pd.concat([self.df_log, pd.DataFrame([nuevo_movimiento])], ignore_index=True)
        
        self.guardar_inventario()
        self.guardar_log()
        return True, f"Salida registrada: {cantidad} {unidad} de {nombre_reactivo}"
    
    def registrar_entrada(self, nombre_reactivo, cantidad, usuario, proyecto_curso, 
                           unidad='L', fecha_vencimiento=None, notas=""):
        mascara = self.df_inventario['Reactivo'] == nombre_reactivo
        if mascara.any():
            idx = self.df_inventario[mascara].index[0]
            self.df_inventario.loc[idx, 'Cantidad'] += cantidad
            if self.df_inventario.loc[idx, 'Estado'] == 'agotado':
                self.df_inventario.loc[idx, 'Estado'] = 'disponible'
            if fecha_vencimiento:
                self.df_inventario.loc[idx, 'FechaVencimiento'] = fecha_vencimiento
            unidad = self.df_inventario.loc[idx, 'Unidad']
            mensaje = f"Entrada registrada: +{cantidad} {unidad}. Nuevo stock: {self.df_inventario.loc[idx, 'Cantidad']} {unidad}"
        else:
            if not fecha_vencimiento:
                fecha_vencimiento = (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')
            nuevo_reactivo = {
                'Reactivo': nombre_reactivo,
                'Cantidad': cantidad,
                'Unidad': unidad,
                'Estado': 'disponible',
                'FechaVencimiento': fecha_vencimiento,
                'FechaIngreso': datetime.now().strftime('%Y-%m-%d'),
                'Notas': notas
            }
            self.df_inventario = pd.concat([self.df_inventario, pd.DataFrame([nuevo_reactivo])], ignore_index=True)
            mensaje = f"Nuevo reactivo agregado: {cantidad} {unidad} de {nombre_reactivo}"
        
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
        self.df_log = pd.concat([self.df_log, pd.DataFrame([nuevo_movimiento])], ignore_index=True)
        
        self.guardar_inventario()
        self.guardar_log()
        return True, mensaje
    
    # ---------------------------
    # ALERTAS Y REPORTES
    # ---------------------------
    
    def verificar_vencimientos(self, dias_alerta=30):
        hoy = datetime.now()
        fecha_limite = hoy + timedelta(days=dias_alerta)
        self.df_inventario['FechaVencimiento'] = pd.to_datetime(self.df_inventario['FechaVencimiento'])
        vencidos = self.df_inventario[self.df_inventario['FechaVencimiento'] < hoy]
        proximos_vencer = self.df_inventario[(self.df_inventario['FechaVencimiento'] >= hoy) &
                                             (self.df_inventario['FechaVencimiento'] <= fecha_limite)]
        return {'vencidos': vencidos, 'proximos_vencer': proximos_vencer}
    
    def generar_reporte_stock(self):
        total_reactivos = len(self.df_inventario)
        disponibles = len(self.df_inventario[self.df_inventario['Estado'] == 'disponible'])
        en_uso = len(self.df_inventario[self.df_inventario['Estado'] == 'en uso'])
        vencimientos = self.verificar_vencimientos()
        return {
            'total': total_reactivos,
            'disponibles': disponibles,
            'en_uso': en_uso,
            'vencidos': len(vencimientos['vencidos']),
            'proximos_vencer': len(vencimientos['proximos_vencer']),
            'vencimientos': vencimientos
        }

# ============================================================================
# INICIALIZACIÓN DE SISTEMA EN SESSION_STATE
# ============================================================================

def inicializar_sistema():
    if 'sistema' not in st.session_state:
        st.session_state.sistema = SistemaInventarioReactivos()

# ============================================================================
# INTERFAZ STREAMLIT
# ============================================================================

def main():
    inicializar_sistema()
    sistema = st.session_state.sistema

    st.title("🧪 Sistema de Inventario de Reactivos Químicos (Sheets)")
    st.markdown("---")

    menu = st.sidebar.radio(
        "Navegación",
        ["📦 Inventario", "➕ Nueva Entrada", "➖ Registrar Salida", 
         "📋 Movimientos", "⚠️ Alertas", "📊 Reportes"]
    )

    # ---------------------------
    # Secciones del menú
    # ---------------------------

    if menu == "📦 Inventario":
        st.header("Inventario de Reactivos")
        busqueda = st.text_input("🔍 Buscar reactivo por nombre:", "")
        df_mostrar = sistema.buscar_reactivo(busqueda)
        if len(df_mostrar) > 0:
            def colorear_estado(val):
                if val == 'disponible': return 'background-color: #d5f4e6'
                elif val == 'en uso': return 'background-color: #fff3cd'
                elif val == 'agotado': return 'background-color: #fadbd8'
                return ''
            st.dataframe(df_mostrar.style.applymap(colorear_estado, subset=['Estado']), use_container_width=True, height=400)
        else:
            st.warning("No se encontraron reactivos.")

    elif menu == "➕ Nueva Entrada":
        st.header("Registrar Nueva Entrada")
        with st.form("form_entrada"):
            col1, col2 = st.columns(2)
            with col1:
                nombre = st.text_input("Nombre del Reactivo *")
                cantidad = st.number_input("Cantidad *", min_value=0.0, step=0.1)
                unidad = st.selectbox("Unidad", ["L", "kg", "g", "mL"])
                usuario = st.text_input("Usuario *")
            with col2:
                proyecto = st.text_input("Proyecto/Curso *")
                fecha_venc = st.date_input("Fecha de Vencimiento", value=datetime.now() + timedelta(days=365))
                notas = st.text_area("Notas", height=100)
            submitted = st.form_submit_button("✅ Registrar Entrada", use_container_width=True)
            if submitted:
                if not nombre or not usuario or not proyecto:
                    st.error("Complete todos los campos obligatorios (*)")
                elif cantidad <= 0:
                    st.error("La cantidad debe ser mayor a 0")
                else:
                    exito, mensaje = sistema.registrar_entrada(nombre, cantidad, usuario, proyecto,
                                                               unidad, fecha_venc.strftime('%Y-%m-%d'), notas)
                    if exito:
                        st.success(mensaje)
                        st.balloons()
                    else:
                        st.error(mensaje)

    elif menu == "➖ Registrar Salida":
        st.header("Registrar Salida de Reactivo")
        with st.form("form_salida"):
            col1, col2 = st.columns(2)
            with col1:
                nombres_reactivos = sistema.df_inventario['Reactivo'].tolist()
                nombre_sel = st.selectbox("Seleccione el Reactivo *", nombres_reactivos)
                if nombre_sel:
                    info = sistema.df_inventario[sistema.df_inventario['Reactivo'] == nombre_sel].iloc[0]
                    st.info(f"Stock disponible: {info['Cantidad']:.2f} {info['Unidad']}")
                cantidad = st.number_input("Cantidad a retirar *", min_value=0.0, step=0.1)
            with col2:
                usuario = st.text_input("Usuario que solicita *")
                proyecto = st.text_input("Proyecto/Curso *")
                notas = st.text_area("Notas", height=100)
            submitted = st.form_submit_button("✅ Registrar Salida", use_container_width=True)
            if submitted:
                if not usuario or not proyecto:
                    st.error("Complete todos los campos obligatorios (*)")
                elif cantidad <= 0:
                    st.error("La cantidad debe ser mayor a 0")
                else:
                    exito, mensaje = sistema.registrar_salida(nombre_sel, cantidad, usuario, proyecto, notas)
                    if exito:
                        st.success(mensaje)
                    else:
                        st.error(mensaje)

    elif menu == "📋 Movimientos":
        st.header("Historial de Movimientos")
        if len(sistema.df_log) > 0:
            df_movimientos = sistema.df_log.tail(100).iloc[::-1]
            def colorear_tipo(val):
                if val == 'ENTRADA': return 'background-color: #d5f4e6'
                elif val == 'SALIDA': return 'background-color: #fadbd8'
                return ''
            st.dataframe(df_movimientos.style.applymap(colorear_tipo, subset=['TipoMovimiento']), use_container_width=True, height=500)
        else:
            st.info("No hay movimientos registrados todavía")

    elif menu == "⚠️ Alertas":
        st.header("Alertas y Advertencias")
        vencimientos = sistema.verificar_vencimientos(dias_alerta=30)
        if len(vencimientos['vencidos']) > 0:
            st.error(f"🔴 REACTIVOS VENCIDOS: {len(vencimientos['vencidos'])}")
        if len(vencimientos['proximos_vencer']) > 0:
            st.warning(f"🟡 PRÓXIMOS A VENCER (30 días): {len(vencimientos['proximos_vencer'])}")
        bajo_stock = sistema.df_inventario[sistema.df_inventario['Cantidad'] < 1]
        if len(bajo_stock) > 0:
            st.warning(f"🟠 STOCK BAJO (< 1 unidad): {len(bajo_stock)}")

    elif menu == "📊 Reportes":
        st.header("Reportes del Sistema")
        if st.button("🔄 Generar Reporte", use_container_width=True):
            reporte = sistema.generar_reporte_stock()
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Reactivos", reporte['total'])
            col2.metric("Disponibles", reporte['disponibles'])
            col3.metric("En Uso", reporte['en_uso'])
            col4.metric("Vencidos", reporte['vencidos'], delta_color="inverse")

if __name__ == "__main__":
    main()
