import streamlit as st
import pandas as pd
import plotly.express as px

# CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(
    page_title="Dashboard Seguimiento Validación 2026",
    page_icon="📊",
    layout="wide"
)

# TÍTULO PRINCIPAL
st.title("📊 Dashboard de Seguimiento de Validación 2026")

# BARRA LATERAL (SIDEBAR)
st.sidebar.header("⚙️ Configuración y Filtros")
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

# Mapeo según especificaciones
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

# --- SEMÁFORO / INDICADORES (METRICS) ---
st.markdown("### 🚦 Semáforo de Avance de Validación")

total_asignaturas = len(df_filtered)
completadas = len(df_filtered[df_filtered[col_estado].astype(str).str.contains("Pasa|Aprobad|Completa", case=False, na=False)])
observadas = len(df_filtered[df_filtered[col_estado].astype(str).str.contains("Observad", case=False, na=False)])
pendientes = total_asignaturas - (completadas + observadas)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Asignaturas", total_asignaturas)
m2.metric("🟢 Pasa a Implementación", completadas)
m3.metric("🟡 Observadas", observadas)
m4.metric("🔴 Sin Registro / No iniciada", pendientes)

st.markdown("---")

# --- VISUALIZACIONES ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("📌 Distribución por Estado de Validación")
    estado_counts = df_filtered[col_estado].value_counts().reset_index()
    estado_counts.columns = ['Estado', 'Cantidad']
    
    fig_estado = px.bar(
        estado_counts, 
        x='Estado', 
        y='Cantidad', 
        text='Cantidad',
        labels={'Estado': '', 'Cantidad': 'N° Asignaturas'},
        color='Estado'
    )
    fig_estado.update_traces(textposition='outside')
    fig_estado.update_layout(showlegend=False)
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
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        st.plotly_chart(fig_obs, use_container_width=True)
    else:
        st.info("Columna de Observaciones no detectada.")

st.markdown("---")

# --- TABLA DE DATOS FILTRADOS ---
st.subheader("📋 Detalle de Asignaturas")
st.dataframe(df_filtered, use_container_width=True)
