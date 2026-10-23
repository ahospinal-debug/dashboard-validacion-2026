import streamlit as st
import pandas as pd
import plotly.express as px

# CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(
    page_title="Dashboard Seguimiento Validación 2026",
    page_icon="📊",
    layout="wide"
)

# ESTILOS CSS PERSONALIZADOS PARA TARJETAS TIPO SEMÁFORO Y TARJETAS PROFESIONALES
st.markdown("""
    <style>
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border-left: 5px solid #2ecc71;
        margin-bottom: 10px;
    }
    .metric-title {
        font-size: 14px;
        color: #6c757d;
        font-weight: 600;
    }
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        color: #2c3e50;
    }
    </style>
""", unsafe_allow_html=True)

# TÍTULO PRINCIPAL
st.title("📊 Dashboard de Seguimiento de Validación 2026")

# BARRA LATERAL (SIDEBAR)
st.sidebar.header("⚙️ Configuración y Filtros")

# Carga automática del archivo subido a GitHub
df = pd.read_excel("Seguimiento Validación 2026 (1).xlsx")

# --- IDENTIFICACIÓN EXACTA O POR LETRA DE COLUMNA ---
def get_col(letters, keywords):
    for kw in keywords:
        for col in df.columns:
            if kw.lower() in str(col).lower():
                return col
    for letter in letters:
        idx = sum((ord(c.upper()) - 64) * (26 ** i) for i, c in enumerate(reversed(letter))) - 1
        if 0 <= idx < len(df.columns):
            return df.columns[idx]
    return None

# Mapeo de columnas
col_validador = get_col(["O"], ["VALIDADOR", "VALIADORA"])
col_disenador = get_col(["AB"], ["DISEÑADOR INSTRUCCIONAL", "DISEÑADOR", "DISENADOR"])
col_obs = get_col(["AJ"], ["NIVEL DE OBSERVACIÓN", "NIVEL DE OBSERVACION", "OBSERVACIÓN"])
col_estado = get_col([], ["ESTADO DE LA VALIDACIÓN", "ESTADO VALIDACION", "ESTADO DE VALIDACION"])
col_carrera = get_col([], ["EAP", "CARRERA", "PROGRAMA"])

# Validar columna clave
if not col_estado:
    st.error("No se encontró la columna 'ESTADO DE LA VALIDACIÓN' en el archivo Excel.")
    st.stop()

# --- FILTROS EN SIDEBAR ---
eap_list = ["Todas"] + sorted([str(x) for x in df[col_carrera].dropna().unique()]) if col_carrera else ["Todas"]
selected_eap = st.sidebar.selectbox("Filtrar por EAP / Carrera:", eap_list)

val_list = ["Todos"] + sorted([str(x) for x in df[col_validador].dropna().unique()]) if col_validador else ["Todos"]
selected_val = st.sidebar.selectbox("Validador (Col. O):", val_list)

dis_list = ["Todos"] + sorted([str(x) for x in df[col_disenador].dropna().unique()]) if col_disenador else ["Todos"]
selected_dis = st.sidebar.selectbox("Diseñador Instruccional (Col. AB):", dis_list)

# APLICAR FILTROS
df_filtered = df.copy()

if col_carrera and selected_eap != "Todas":
    df_filtered = df_filtered[df_filtered[col_carrera].astype(str) == selected_eap]

if col_validador and selected_val != "Todos":
    df_filtered = df_filtered[df_filtered[col_validador].astype(str) == selected_val]

if col_disenador and selected_dis != "Todos":
    df_filtered = df_filtered[df_filtered[col_disenador].astype(str) == selected_dis]

# --- SEMÁFORO DE AVANCE DE VALIDACIÓN (TARJETAS KPI PROFESIONALES) ---
st.subheader("🚦 Semáforo de Avance de Validación")

total_asignaturas = len(df_filtered)
completadas = len(df_filtered[df_filtered[col_estado].astype(str).str.contains("Pasa|Aprobad|Completa", case=False, na=False)])
observadas = len(df_filtered[df_filtered[col_estado].astype(str).str.contains("Observad", case=False, na=False)])
pendientes = total_asignaturas - (completadas + observadas)

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.markdown('<div class="metric-card" style="border-left-color: #3498db;"><div class="metric-title">Total Asignaturas</div><div class="metric-value">{}</div></div>'.format(total_asignaturas), unsafe_allow_html=True)
with m2:
    st.markdown('<div class="metric-card" style="border-left-color: #2ecc71;"><div class="metric-title">🟢 Pasa a Implementación</div><div class="metric-value">{}</div></div>'.format(completadas), unsafe_allow_html=True)
with m3:
    st.markdown('<div class="metric-card" style="border-left-color: #f1c40f;"><div class="metric-title">🟡 Observadas</div><div class="metric-value">{}</div></div>'.format(observadas), unsafe_allow_html=True)
with m4:
    st.markdown('<div class="metric-card" style="border-left-color: #e74c3c;"><div class="metric-title">🔴 Sin Registro / No iniciada</div><div class="metric-value">{}</div></div>'.format(pendientes), unsafe_allow_html=True)

st.markdown("---")

# --- VISUALIZACIONES PRINCIPALES (PALETA VERDE Y DISEÑO PROFESIONAL) ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("📌 Distribución por Estado de Validación")
    estado_counts = df_filtered[col_estado].value_counts().reset_index()
    estado_counts.columns = ['Estado', 'Cantidad']
    
    # Colores verdes / profesionales
    colors_map = {
        "Pasa a implementación": "#2ecc71",
        "Observada": "#e74c3c",
        "Sin registro / No iniciada": "#95a5a6"
    }
    
    fig_estado = px.bar(
        estado_counts, 
        x='Estado', 
        y='Cantidad', 
        text='Cantidad',
        labels={'Estado': '', 'Cantidad': 'N° Asignaturas'},
        color='Estado',
        color_discrete_map=colors_map
    )
    fig_estado.update_traces(textposition='outside')
    fig_estado.update_layout(
        showlegend=False, 
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=30, b=20)
    )
    st.plotly_chart(fig_estado, use_container_width=True)

with col2:
    st.subheader("⚠️ Proporción de Asignaturas Observadas")
    if col_obs:
        obs_counts = df_filtered[col_obs].fillna("Sin Registro").value_counts().reset_index()
        obs_counts.columns = ['Observación', 'Cantidad']
        
        fig_obs = px.pie(
            obs_counts, 
            values='Cantidad', 
            names='Observación', 
            hole=0.4,
            color_discrete_sequence=["#2ecc71", "#e74c3c", "#f39c12", "#3498db"]
        )
        fig_obs.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=20, r=20, t=30, b=20)
        )
        st.plotly_chart(fig_obs, use_container_width=True)
    else:
        st.info("Columna de Observaciones no detectada.")

st.markdown("---")

# --- TABLA DE DETALLE COMPLETA CON SEMÁFORO INCORPORADO ---
st.subheader("📋 Detalle de Asignaturas")

# Crear una columna visual con semáforo/badge para la tabla de datos
def generar_badge_estado(val):
    val_str = str(val).lower()
    if "pasa" in val_str or "aprobad" in val_str or "completa" in val_str:
        return "🟢 Pasa a implementación"
    elif "observad" in val_str:
        return "🟡 Observada"
    else:
        return "🔴 Sin registro / No iniciada"

# Insertar la columna de Semáforo visual al inicio
df_display = df_filtered.copy()
df_display.insert(0, "Semáforo Estado", df_display[col_estado].apply(generar_badge_estado))

# Desplegar la tabla completa con todas las columnas del Excel
st.dataframe(
    df_display,
    use_container_width=True,
    hide_index=True
)
