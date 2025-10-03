import gspread
import pandas as pd
from datetime import datetime, timedelta
import streamlit as st
from google.oauth2.service_account import Credentials

# ============================================================================
# CONFIGURACIÓN INICIAL DE GOOGLE SHEETS
# ============================================================================

@st.cache_resource
def conectar_google_sheets():
    """Conexión mejorada a Google Sheets con manejo de errores"""
    try:
        # Obtener credenciales desde secrets
        credentials_dict = dict(st.secrets["GOOGLE_SERVICE_ACCOUNT"])
        
        # Definir los scopes necesarios
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        
        # Crear credenciales usando google-auth
        credentials = Credentials.from_service_account_info(
            credentials_dict,
            scopes=scopes
        )
        
        # Autenticar con gspread
        gc = gspread.authorize(credentials)
        
        # IDs de las hojas
        SHEET_ID = "1Z16IVvPiDIZ8UsNRSiAGX5eccW-ktoWXrZaxSRnGx4Y"
        
        # Acceder a las hojas
        sheet_inventario = gc.open_by_key(SHEET_ID).worksheet("Inventario")
        sheet_log = gc.open_by_key(SHEET_ID).worksheet("Log")
        
        return gc, sheet_inventario, sheet_log, None
        
    except Exception as e:
        return None, None, None, str(e)

# Intentar conexión
gc, sheet_inventario, sheet_log, error = conectar_google_sheets()

if error:
    st.error(f"❌ Error de conexión a Google Sheets: {error}")
    st.info("🔍 Pasos para solucionar:")
    st.markdown("""
    1. Verifica que tu archivo `.streamlit/secrets.toml` tenga el formato correcto
    2. Asegúrate de haber compartido la hoja con: `streamlitinventario@inventariostreamlit-474015.iam.gserviceaccount.com`
    3. Dale permisos de EDITOR a ese correo
    4. Verifica que el SHEET_ID sea correcto: `1Z16IVvPiDIZ8UsNRSiAGX5eccW-ktoWXrZaxSRnGx4Y`
    """)
    st.stop()
else:
    st.success("✅ Conectado exitosamente a Google Sheets")

# ============================================================================
# CONFIGURACIÓN DE STREAMLIT
# ============================================================================

st.set_page_config(
    page_title="Sistema de Inventario de Reactivos",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
            if inventario_data:
                self.df_inventario = pd.DataFrame(inventario_data)
            else:
                self.crear_inventario_inicial()
        except Exception as e:
            st.warning(f"Creando inventario inicial... ({e})")
            self.crear_inventario_inicial()
        
        try:
            log_data = sheet_log.get_all_records()
            if log_data:
                self.df_log = pd.DataFrame(log_data)
            else:
                self.crear_log_inicial()
        except Exception as e:
            st.warning(f"Creando log inicial... ({e})")
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
            # Convertir DataFrame a lista para Google Sheets
            data = [self.df_inventario.columns.tolist()] + self.df_inventario.values.tolist()
            sheet_inventario.clear()
            sheet_inventario.update(range_name='A1', values=data, value_input_option='RAW')
            return True
        except Exception as e:
            st.error(f"Error al guardar inventario en Sheets: {e}")
            return False
    
    def guardar_log(self):
        try:
            if len(self.df_log) > 0:
                data = [self.df_log.columns.tolist()] + self.df_log.values.tolist()
                sheet_log.clear()
                sheet_log.update(range_name='A1', values=data, value_input_option='RAW')
            return True
        except Exception as e:
            st.error(f"Error al guardar log en Sheets: {e}")
            return False
    
    # ---------------------------
    # BÚSQUEDA
    # ---------------------------
    
    def buscar_reactivo(self, termino_busqueda):
        if self.df_inventario is None or self.df_inventario.empty:
            return pd.DataFrame()
            
        if termino_busqueda.strip() == "":
            return self.df_inventario
            
        mascara = self.df_inventario['Reactivo'].str.contains(termino_busqueda, case=False, na=False)
        return self.df_inventario[mascara]
    
    # ---------------------------
    # REGISTRAR MOVIMIENTOS
    # ---------------------------
    
    def registrar_salida(self, nombre_reactivo, cantidad, usuario, proyecto_curso, notas=""):
        if self.df_inventario is None or self.df_inventario.empty:
            return False, "No hay inventario cargado"
            
        mascara = self.df_inventario['Reactivo'] == nombre_reactivo
        if not mascara.any():
            return False, f"Reactivo '{nombre_reactivo}' no encontrado"
        
        idx = self.df_inventario[mascara].index[0]
        cantidad_actual = float(self.df_inventario.loc[idx, 'Cantidad'])
        unidad = self.df_inventario.loc[idx, 'Unidad']
        
        if cantidad > cantidad_actual:
            return False, f"Stock insuficiente. Disponible: {cantidad_actual} {unidad}"
        
        self.df_inventario.loc[idx, 'Cantidad'] = cantidad_actual - cantidad
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
        
        # Actualizar log
        nuevo_df = pd.DataFrame([nuevo_movimiento])
        if self.df_log is None or self.df_log.empty:
            self.df_log = nuevo_df
        else:
            self.df_log = pd.concat([self.df_log, nuevo_df], ignore_index=True)
        
        self.guardar_inventario()
        self.guardar_log()
        return True, f"Salida registrada: {cantidad} {unidad} de {nombre_reactivo}"
    
    def registrar_entrada(self, nombre_reactivo, cantidad, usuario, proyecto_curso, 
                           unidad='L', fecha_vencimiento=None, notas=""):
        if self.df_inventario is None:
            self.df_inventario = pd.DataFrame()
            
        mascara = self.df_inventario['Reactivo'] == nombre_reactivo if not self.df_inventario.empty else pd.Series([], dtype=bool)
        
        if mascara.any():
            idx = self.df_inventario[mascara].index[0]
            cantidad_actual = float(self.df_inventario.loc[idx, 'Cantidad'])
            self.df_inventario.loc[idx, 'Cantidad'] = cantidad_actual + cantidad
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
            
            nuevo_df = pd.DataFrame([nuevo_reactivo])
            if self.df_inventario is None or self.df_inventario.empty:
                self.df_inventario = nuevo_df
            else:
                self.df_inventario = pd.concat([self.df_inventario, nuevo_df], ignore_index=True)
                
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
        
        # Actualizar log
        nuevo_log_df = pd.DataFrame([nuevo_movimiento])
        if self.df_log is None or self.df_log.empty:
            self.df_log = nuevo_log_df
        else:
            self.df_log = pd.concat([self.df_log, nuevo_log_df], ignore_index=True)
        
        self.guardar_inventario()
        self.guardar_log()
        return True, mensaje
    
    # ---------------------------
    # ALERTAS Y REPORTES
    # ---------------------------
    
    def verificar_vencimientos(self, dias_alerta=30):
        if self.df_inventario is None or self.df_inventario.empty:
            return {'vencidos': pd.DataFrame(), 'proximos_vencer': pd.DataFrame()}
            
        try:
            hoy = datetime.now()
            fecha_limite = hoy + timedelta(days=dias_alerta)
            self.df_inventario['FechaVencimiento'] = pd.to_datetime(self.df_inventario['FechaVencimiento'], errors='coerce')
            vencidos = self.df_inventario[self.df_inventario['FechaVencimiento'] < hoy]
            proximos_vencer = self.df_inventario[(self.df_inventario['FechaVencimiento'] >= hoy) &
                                                 (self.df_inventario['FechaVencimiento'] <= fecha_limite)]
            return {'vencidos': vencidos, 'proximos_vencer': proximos_vencer}
        except:
            return {'vencidos': pd.DataFrame(), 'proximos_vencer': pd.DataFrame()}
    
    def generar_reporte_stock(self):
        if self.df_inventario is None or self.df_inventario.empty:
            return {
                'total': 0, 'disponibles': 0, 'en_uso': 0, 
                'vencidos': 0, 'proximos_vencer': 0, 'vencimientos': {'vencidos': pd.DataFrame(), 'proximos_vencer': pd.DataFrame()}
            }
            
        total_reactivos = len(self.df_inventario)
        disponibles = len(self.df_inventario[self.df_inventario['Estado'] == 'disponible']) if 'Estado' in self.df_inventario.columns else 0
        en_uso = len(self.df_inventario[self.df_inventario['Estado'] == 'en uso']) if 'Estado' in self.df_inventario.columns else 0
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

    st.title("🧪 Sistema de Inventario de Reactivos Químicos")
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
        
        if sistema.df_inventario is not None and not sistema.df_inventario.empty:
            busqueda = st.text_input("🔍 Buscar reactivo por nombre:", "")
            df_mostrar = sistema.buscar_reactivo(busqueda)
            
            if len(df_mostrar) > 0:
                def colorear_estado(val):
                    if val == 'disponible': return 'background-color: #d5f4e6'
                    elif val == 'en uso': return 'background-color: #fff3cd'
                    elif val == 'agotado': return 'background-color: #fadbd8'
                    return ''
                
                st.dataframe(df_mostrar.style.applymap(colorear_estado, subset=['Estado']), 
                           use_container_width=True, height=400)
            else:
                st.warning("No se encontraron reactivos.")
        else:
            st.warning("No hay datos de inventario disponibles.")

    elif menu == "➕ Nueva Entrada":
        st.header("Registrar Nueva Entrada")
        with st.form("form_entrada"):
            col1, col2 = st.columns(2)
            with col1:
                nombre = st.text_input("Nombre del Reactivo *")
                cantidad = st.number_input("Cantidad *", min_value=0.0, step=0.1, format="%.2f")
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
                    exito, mensaje = sistema.registrar_entrada(
                        nombre, cantidad, usuario, proyecto, unidad, 
                        fecha_venc.strftime('%Y-%m-%d'), notas
                    )
                    if exito:
                        st.success(mensaje)
                        st.balloons()
                    else:
                        st.error(mensaje)

    elif menu == "➖ Registrar Salida":
        st.header("Registrar Salida de Reactivo")
        
        if sistema.df_inventario is not None and not sistema.df_inventario.empty:
            with st.form("form_salida"):
                col1, col2 = st.columns(2)
                with col1:
                    nombres_reactivos = sistema.df_inventario['Reactivo'].tolist()
                    nombre_sel = st.selectbox("Seleccione el Reactivo *", nombres_reactivos)
                    if nombre_sel:
                        info = sistema.df_inventario[sistema.df_inventario['Reactivo'] == nombre_sel].iloc[0]
                        st.info(f"Stock disponible: {info['Cantidad']:.2f} {info['Unidad']}")
                    cantidad = st.number_input("Cantidad a retirar *", min_value=0.0, step=0.1, format="%.2f")
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
        else:
            st.warning("No hay reactivos disponibles en el inventario.")

    elif menu == "📋 Movimientos":
        st.header("Historial de Movimientos")
        if sistema.df_log is not None and len(sistema.df_log) > 0:
            df_movimientos = sistema.df_log.tail(100).iloc[::-1]
            def colorear_tipo(val):
                if val == 'ENTRADA': return 'background-color: #d5f4e6'
                elif val == 'SALIDA': return 'background-color: #fadbd8'
                return ''
            st.dataframe(df_movimientos.style.applymap(colorear_tipo, subset=['TipoMovimiento']), 
                       use_container_width=True, height=500)
        else:
            st.info("No hay movimientos registrados todavía")

    elif menu == "⚠️ Alertas":
        st.header("Alertas y Advertencias")
        vencimientos = sistema.verificar_vencimientos(dias_alerta=30)
        
        if len(vencimientos['vencidos']) > 0:
            st.error(f"🔴 REACTIVOS VENCIDOS: {len(vencimientos['vencidos'])}")
            st.dataframe(vencimientos['vencidos'][['Reactivo', 'Cantidad', 'Unidad', 'FechaVencimiento']])
        
        if len(vencimientos['proximos_vencer']) > 0:
            st.warning(f"🟡 PRÓXIMOS A VENCER (30 días): {len(vencimientos['proximos_vencer'])}")
            st.dataframe(vencimientos['proximos_vencer'][['Reactivo', 'Cantidad', 'Unidad', 'FechaVencimiento']])
        
        if sistema.df_inventario is not None and not sistema.df_inventario.empty:
            bajo_stock = sistema.df_inventario[sistema.df_inventario['Cantidad'] < 1]
            if len(bajo_stock) > 0:
                st.warning(f"🟠 STOCK BAJO (< 1 unidad): {len(bajo_stock)}")
                st.dataframe(bajo_stock[['Reactivo', 'Cantidad', 'Unidad']])

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
