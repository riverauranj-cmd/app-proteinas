import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import datetime
import json

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="EcoUrmet S.A.S - Control Financiero", layout="wide")

# --- CONEXIÓN A FIREBASE ---
@st.cache_resource
def init_firebase():
    # Intentamos conectar usando secretos (para la nube) o el archivo local llave.json
    if not firebase_admin._apps:
        try:
            # Opción 1: Buscar archivo local llave.json
            if "firebase" in st.secrets:
                # Si estás en Streamlit Cloud, usa st.secrets
                key_dict = json.loads(st.secrets["firebase"]["key"])
                cred = credentials.Certificate(key_dict)
            else:
                # Si estás en local, usa el archivo que mencionaste
                cred = credentials.Certificate("llave.json")
            
            firebase_admin.initialize_app(cred)
        except Exception as e:
            st.error(f"Error de conexión: {e}")
            return None
    return firestore.client()

db = init_firebase()

# --- FUNCIONES DE PERSISTENCIA (EL "MOTOR") ---

def guardar_inversion(categoria, descripcion, valor):
    if db:
        doc_ref = db.collection('Inversiones').document()
        doc_ref.set({
            'category': categoria,
            'description': descripcion,
            'totalValue': valor,
            'status': 'Paid', # Por defecto
            'createdAt': datetime.datetime.now(),
            'userId': 'admin_user' # O el ID del usuario si tienes auth
        })
        return True
    return False

def guardar_venta(producto, cantidad, precio_unitario):
    if db:
        total = cantidad * precio_unitario
        doc_ref = db.collection('Ventas').document()
        doc_ref.set({
            'product': producto,
            'quantity': cantidad,
            'unitPrice': precio_unitario,
            'totalAmount': total,
            'date': datetime.datetime.now(),
            'userId': 'admin_user'
        })
        return True
    return False

# --- LÓGICA DEL DASHBOARD (RECUPERACIÓN) ---

def obtener_metricas():
    if not db:
        return 0, 0, 0
    
    # Leer Inversiones
    inv_docs = db.collection('Inversiones').stream()
    total_inv = sum([doc.to_dict().get('totalValue', 0) for doc in inv_docs])
    
    # Leer Ventas
    ventas_docs = db.collection('Ventas').stream()
    total_ventas = sum([doc.to_dict().get('totalAmount', 0) for doc in ventas_docs])
    
    porcentaje_recuperacion = (total_ventas / total_inv * 100) if total_inv > 0 else 0
    return total_inv, total_ventas, porcentaje_recuperacion

# --- INTERFAZ DE USUARIO (STREAMLIT) ---

st.title("🌱 EcoUrmet S.A.S - Food & Market")
st.markdown("### Control Financiero y Recuperación de Inversión")

# Tabs para organizar la app
tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "💰 Inversiones", "🛒 Ventas"])

with tab1:
    st.header("Resumen General")
    t_inv, t_ven, p_rec = obtener_metricas()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Inversión Total", f"${t_inv:,.2f}")
    col2.metric("Ventas Totales", f"${t_ven:,.2f}")
    col3.metric("Recuperación", f"{p_rec:.2f}%")
    
    st.progress(min(p_rec/100, 1.0))
    st.write(f"Falta por recuperar: ${max(0, t_inv - t_ven):,.2f}")

with tab2:
    st.header("Registro de Gastos")
    with st.form("form_inversion"):
        cat = st.selectbox("Categoría", ["Equipos", "Materia Prima", "Marketing", "Local", "Otros"])
        desc = st.text_input("Descripción")
        val = st.number_input("Valor", min_value=0.0)
        btn_inv = st.form_submit_button("Guardar Inversión")
        
        if btn_inv:
            if guardar_inversion(cat, desc, val):
                st.success("Inversión guardada en Firebase (Colección: Inversiones)")
                st.rerun()

with tab3:
    st.header("Registro de Ventas")
    with st.form("form_ventas"):
        prod = st.text_input("Producto/Servicio")
        cant = st.number_input("Cantidad", min_value=1)
        prec = st.number_input("Precio Unitario", min_value=0.0)
        btn_ven = st.form_submit_button("Registrar Venta")
        
        if btn_ven:
            if guardar_venta(prod, cant, prec):
                st.success("Venta registrada en Firebase (Colección: Ventas)")
                st.rerun()

# --- NOTA PARA LA NUBE (Streamlit Cloud) ---
# En Streamlit Cloud, ve a Settings -> Secrets y pega lo siguiente:
# [firebase]
# key = '''{ "type": "service_account", ... pega aquí todo el contenido de llave.json ... }'''
