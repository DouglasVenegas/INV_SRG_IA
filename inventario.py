"""
Sistema de Inventario de Reactivos Químicos - Versión Streamlit
================================================================
Aplicación web completa para gestionar inventario de reactivos en laboratorios

INSTALACIÓN DE DEPENDENCIAS:
pip install streamlit pandas openpyxl

EJECUCIÓN:
streamlit run app.py

Autor: Sistema de Gestión de Laboratorio
Versión: 2.0 (Streamlit)
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

# ============================================================================
# CONFIGURACIÓN GLOBAL
# ============================================================================

ARCHIVO_INVENTARIO = "inventario_reactivos.xlsx"
ARCHIVO_LOG = "log_movimientos.xlsx"

# Configuración de la página
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
    """Clase principal que gestiona el inventario de reactivos químicos"""
    
    def __init__(self):
        """Inicializa el sistema y carga/crea los archivos necesarios"""
        self.df_inventario = None
        self.df_log = None
        self.cargar_o_crear_archivos()
    
    def cargar_o_crear_archivos(self):
        """Carga los archivos Excel o los crea si no existen"""
        if os.path.exists(ARCHIVO_INVENTARIO):
            try:
                self.df_inventario = pd.read_excel(ARCHIVO_INVENTARIO)
            except Exception as e:
                st.error(f"Error al cargar inventario: {e}")
                self.crear_inventario_inicial()
        else:
            self.crear_inventario_inicial()
        
        if os.path.exists(ARCHIVO_LOG):
            try:
                self.df_log = pd.read_excel(ARCHIVO_LOG)
            except Exception as e:
                st.error(f"Error al cargar log: {e}")
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
    
    def crear_log_inicial(self):
        """Crea un archivo de log inicial vacío"""
        self.df_log = pd.DataFrame(columns=[
            'Fecha', 'Hora', 'TipoMovimiento', 'Reactivo', 
            'Cantidad', 'Unidad', 'Usuario', 'ProyectoCurso', 'Notas'
        ])
        self.guardar_log()
    
    def guardar_inventario(self):
        """Guarda el inventario en el archivo Excel"""
        try:
            self.df_inventario.to_excel(ARCHIVO_INVENTARIO, index=False)
            return True
        except Exception as e:
            st.error(f"Error al guardar inventario: {e}")
            return False
    
    def guardar_log(self):
        """Guarda el log de movimientos en el archivo Excel"""
        try:
            self.df_log.to_excel(ARCHIVO_LOG, index=False)
            return True
        except Exception as e:
            st.error(f"Error al guardar log: {e}")
            return False
    
    def buscar_reactivo(self, termino_busqueda):
        """Busca reactivos por nombre"""
        if termino_busqueda.strip() == "":
            return self.df_inventario
        
        mascara = self.df_inventario['Reactivo'].str.contains(
            termino_busqueda, case=False, na=False
        )
        return self.df_inventario[mascara]
    
    def registrar_salida(self, nombre_reactivo, cantidad, usuario, proyecto_curso, notas=""):
        """Registra una salida de reactivo del inventario"""
        mascara = self.df_inventario['Reactivo'] == nombre_reactivo
        
        if not mascara.any():
            return False, f"Reactivo '{nombre_reactivo}' no encontrado"
        
        idx = self.df_inventario[mascara].index[0]
        cantidad_actual = self.df_inventario.loc[idx, 'Cantidad']
        unidad = self.df_inventario.loc[idx, 'Unidad']
        
        if cantidad > cantidad_actual:
            return False, f"Stock insuficiente. Disponible: {cantidad_actual} {unidad}"
        
        nueva_cantidad = cantidad_actual - cantidad
        self.df_inventario.loc[idx, 'Cantidad'] = nueva_cantidad
        
        if nueva_cantidad == 0:
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
        
        self.df_log = pd.concat([self.df_log, pd.DataFrame([nuevo_movimiento])], 
                                ignore_index=True)
        
        self.guardar_inventario()
        self.guardar_log()
        
        return True, f"Salida registrada: {cantidad} {unidad} de {nombre_reactivo}"
    
    def registrar_entrada(self, nombre_reactivo, cantidad, usuario, proyecto_curso, 
                         unidad='L', fecha_vencimiento=None, notas=""):
        """Registra una entrada de reactivo al inventario"""
        mascara = self.df_inventario['Reactivo'] == nombre_reactivo
        
        if mascara.any():
            idx = self.df_inventario[mascara].index[0]
            cantidad_actual = self.df_inventario.loc[idx, 'Cantidad']
            nueva_cantidad = cantidad_actual + cantidad
            self.df_inventario.loc[idx, 'Cantidad'] = nueva_cantidad
            
            if self.df_inventario.loc[idx, 'Estado'] == 'agotado':
                self.df_inventario.loc[idx, 'Estado'] = 'disponible'
            
            if fecha_vencimiento:
                self.df_inventario.loc[idx, 'FechaVencimiento'] = fecha_vencimiento
            
            unidad = self.df_inventario.loc[idx, 'Unidad']
            mensaje = f"Entrada registrada: +{cantidad} {unidad}. Nuevo stock: {nueva_cantidad} {unidad}"
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
            
            self.df_inventario = pd.concat([self.df_inventario, 
                                           pd.DataFrame([nuevo_reactivo])], 
                                          ignore_index=True)
            
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
        
        self.df_log = pd.concat([self.df_log, pd.DataFrame([nuevo_movimiento])], 
                                ignore_index=True)
        
        self.guardar_inventario()
        self.guardar_log()
        
        return True, mensaje
    
    def verificar_vencimientos(self, dias_alerta=30):
        """Verifica reactivos vencidos o próximos a vencer"""
        hoy = datetime.now()
        fecha_limite = hoy + timedelta(days=dias_alerta)
        
        self.df_inventario['FechaVencimiento'] = pd.to_datetime(
            self.df_inventario['FechaVencimiento']
        )
        
        vencidos = self.df_inventario[
            self.df_inventario['FechaVencimiento'] < hoy
        ]
        
        proximos_vencer = self.df_inventario[
            (self.df_inventario['FechaVencimiento'] >= hoy) &
            (self.df_inventario['FechaVencimiento'] <= fecha_limite)
        ]
        
        return {
            'vencidos': vencidos,
            'proximos_vencer': proximos_vencer
        }
    
    def generar_reporte_stock(self):
        """Genera reporte completo del estado del inventario"""
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
# INICIALIZACIÓN DE LA APLICACIÓN
# ============================================================================

def inicializar_sistema():
    """Inicializa el sistema en session_state"""
    if 'sistema' not in st.session_state:
        st.session_state.sistema = SistemaInventarioReactivos()

# ============================================================================
# INTERFAZ DE USUARIO - STREAMLIT
# ============================================================================

def main():
    """Función principal de la aplicación Streamlit"""
    
    # Inicializar sistema
    inicializar_sistema()
    sistema = st.session_state.sistema
    
    # Encabezado
    st.title("🧪 Sistema de Inventario de Reactivos Químicos")
    st.markdown("---")
    
    # Menú lateral
    menu = st.sidebar.radio(
        "Navegación",
        ["📦 Inventario", "➕ Nueva Entrada", "➖ Registrar Salida", 
         "📋 Movimientos", "⚠️ Alertas", "📊 Reportes"]
    )
    
    # ========================================================================
    # SECCIÓN: INVENTARIO
    # ========================================================================
    
    if menu == "📦 Inventario":
        st.header("Inventario de Reactivos")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            busqueda = st.text_input("🔍 Buscar reactivo por nombre:", "")
        
        with col2:
            if st.button("🔄 Actualizar", use_container_width=True):
                st.rerun()
        
        # Mostrar tabla
        if busqueda:
            df_mostrar = sistema.buscar_reactivo(busqueda)
            if len(df_mostrar) == 0:
                st.warning(f"No se encontraron reactivos con '{busqueda}'")
        else:
            df_mostrar = sistema.df_inventario
        
        if len(df_mostrar) > 0:
            # Aplicar formato de colores
            def colorear_estado(val):
                if val == 'disponible':
                    return 'background-color: #d5f4e6'
                elif val == 'en uso':
                    return 'background-color: #fff3cd'
                elif val == 'agotado':
                    return 'background-color: #fadbd8'
                return ''
            
            st.dataframe(
                df_mostrar.style.applymap(colorear_estado, subset=['Estado']),
                use_container_width=True,
                height=400
            )
            
            st.info(f"Total de reactivos mostrados: {len(df_mostrar)}")
    
    # ========================================================================
    # SECCIÓN: NUEVA ENTRADA
    # ========================================================================
    
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
                fecha_venc = st.date_input(
                    "Fecha de Vencimiento",
                    value=datetime.now() + timedelta(days=365)
                )
                notas = st.text_area("Notas", height=100)
            
            submitted = st.form_submit_button("✅ Registrar Entrada", use_container_width=True)
            
            if submitted:
                if not nombre or not usuario or not proyecto:
                    st.error("Complete todos los campos obligatorios (*)")
                elif cantidad <= 0:
                    st.error("La cantidad debe ser mayor a 0")
                else:
                    exito, mensaje = sistema.registrar_entrada(
                        nombre, cantidad, usuario, proyecto,
                        unidad, fecha_venc.strftime('%Y-%m-%d'), notas
                    )
                    
                    if exito:
                        st.success(mensaje)
                        st.balloons()
                    else:
                        st.error(mensaje)
    
    # ========================================================================
    # SECCIÓN: REGISTRAR SALIDA
    # ========================================================================
    
    elif menu == "➖ Registrar Salida":
        st.header("Registrar Salida de Reactivo")
        
        with st.form("form_salida"):
            col1, col2 = st.columns(2)
            
            with col1:
                nombres_reactivos = sistema.df_inventario['Reactivo'].tolist()
                nombre_sel = st.selectbox("Seleccione el Reactivo *", nombres_reactivos)
                
                # Mostrar info del reactivo seleccionado
                if nombre_sel:
                    info = sistema.df_inventario[
                        sistema.df_inventario['Reactivo'] == nombre_sel
                    ].iloc[0]
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
                    exito, mensaje = sistema.registrar_salida(
                        nombre_sel, cantidad, usuario, proyecto, notas
                    )
                    
                    if exito:
                        st.success(mensaje)
                    else:
                        st.error(mensaje)
    
    # ========================================================================
    # SECCIÓN: MOVIMIENTOS
    # ========================================================================
    
    elif menu == "📋 Movimientos":
        st.header("Historial de Movimientos")
        
        if len(sistema.df_log) > 0:
            # Mostrar últimos 100 movimientos
            df_movimientos = sistema.df_log.tail(100).iloc[::-1]
            
            # Aplicar colores
            def colorear_tipo(val):
                if val == 'ENTRADA':
                    return 'background-color: #d5f4e6'
                elif val == 'SALIDA':
                    return 'background-color: #fadbd8'
                return ''
            
            st.dataframe(
                df_movimientos.style.applymap(colorear_tipo, subset=['TipoMovimiento']),
                use_container_width=True,
                height=500
            )
            
            st.info(f"Mostrando últimos {len(df_movimientos)} movimientos")
        else:
            st.info("No hay movimientos registrados todavía")
    
    # ========================================================================
    # SECCIÓN: ALERTAS
    # ========================================================================
    
    elif menu == "⚠️ Alertas":
        st.header("Alertas y Advertencias")
        
        vencimientos = sistema.verificar_vencimientos(dias_alerta=30)
        
        # Reactivos vencidos
        if len(vencimientos['vencidos']) > 0:
            st.error(f"🔴 REACTIVOS VENCIDOS: {len(vencimientos['vencidos'])}")
            for _, row in vencimientos['vencidos'].iterrows():
                dias_vencido = (datetime.now() - row['FechaVencimiento']).days
                with st.expander(f"⚠️ {row['Reactivo']} - Vencido hace {dias_vencido} días"):
                    st.write(f"**Stock:** {row['Cantidad']:.2f} {row['Unidad']}")
                    st.write(f"**Fecha de vencimiento:** {row['FechaVencimiento'].strftime('%Y-%m-%d')}")
                    st.write(f"**Notas:** {row['Notas']}")
        else:
            st.success("✅ No hay reactivos vencidos")
        
        st.markdown("---")
        
        # Próximos a vencer
        if len(vencimientos['proximos_vencer']) > 0:
            st.warning(f"🟡 PRÓXIMOS A VENCER (30 días): {len(vencimientos['proximos_vencer'])}")
            for _, row in vencimientos['proximos_vencer'].iterrows():
                dias_restantes = (row['FechaVencimiento'] - datetime.now()).days
                with st.expander(f"⏰ {row['Reactivo']} - Vence en {dias_restantes} días"):
                    st.write(f"**Stock:** {row['Cantidad']:.2f} {row['Unidad']}")
                    st.write(f"**Fecha de vencimiento:** {row['FechaVencimiento'].strftime('%Y-%m-%d')}")
                    st.write(f"**Notas:** {row['Notas']}")
        else:
            st.success("✅ No hay reactivos próximos a vencer")
        
        st.markdown("---")
        
        # Stock bajo
        bajo_stock = sistema.df_inventario[sistema.df_inventario['Cantidad'] < 1]
        if len(bajo_stock) > 0:
            st.warning(f"🟠 STOCK BAJO (< 1 unidad): {len(bajo_stock)}")
            for _, row in bajo_stock.iterrows():
                with st.expander(f"📉 {row['Reactivo']} - {row['Cantidad']:.2f} {row['Unidad']}"):
                    if row['Estado'] == 'agotado':
                        st.error("⚠️ AGOTADO - Necesita reposición urgente")
                    st.write(f"**Notas:** {row['Notas']}")
        else:
            st.success("✅ Todos los reactivos tienen stock adecuado")
    
    # ========================================================================
    # SECCIÓN: REPORTES
    # ========================================================================
    
    elif menu == "📊 Reportes":
        st.header("Reportes del Sistema")
        
        if st.button("🔄 Generar Reporte", use_container_width=True):
            reporte = sistema.generar_reporte_stock()
            
            # Métricas principales
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Reactivos", reporte['total'])
            with col2:
                st.metric("Disponibles", reporte['disponibles'])
            with col3:
                st.metric("En Uso", reporte['en_uso'])
            with col4:
                st.metric("Vencidos", reporte['vencidos'], delta_color="inverse")
            
            st.markdown("---")
            
            # Resumen detallado
            st.subheader("Resumen Detallado")
            
            resumen = f"""
**Fecha del reporte:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**RESUMEN GENERAL:**
- Total de reactivos: {reporte['total']}
- Disponibles: {reporte['disponibles']}
- En uso: {reporte['en_uso']}
- Vencidos: {reporte['vencidos']}
- Próximos a vencer (30 días): {reporte['proximos_vencer']}
            """
            
            st.text_area("Reporte", resumen, height=200)
            
            # Botón de descarga
            st.download_button(
                label="💾 Descargar Reporte",
                data=resumen,
                file_name=f"reporte_inventario_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.info(
        "**Sistema de Inventario v2.0**\n\n"
        f"Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

# ============================================================================
# PUNTO DE ENTRADA
# ============================================================================

if __name__ == "__main__":
    main()