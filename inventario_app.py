import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
from supabase import create_client, Client

st.set_page_config(
    page_title="Sistema de Inventario de Reactivos",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CONEXIÓN A SUPABASE
# ============================================================================

@st.cache_resource
def init_supabase() -> Client:
    """Inicializa conexión con Supabase"""
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"Error conectando a Supabase: {e}")
        st.stop()

supabase = init_supabase()

# ============================================================================
# CLASE PRINCIPAL DEL SISTEMA
# ============================================================================

class SistemaInventarioReactivos:
    """Gestión de inventario de reactivos químicos con Supabase"""
    
    def __init__(self):
        self.df_inventario = None
        self.df_log = None
        self.cargar_datos()
    
    def cargar_datos(self):
        """Carga datos desde Supabase"""
        try:
            # Cargar inventario
            response = supabase.table('inventario').select("*").execute()
            if response.data:
                self.df_inventario = pd.DataFrame(response.data)
            else:
                st.info("No hay datos en inventario. Creando ejemplos iniciales...")
                self.crear_inventario_inicial()
            
            # Cargar log
            response = supabase.table('log_movimientos').select("*").order('id', desc=True).limit(1000).execute()
            if response.data:
                self.df_log = pd.DataFrame(response.data)
            else:
                self.df_log = pd.DataFrame()
                
        except Exception as e:
            st.error(f"Error cargando datos: {e}")
            self.df_inventario = pd.DataFrame()
            self.df_log = pd.DataFrame()
    
    def crear_inventario_inicial(self):
        """Crea datos de ejemplo iniciales"""
        datos_ejemplo = [
            {
                'reactivo': 'Ácido Sulfúrico 98%',
                'cantidad': 2.5,
                'unidad': 'L',
                'estado': 'disponible',
                'fecha_vencimiento': '2026-12-31',
                'fecha_ingreso': '2024-01-15',
                'notas': 'Manipular con precaución - Corrosivo'
            },
            {
                'reactivo': 'Hidróxido de Sodio',
                'cantidad': 5.0,
                'unidad': 'kg',
                'estado': 'disponible',
                'fecha_vencimiento': '2027-06-30',
                'fecha_ingreso': '2024-02-20',
                'notas': 'Almacenar en lugar seco'
            },
            {
                'reactivo': 'Etanol 96%',
                'cantidad': 10.0,
                'unidad': 'L',
                'estado': 'disponible',
                'fecha_vencimiento': '2025-11-15',
                'fecha_ingreso': '2024-03-10',
                'notas': 'Inflamable - Mantener alejado del fuego'
            },
            {
                'reactivo': 'Cloruro de Sodio',
                'cantidad': 15.0,
                'unidad': 'kg',
                'estado': 'disponible',
                'fecha_vencimiento': '2028-01-31',
                'fecha_ingreso': '2024-01-05',
                'notas': 'Grado analítico'
            },
            {
                'reactivo': 'Acetona',
                'cantidad': 8.0,
                'unidad': 'L',
                'estado': 'disponible',
                'fecha_vencimiento': '2025-10-20',
                'fecha_ingreso': '2024-04-12',
                'notas': 'Inflamable - Buena ventilación'
            }
        ]
        
        try:
            supabase.table('inventario').insert(datos_ejemplo).execute()
            self.cargar_datos()
            st.success("✅ Inventario inicial creado")
        except Exception as e:
            st.error(f"Error creando inventario inicial: {e}")
    
    def buscar_reactivo(self, termino_busqueda):
        """Busca reactivos por nombre"""
        if self.df_inventario is None or self.df_inventario.empty:
            return pd.DataFrame()
        
        if termino_busqueda.strip() == "":
            return self.df_inventario
        
        mascara = self.df_inventario['reactivo'].str.contains(termino_busqueda, case=False, na=False)
        return self.df_inventario[mascara]
    
    def registrar_salida(self, reactivo_id, cantidad, usuario, proyecto_curso, notas=""):
        """Registra una salida de reactivo"""
        try:
            # Obtener reactivo actual
            response = supabase.table('inventario').select("*").eq('id', reactivo_id).single().execute()
            reactivo = response.data
            
            cantidad_actual = float(reactivo['cantidad'])
            
            if cantidad > cantidad_actual:
                return False, f"Stock insuficiente. Disponible: {cantidad_actual} {reactivo['unidad']}"
            
            # Actualizar cantidad
            nueva_cantidad = cantidad_actual - cantidad
            nuevo_estado = 'agotado' if nueva_cantidad == 0 else reactivo['estado']
            
            supabase.table('inventario').update({
                'cantidad': nueva_cantidad,
                'estado': nuevo_estado,
                'updated_at': datetime.now().isoformat()
            }).eq('id', reactivo_id).execute()
            
            # Registrar en log
            ahora = datetime.now()
            supabase.table('log_movimientos').insert({
                'fecha': ahora.strftime('%Y-%m-%d'),
                'hora': ahora.strftime('%H:%M:%S'),
                'tipo_movimiento': 'SALIDA',
                'reactivo': reactivo['reactivo'],
                'cantidad': cantidad,
                'unidad': reactivo['unidad'],
                'usuario': usuario,
                'proyecto_curso': proyecto_curso,
                'notas': notas
            }).execute()
            
            # Recargar datos
            self.cargar_datos()
            
            return True, f"Salida registrada: {cantidad} {reactivo['unidad']} de {reactivo['reactivo']}"
            
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def registrar_entrada(self, nombre_reactivo, cantidad, usuario, proyecto_curso, 
                          unidad='L', fecha_vencimiento=None, notas=""):
        """Registra una entrada de reactivo"""
        try:
            # Buscar si el reactivo ya existe
            response = supabase.table('inventario').select("*").ilike('reactivo', nombre_reactivo).execute()
            
            if response.data and len(response.data) > 0:
                # Reactivo existe, actualizar cantidad
                reactivo = response.data[0]
                nueva_cantidad = float(reactivo['cantidad']) + cantidad
                nuevo_estado = 'disponible' if reactivo['estado'] == 'agotado' else reactivo['estado']
                
                update_data = {
                    'cantidad': nueva_cantidad,
                    'estado': nuevo_estado,
                    'updated_at': datetime.now().isoformat()
                }
                
                if fecha_vencimiento:
                    update_data['fecha_vencimiento'] = fecha_vencimiento
                
                supabase.table('inventario').update(update_data).eq('id', reactivo['id']).execute()
                
                mensaje = f"Entrada registrada: +{cantidad} {reactivo['unidad']}. Nuevo stock: {nueva_cantidad} {reactivo['unidad']}"
                unidad_usada = reactivo['unidad']
            else:
                # Reactivo nuevo
                if not fecha_vencimiento:
                    fecha_vencimiento = (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')
                
                supabase.table('inventario').insert({
                    'reactivo': nombre_reactivo,
                    'cantidad': cantidad,
                    'unidad': unidad,
                    'estado': 'disponible',
                    'fecha_vencimiento': fecha_vencimiento,
                    'fecha_ingreso': datetime.now().strftime('%Y-%m-%d'),
                    'notas': notas
                }).execute()
                
                mensaje = f"Nuevo reactivo agregado: {cantidad} {unidad} de {nombre_reactivo}"
                unidad_usada = unidad
            
            # Registrar en log
            ahora = datetime.now()
            supabase.table('log_movimientos').insert({
                'fecha': ahora.strftime('%Y-%m-%d'),
                'hora': ahora.strftime('%H:%M:%S'),
                'tipo_movimiento': 'ENTRADA',
                'reactivo': nombre_reactivo,
                'cantidad': cantidad,
                'unidad': unidad_usada,
                'usuario': usuario,
                'proyecto_curso': proyecto_curso,
                'notas': notas
            }).execute()
            
            # Recargar datos
            self.cargar_datos()
            
            return True, mensaje
            
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def verificar_vencimientos(self, dias_alerta=30):
        """Verifica reactivos vencidos y próximos a vencer"""
        if self.df_inventario is None or self.df_inventario.empty:
            return {'vencidos': pd.DataFrame(), 'proximos_vencer': pd.DataFrame()}
        
        try:
            hoy = datetime.now()
            fecha_limite = hoy + timedelta(days=dias_alerta)
            
            self.df_inventario['fecha_vencimiento'] = pd.to_datetime(
                self.df_inventario['fecha_vencimiento'], 
                errors='coerce'
            )
            
            vencidos = self.df_inventario[self.df_inventario['fecha_vencimiento'] < hoy]
            proximos_vencer = self.df_inventario[
                (self.df_inventario['fecha_vencimiento'] >= hoy) &
                (self.df_inventario['fecha_vencimiento'] <= fecha_limite)
            ]
            
            return {'vencidos': vencidos, 'proximos_vencer': proximos_vencer}
        except:
            return {'vencidos': pd.DataFrame(), 'proximos_vencer': pd.DataFrame()}
    
    def generar_reporte_stock(self):
        """Genera reporte del estado del inventario"""
        if self.df_inventario is None or self.df_inventario.empty:
            return {
                'total': 0, 'disponibles': 0, 'en_uso': 0, 
                'vencidos': 0, 'proximos_vencer': 0,
                'vencimientos': {'vencidos': pd.DataFrame(), 'proximos_vencer': pd.DataFrame()}
            }
        
        total_reactivos = len(self.df_inventario)
        disponibles = len(self.df_inventario[self.df_inventario['estado'] == 'disponible'])
        en_uso = len(self.df_inventario[self.df_inventario['estado'] == 'en uso'])
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
# INTERFAZ STREAMLIT
# ============================================================================

def inicializar_sistema():
    if 'sistema' not in st.session_state:
        st.session_state.sistema = SistemaInventarioReactivos()

def main():
    inicializar_sistema()
    sistema = st.session_state.sistema

    st.title("🧪 Sistema de Inventario de Reactivos Químicos")
    st.success("✅ Conectado a Supabase - Guardado automático")
    st.markdown("---")

    menu = st.sidebar.radio(
        "Navegación",
        ["📦 Inventario", "➕ Nueva Entrada", "➖ Registrar Salida", 
         "📋 Movimientos", "⚠️ Alertas", "📊 Reportes"]
    )

    if menu == "📦 Inventario":
        st.header("Inventario de Reactivos")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            busqueda = st.text_input("🔍 Buscar reactivo por nombre:", "")
        with col2:
            if st.button("🔄 Recargar", use_container_width=True):
                sistema.cargar_datos()
                st.rerun()
        
        if sistema.df_inventario is not None and not sistema.df_inventario.empty:
            df_mostrar = sistema.buscar_reactivo(busqueda)
            
            if len(df_mostrar) > 0:
                # Renombrar columnas para mostrar
                df_display = df_mostrar.copy()
                df_display = df_display.rename(columns={
                    'reactivo': 'Reactivo',
                    'cantidad': 'Cantidad',
                    'unidad': 'Unidad',
                    'estado': 'Estado',
                    'fecha_vencimiento': 'Fecha Vencimiento',
                    'fecha_ingreso': 'Fecha Ingreso',
                    'notas': 'Notas'
                })
                
                def colorear_estado(val):
                    if val == 'disponible': return 'background-color: #d5f4e6'
                    elif val == 'en uso': return 'background-color: #fff3cd'
                    elif val == 'agotado': return 'background-color: #fadbd8'
                    return ''
                
                columnas_mostrar = ['Reactivo', 'Cantidad', 'Unidad', 'Estado', 
                                   'Fecha Vencimiento', 'Fecha Ingreso', 'Notas']
                
                st.dataframe(
                    df_display[columnas_mostrar].style.applymap(colorear_estado, subset=['Estado']), 
                    use_container_width=True, 
                    height=400
                )
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
                fecha_venc = st.date_input("Fecha de Vencimiento", 
                                          value=datetime.now() + timedelta(days=365))
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
                        st.rerun()
                    else:
                        st.error(mensaje)

    elif menu == "➖ Registrar Salida":
        st.header("Registrar Salida de Reactivo")
        
        if sistema.df_inventario is not None and not sistema.df_inventario.empty:
            with st.form("form_salida"):
                col1, col2 = st.columns(2)
                with col1:
                    # Crear diccionario de reactivos con ID
                    reactivos_dict = {
                        f"{row['reactivo']} ({row['cantidad']:.2f} {row['unidad']})": row['id']
                        for _, row in sistema.df_inventario.iterrows()
                    }
                    
                    nombre_sel = st.selectbox("Seleccione el Reactivo *", list(reactivos_dict.keys()))
                    reactivo_id = reactivos_dict[nombre_sel]
                    
                    if nombre_sel:
                        info = sistema.df_inventario[sistema.df_inventario['id'] == reactivo_id].iloc[0]
                        st.info(f"Stock disponible: {info['cantidad']:.2f} {info['unidad']}")
                    
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
                        exito, mensaje = sistema.registrar_salida(
                            reactivo_id, cantidad, usuario, proyecto, notas
                        )
                        if exito:
                            st.success(mensaje)
                            st.rerun()
                        else:
                            st.error(mensaje)
        else:
            st.warning("No hay reactivos disponibles en el inventario.")

    elif menu == "📋 Movimientos":
        st.header("Historial de Movimientos")
        if sistema.df_log is not None and len(sistema.df_log) > 0:
            df_movimientos = sistema.df_log.copy()
            
            # Renombrar columnas
            df_movimientos = df_movimientos.rename(columns={
                'fecha': 'Fecha',
                'hora': 'Hora',
                'tipo_movimiento': 'Tipo',
                'reactivo': 'Reactivo',
                'cantidad': 'Cantidad',
                'unidad': 'Unidad',
                'usuario': 'Usuario',
                'proyecto_curso': 'Proyecto/Curso',
                'notas': 'Notas'
            })
            
            def colorear_tipo(val):
                if val == 'ENTRADA': return 'background-color: #d5f4e6'
                elif val == 'SALIDA': return 'background-color: #fadbd8'
                return ''
            
            columnas_mostrar = ['Fecha', 'Hora', 'Tipo', 'Reactivo', 'Cantidad', 
                               'Unidad', 'Usuario', 'Proyecto/Curso', 'Notas']
            
            st.dataframe(
                df_movimientos[columnas_mostrar].head(100).style.applymap(
                    colorear_tipo, subset=['Tipo']
                ), 
                use_container_width=True, 
                height=500
            )
        else:
            st.info("No hay movimientos registrados todavía")

    elif menu == "⚠️ Alertas":
        st.header("Alertas y Advertencias")
        vencimientos = sistema.verificar_vencimientos(dias_alerta=30)
        
        if len(vencimientos['vencidos']) > 0:
            st.error(f"🔴 REACTIVOS VENCIDOS: {len(vencimientos['vencidos'])}")
            df_vencidos = vencimientos['vencidos'][['reactivo', 'cantidad', 'unidad', 'fecha_vencimiento']].rename(columns={
                'reactivo': 'Reactivo',
                'cantidad': 'Cantidad',
                'unidad': 'Unidad',
                'fecha_vencimiento': 'Fecha Vencimiento'
            })
            st.dataframe(df_vencidos, use_container_width=True)
        
        if len(vencimientos['proximos_vencer']) > 0:
            st.warning(f"🟡 PRÓXIMOS A VENCER (30 días): {len(vencimientos['proximos_vencer'])}")
            df_proximos = vencimientos['proximos_vencer'][['reactivo', 'cantidad', 'unidad', 'fecha_vencimiento']].rename(columns={
                'reactivo': 'Reactivo',
                'cantidad': 'Cantidad',
                'unidad': 'Unidad',
                'fecha_vencimiento': 'Fecha Vencimiento'
            })
            st.dataframe(df_proximos, use_container_width=True)
        
        if sistema.df_inventario is not None and not sistema.df_inventario.empty:
            bajo_stock = sistema.df_inventario[sistema.df_inventario['cantidad'] < 1]
            if len(bajo_stock) > 0:
                st.warning(f"🟠 STOCK BAJO (< 1 unidad): {len(bajo_stock)}")
                df_bajo = bajo_stock[['reactivo', 'cantidad', 'unidad']].rename(columns={
                    'reactivo': 'Reactivo',
                    'cantidad': 'Cantidad',
                    'unidad': 'Unidad'
                })
                st.dataframe(df_bajo, use_container_width=True)
        
        if (len(vencimientos['vencidos']) == 0 and 
            len(vencimientos['proximos_vencer']) == 0 and 
            (sistema.df_inventario is None or len(sistema.df_inventario[sistema.df_inventario['cantidad'] < 1]) == 0)):
            st.success("✅ No hay alertas en este momento")

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