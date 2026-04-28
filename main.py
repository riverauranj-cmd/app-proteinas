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
    if not firebase_admin._apps:
        try:
            # Primero intentamos leer desde los Secrets de Streamlit (Modo Nube)
            if st.secrets:
                # Si pegaste el JSON directamente en Secrets, lo cargamos así:
                key_dict = dict(st.secrets)
                cred = credentials.Certificate(key_dict)
            else:
                # Modo local
                cred = credentials.Certificate("llave.json")
            
            firebase_admin.initialize_app(cred)
        except Exception as e:
            st.error(f"Error de conexión: {e}")
            return None
    return firestore.client()

db = init_firebase()

# --- FUNCIONES DE PERSISTENCIA ---

def guardar_inversion(categoria, descripcion, valor):
    if db:
        try:
            doc_ref = db.collection('Inversiones').document()
            doc_ref.set({
                'category': categoria,
                'description': descripcion,
                'totalValue': valor,
                'status': 'Paid',
                'createdAt': datetime.datetime.now()
            })
            return True
        except: return False
    return False

def guardar_venta(producto, cantidad, precio_unitario):
    if db:
        try:
            total = cantidad * precio_unitario
            doc_ref = db.collection('Ventas').document()
            doc_ref.set({
                'product': producto,
                'quantity': cantidad,
                'unitPrice': precio_unitario,
                'totalAmount': total,
                'date': datetime.datetime.now()
            })
            return True
        except: return False
    return False

def obtener_metricas():
    if not db:
        return 0.0, 0.0, 0.0
    
    try:
        # Leer Inversiones con protección si está vacío
        inv_docs = db.collection('Inversiones').get()
        total_inv = sum([doc.to_dict().get('totalValue', 0) for doc in inv_docs]) if inv_docs else 0.0
        
        # Leer Ventas con protección si está vacío
        ventas_docs = db.collection('Ventas').get()
        total_ventas = sum([doc.to_dict().get('totalAmount', 0) for doc in ventas_docs]) if ventas_docs else 0.0
        
        porcentaje_recuperacion = (total_ventas / total_inv * 100) if total_inv > 0 else 0.0
        return float(total_inv), float(total_ventas), float(porcentaje_recuperacion)
    except:
        return 0.0, 0.0, 0.0

# --- INTERFAZ DE USUARIO ---

st.title("🌱 EcoUrmet S.A.S - Food & Market")
st.markdown("### Control Financiero y Recuperación de Inversión")

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
                st.success("¡Inversión guardada!")
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
                st.success("¡Venta registrada!")
                st.rerun()
