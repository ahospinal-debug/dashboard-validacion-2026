import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# Configuración inicial de la página
st.set_page_config(
    page_title="Dashboard de Seguimiento de Validación 2026",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Dashboard de Seguimiento de Validación 2026")
st.markdown("---")

# BARRA LATERAL (SIDEBAR)
st.sidebar.header("⚙️ Configuración y Filtros")

# Carga automática directa desde el repositorio de GitHub
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
col_eap = get_col([], ["EAP", "CARRERA", "PROGRAMA"])
col_asig = get_col([], ["ASIGNATURA", "NOMBRE ASIGNATURA", "CURSO"])

# Columnas de Fechas para las Reglas del Semáforo
col_f_ter_val = get_col(["U"], ["FECHA DE TERMINO DE VALIDACION", "TÉRMINO DE VALIDACIÓN", "TERMINO DE VALIDACION"])
col_f_envio_obs = get_col(["AG"], ["FECHA DE ENVÍO DE OBSERVACIONES", "ENVIO DE OBSERVACIONES", "OBSERVACIONES DEL VALIDADOR"])
col_f_resp_dis = get_col(["AK"], ["FECHA DE RESPUESTA DEL DISEÑADOR", "RESPUESTA DEL DISEÑADOR", "RESPUESTA DISEÑADOR"])

if not col_estado:
    col_estado = df.columns[10] if len(df.columns) > 10 else df.columns[0]

# Rellenar vacíos manteniendo el total de asignaturas
df[col_estado] = df[col_estado].fillna('Sin registro / No iniciada')
if col_obs and col_obs in df.columns:
    df[col_obs] = df[col_obs].fillna('Sin observaciones')

# Convertir columnas de fechas a datetime
for col_f in [col_f_ter_val, col_f_envio_obs, col_f_resp_dis]:
    if col_f and col_f in df.columns:
        df[col_f] = pd.to_datetime(df[col_f], errors='coerce')

# --- FUNCIÓN CÁLCULO DÍAS HÁBILES (EXCLUYE SÁBADOS Y DOMINGOS) ---
def obtener_dias_habiles(f_inicio, f_fin):
    if pd.isnull(f_inicio) or pd.isnull(f_fin):
        return np.nan
    d1 = np.datetime64(f_inicio.date(), 'D')
    d2 = np.datetime64(f_fin.date(), 'D')
    return np.busday_count(d1, d2)

# --- LÓGICA DEL SEMÁFORO (DÍAS HÁBILES PARA VALIDADOR Y DISEÑADOR) ---
def calcular_semaforo_actualizado(row):
    f_U = row.get(col_f_ter_val) if col_f_ter_val else None
    f_AG = row.get(col_f_envio_obs) if col_f_envio_obs else None
    f_AK = row.get(col_f_resp_dis) if col_f_resp_dis else None

    alertas = []

    # 1) Evaluación Validador en días hábiles (Col. AG vs Col. U)
    if pd.notnull(f_AG) and pd.notnull(f_U):
        dias_val = obtener_dias_habiles(f_U, f_AG)
        if not np.isnan(dias_val):
            if dias_val <= 0:
                alertas.append('🟢 Validador en Fecha')
            else:
                alertas.append('🔴 Validador Vencido')

    # 2) Evaluación Diseñador en días hábiles (Col. AK vs Col. AG + 2 días L-V)
    if pd.notnull(f_AK) and pd.notnull(f_AG):
        dias_dis = obtener_dias_habiles(f_AG, f_AK)
        if not np.isnan(dias_dis):
            if dias_dis <= 2:
                alertas.append('🟢 Diseñador en Fecha')
            else:
                alertas.append('🔴 Diseñador Vencido')

    if not alertas:
        return '⚪ Sin Fechas Registradas'
    
    return ' | '.join(alertas)

df['Semáforo de Plazo'] = df.apply(calcular_semaforo_actualizado, axis=1)

# --- FILTROS ---
st.sidebar.subheader("🎯 Filtros")

if col_eap and col_eap in df.columns:
    eaps = ["Todas"] + sorted([str(x) for x in df[col_eap].dropna().unique()])
    eap_sel = st.sidebar.selectbox("Filtrar por EAP / Carrera:", eaps)
    if eap_sel != "Todas":
        df = df[df[col_eap] == eap_sel]

validador_sel = "Todos"
if col_validador and col_validador in df.columns:
    validadores = ["Todos"] + sorted([str(x) for x in df[col_validador].dropna().unique()])
    validador_sel = st.sidebar.selectbox("👤 Validador (Col. O):", validadores)

df_validador = df.copy()
if validador_sel != "Todos":
    df_validador = df[df[col_validador] == validador_sel]

disenador_sel = "Todos"
if col_disenador and col_disenador in df_validador.columns:
    disenadores_disponibles = ["Todos"] + sorted([str(x) for x in df_validador[col_disenador].dropna().unique()])
    disenador_sel = st.sidebar.selectbox("🎨 Diseñador Instruccional (Col. AB):", disenadores_disponibles)

df_final = df_validador.copy()
if disenador_sel != "Todos":
    df_final = df_final[df_final[col_disenador] == disenador_sel]

# --- KPIS ---
total_asig = len(df_final)
pasa_imp = len(df_final[df_final[col_estado].str.contains('Pasa a implementación|implementación', case=False, na=False)])
observadas = len(df_final[df_final[col_estado].str.contains('Observada', case=False, na=False)])
pendientes = total_asig - (pasa_imp + observadas)

pct = f"↑ {(pasa_imp/total_asig)*100:.1f}%" if total_asig > 0 else "0%"

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Asignaturas", total_asig)
k2.metric("Pasan a Implementación", pasa_imp, delta=pct)
k3.metric("Observadas", observadas)
k4.metric("Pendientes / Sin iniciar", pendientes)

st.markdown("---")

# --- GRÁFICOS DINÁMICOS ---
g1, g2 = st.columns(2)

with g1:
    st.subheader("📌 Distribución por Estado de Validación")
    df_est = df_final[col_estado].value_counts().reset_index()
    df_est.columns = ['Estado', 'Cantidad']
    fig_est = px.bar(
        df_est, x='Estado', y='Cantidad', color='Estado',
        text='Cantidad',
        color_discrete_map={
            'Pasa a implementación': '#50C878',
            'Observada': '#FF6F61',
            'Sin registro / No iniciada': '#7F97C7'
        }
    )
    fig_est.update_traces(textposition='outside')
    fig_est.update_layout(showlegend=False, xaxis_title="", yaxis_title="N° Asignaturas")
    st.plotly_chart(fig_est, use_container_width=True)

with g2:
    if disenador_sel != "Todos" and col_obs and col_obs in df_final.columns:
        st.subheader(f"🎨 Nivel de Observación ({disenador_sel})")
        df_obs_cnt = df_final[col_obs].value_counts().reset_index()
        df_obs_cnt.columns = ['Nivel', 'Cantidad']
        fig_obs = px.bar(
            df_obs_cnt, x='Nivel', y='Cantidad', color='Nivel',
            text='Cantidad', color_discrete_sequence=px.colors.qualitative.Bold
        )
        fig_obs.update_traces(textposition='outside')
        fig_obs.update_layout(showlegend=False, xaxis_title="", yaxis_title="N° Asignaturas")
        st.plotly_chart(fig_obs, use_container_width=True)

    elif validador_sel != "Todos":
        st.subheader(f"⚠️ Proporción del Validador ({validador_sel})")
        df_pie = df_final[col_estado].value_counts().reset_index()
        df_pie.columns = ['Estado', 'Cantidad']
        fig_pie = px.pie(
            df_pie, values='Cantidad', names='Estado', hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        fig_pie.update_traces(textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)

    else:
        st.subheader("⚠️ Proporción de Asignaturas Observadas")
        obs_yes = observadas
        obs_no = total_asig - observadas
        df_prop = pd.DataFrame({'Observada': ['Sí', 'No'], 'Cantidad': [obs_yes, obs_no]})
        fig_prop = px.pie(
            df_prop, values='Cantidad', names='Observada', hole=0.4,
            color='Observada',
            color_discrete_map={'Sí': '#50C878', 'No': '#FF4D4D'}
        )
        fig_prop.update_traces(textinfo='percent+label')
        st.plotly_chart(fig_prop, use_container_width=True)

st.markdown("---")

# --- TABLA DE DETALLE ---
st.subheader("📋 Detalle General de Asignaturas")

f1, f2 = st.columns(2)
with f1:
    busqueda_asig = st.text_input("🔍 Buscar por Nombre de Asignatura:")
with f2:
    estados_unicos = list(df_final[col_estado].unique())
    filtro_estado_tbl = st.multiselect("Filtrar por Estado:", estados_unicos)

df_tabla = df_final.copy()
if busqueda_asig and col_asig and col_asig in df_tabla.columns:
    df_tabla = df_tabla[df_tabla[col_asig].astype(str).str.contains(busqueda_asig, case=False, na=False)]
if filtro_estado_tbl:
    df_tabla = df_tabla[df_tabla[col_estado].isin(filtro_estado_tbl)]

st.dataframe(df_tabla, use_container_width=True)
