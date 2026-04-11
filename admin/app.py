import os
import sys
import uuid
import hashlib
from datetime import datetime, date, timedelta

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from supabase_client import get_supabase

# Agregar path padre para importar ToteatAPI
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# ──────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────

st.set_page_config(
    page_title="Toteat Admin",
    page_icon="https://toteat.com/favicon.ico",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ──────────────────────────────────────────────
# TOTEAT BRAND PALETTE
# ──────────────────────────────────────────────

TOTEAT_RED = "#ff4235"
TOTEAT_RED_HOVER = "#ffa099"
TOTEAT_RED_LIGHT = "#fff1f0"
TOTEAT_RED_BG = "#ff42350d"
BG_PAGE = "#f7f8fa"
BG_CARD = "#ffffff"
BG_SIDEBAR = "#1a1a1a"
TEXT_PRIMARY = "#1a1a1a"
TEXT_SECONDARY = "#6b7280"
TEXT_MUTED = "#9ca3af"
BORDER = "#e5e7eb"
BORDER_LIGHT = "#f3f4f6"
SUCCESS = "#22c55e"
SUCCESS_BG = "#f0fdf4"
WARNING = "#f59e0b"
WARNING_BG = "#fffbeb"
DANGER = "#ef4444"
DANGER_BG = "#fef2f2"

CUSTOM_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito+Sans:wght@300;400;500;600;700;800;900&family=Inter:wght@400;500;600;700;800&display=swap');

/* Global */
.stApp {{
    font-family: 'Nunito Sans', 'Inter', sans-serif;
    background-color: {BG_PAGE};
}}
.block-container {{
    padding-top: 0.6rem;
    padding-bottom: 0;
    max-width: 1400px;
}}
#MainMenu, footer, header {{ visibility: hidden; }}

/* KPI Card */
.kpi {{
    background: {BG_CARD};
    border-radius: 12px;
    padding: 16px 20px;
    border: 1px solid {BORDER};
    min-height: 90px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}}
.kpi-icon {{ font-size: 1.3rem; margin-bottom: 2px; }}
.kpi-label {{
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #374151;
    margin-bottom: 2px;
}}
.kpi-val {{
    font-size: 1.6rem;
    font-weight: 800;
    color: {TEXT_PRIMARY};
    line-height: 1.2;
}}
.kpi-sub {{ font-size: 0.73rem; color: {SUCCESS}; margin-top: 3px; font-weight: 600; }}
.kpi-sub-warn {{ font-size: 0.73rem; color: {WARNING}; margin-top: 3px; font-weight: 600; }}
.kpi-sub-red {{ font-size: 0.73rem; color: {DANGER}; margin-top: 3px; font-weight: 600; }}

/* Badge */
.badge-active {{
    display: inline-block;
    background: {SUCCESS_BG};
    color: {SUCCESS};
    padding: 4px 14px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 800;
    border: 1px solid {SUCCESS}30;
}}
.badge-trial {{
    display: inline-block;
    background: {WARNING_BG};
    color: {WARNING};
    padding: 4px 14px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 800;
    border: 1px solid {WARNING}30;
}}
.badge-suspended {{
    display: inline-block;
    background: {DANGER_BG};
    color: {DANGER};
    padding: 4px 14px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 800;
    border: 1px solid {DANGER}30;
}}
.badge-created {{
    display: inline-block;
    background: #f0f4ff;
    color: #6366f1;
    padding: 4px 14px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 800;
    border: 1px solid #6366f130;
}}

/* Section header */
.sec {{
    font-size: 0.95rem;
    font-weight: 800;
    color: {TEXT_PRIMARY};
    margin: 28px 0 12px 0;
    padding-bottom: 8px;
    border-bottom: 2px solid {TOTEAT_RED};
    display: flex;
    align-items: center;
    gap: 8px;
}}

/* Header */
.toteat-header {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 0 14px 0;
    border-bottom: 1px solid {BORDER};
    margin-bottom: 18px;
}}
.toteat-brand {{
    display: flex;
    align-items: center;
    gap: 10px;
}}
.toteat-logo-icon {{
    width: 32px;
    height: 32px;
    background: {TOTEAT_RED};
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-weight: 900;
    font-size: 16px;
}}
.toteat-title {{
    font-size: 1.25rem;
    font-weight: 800;
    color: {TEXT_PRIMARY};
}}
.toteat-title span {{
    color: {TOTEAT_RED};
}}
.toteat-subtitle {{
    font-size: 0.78rem;
    color: #4b5563;
    font-weight: 500;
}}

/* Tabs - Toteat style */
.stTabs [data-baseweb="tab-list"] {{
    gap: 0;
    background: {BG_CARD};
    border-radius: 10px;
    padding: 3px;
    border: 1px solid {BORDER};
}}
.stTabs [data-baseweb="tab"] {{
    border-radius: 8px;
    padding: 8px 20px;
    font-weight: 700;
    font-size: 0.82rem;
    color: {TEXT_SECONDARY};
}}
.stTabs [aria-selected="true"] {{
    background: {TEXT_PRIMARY};
    color: white !important;
}}

/* Buttons - Toteat red */
.stButton > button {{
    background: {TOTEAT_RED};
    color: white;
    font-weight: 700;
    border: none;
    border-radius: 8px;
    padding: 6px 20px;
    font-size: 0.82rem;
    transition: all 0.2s;
    white-space: nowrap;
}}
.stButton > button:hover {{
    background: #e6372c;
    box-shadow: 0 2px 8px {TOTEAT_RED}30;
}}

/* Company table header */
.company-table-header {{
    display: grid;
    grid-template-columns: 2.5fr 1.5fr 2.5fr 1fr 1fr 2.2fr;
    gap: 8px;
    padding: 10px 16px;
    background: {TEXT_PRIMARY};
    color: white;
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    border-radius: 8px;
    margin-bottom: 4px;
}}

/* Dataframes */
.stDataFrame {{
    border-radius: 10px;
    overflow: hidden;
    border: 1px solid {BORDER};
}}

/* Plotly container */
.stPlotlyChart {{
    background: {BG_CARD};
    border-radius: 12px;
    border: 1px solid {BORDER};
    padding: 8px;
}}

/* Login container */
.login-box {{
    max-width: 400px;
    margin: 80px auto;
    background: {BG_CARD};
    border-radius: 16px;
    padding: 40px;
    border: 1px solid {BORDER};
    box-shadow: 0 4px 16px rgba(0,0,0,0.06);
    text-align: center;
}}
.login-logo {{
    width: 48px;
    height: 48px;
    background: {TOTEAT_RED};
    border-radius: 12px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-weight: 900;
    font-size: 22px;
    margin-bottom: 16px;
}}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Nunito Sans, Inter, sans-serif", color="#1a1a1a", size=12),
    margin=dict(l=16, r=16, t=40, b=16),
    xaxis=dict(gridcolor=BORDER, zeroline=False, tickfont=dict(color="#374151", size=11)),
    yaxis=dict(gridcolor=BORDER, zeroline=False, tickfont=dict(color="#374151", size=11)),
    bargap=0.3,
    title_font=dict(color="#1a1a1a", size=14),
)


# ──────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────

def kpi_card(icon, label, value, sub="", sub_class="kpi-sub"):
    return f"""
    <div class="kpi">
        <div class="kpi-icon">{icon}</div>
        <div class="kpi-label">{label}</div>
        <div class="kpi-val">{value}</div>
        <div class="{sub_class}">{sub}</div>
    </div>
    """


def section_header(icon, title):
    st.markdown(f'<div class="sec">{icon} {title}</div>', unsafe_allow_html=True)


COUNTRY_OPTIONS = ["CL", "AR", "PE", "CO", "CR", "MX"]
COUNTRY_LABELS = {"CL": "Chile", "AR": "Argentina", "PE": "Peru", "CO": "Colombia", "CR": "Costa Rica", "MX": "Mexico"}
COUNTRY_CURRENCY = {"CL": "CLP", "AR": "ARS", "PE": "PEN", "CO": "COP", "CR": "CRC", "MX": "MXN"}


def status_badge(status):
    s = (status or "").lower()
    if s == "active":
        return '<span class="badge-active">Activo</span>'
    elif s == "trial":
        return '<span class="badge-trial">Trial</span>'
    elif s in ("suspended", "inactive"):
        return '<span class="badge-suspended">Suspendido</span>'
    elif s == "created":
        return '<span class="badge-created">Creada</span>'
    return f'<span style="color:{TEXT_SECONDARY}">{status or "N/A"}</span>'


def generate_token():
    return hashlib.sha256(uuid.uuid4().hex.encode()).hexdigest()[:32]


def safe_query(query_func):
    """Ejecuta una query de Supabase con manejo de errores."""
    try:
        result = query_func()
        return result.data if result.data else []
    except Exception as e:
        st.error(f"Error de base de datos: {str(e)}")
        return []


# ──────────────────────────────────────────────
# AUTH
# ──────────────────────────────────────────────

def check_auth():
    if "admin_authenticated" not in st.session_state:
        st.session_state.admin_authenticated = False

    if st.session_state.admin_authenticated:
        return True

    st.markdown("""
    <div class="login-box">
        <div class="login-logo">T</div>
        <div style="font-size:1.3rem; font-weight:800; color:#1a1a1a; margin-bottom:4px;">
            tot<span style="color:#ff4235">eat</span> Admin
        </div>
        <div style="font-size:0.82rem; color:#6b7280; margin-bottom:24px;">
            Panel de administracion
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        password = st.text_input("Contrasena", type="password", key="admin_pw")
        if st.button("Ingresar", use_container_width=True):
            admin_pw = st.secrets.get("ADMIN_PASSWORD", "admin123")
            if password == admin_pw:
                st.session_state.admin_authenticated = True
                st.rerun()
            else:
                st.error("Contrasena incorrecta")
    return False


if not check_auth():
    st.stop()


# ──────────────────────────────────────────────
# HEADER
# ──────────────────────────────────────────────

st.markdown(f"""
<div class="toteat-header">
    <div class="toteat-brand">
        <div class="toteat-logo-icon">T</div>
        <div>
            <div class="toteat-title">tot<span>eat</span> Admin</div>
            <div class="toteat-subtitle">Panel de administracion de clientes</div>
        </div>
    </div>
    <div style="font-size:0.8rem; color:#4b5563; font-weight:600;">
        {date.today().strftime("%d %b %Y")}
    </div>
</div>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# SUPABASE CLIENT
# ──────────────────────────────────────────────

sb = get_supabase()

# ──────────────────────────────────────────────
# TABS
# ──────────────────────────────────────────────

tab_empresas, tab_restaurants, tab_usuarios, tab_billing, tab_metrics = st.tabs([
    "🏢 Empresas",
    "🍽️ Restaurantes",
    "👥 Usuarios",
    "💰 Facturacion",
    "📊 Metricas",
])


# ══════════════════════════════════════════════
# TAB 1: EMPRESAS
# ══════════════════════════════════════════════

with tab_empresas:
    companies = safe_query(lambda: sb.table("companies").select("*").execute())

    # KPI cards
    total = len(companies)
    active = sum(1 for c in companies if (c.get("status") or "").lower() == "active")
    trial = sum(1 for c in companies if (c.get("status") or "").lower() == "trial")
    suspended = sum(1 for c in companies if (c.get("status") or "").lower() in ("suspended", "inactive"))

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(kpi_card("🏢", "Total Empresas", total), unsafe_allow_html=True)
    with k2:
        st.markdown(kpi_card("✅", "Activas", active, sub_class="kpi-sub"), unsafe_allow_html=True)
    with k3:
        st.markdown(kpi_card("⏳", "En Trial", trial, sub_class="kpi-sub-warn"), unsafe_allow_html=True)
    with k4:
        st.markdown(kpi_card("🚫", "Suspendidas", suspended, sub_class="kpi-sub-red"), unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # Filtros
    fc1, fc2 = st.columns([2, 1])
    with fc1:
        search_company = st.text_input("🔍 Buscar empresa", placeholder="Nombre o email...", key="search_co")
    with fc2:
        filter_status = st.selectbox("Estado", ["Todos", "created", "active", "trial", "suspended"], key="filter_co_status")

    # Nueva empresa
    with st.expander("➕ Nueva Empresa", expanded=False):
        with st.form("form_new_company", clear_on_submit=True):
            nc1, nc2 = st.columns(2)
            with nc1:
                new_name = st.text_input("Nombre *")
                new_country = st.selectbox("Pais *", COUNTRY_OPTIONS, format_func=lambda x: COUNTRY_LABELS.get(x, x))
                new_tax_id = st.text_input("ID Fiscal (RUT/CUIT/RUC/NIT/RFC)")
                new_email = st.text_input("Email de contacto *")
            with nc2:
                new_phone = st.text_input("Telefono")
                new_plan = st.selectbox("Plan", ["trial", "starter", "professional", "enterprise"])
                new_notes = st.text_area("Notas", height=68)
            submitted = st.form_submit_button("Crear Empresa", use_container_width=True)
            if submitted:
                if not new_name or not new_email:
                    st.error("Nombre y email son requeridos")
                else:
                    try:
                        sb.table("companies").insert({
                            "name": new_name,
                            "country": new_country,
                            "tax_id": new_tax_id or None,
                            "contact_email": new_email,
                            "contact_phone": new_phone or None,
                            "plan": new_plan,
                            "status": "trial" if new_plan == "trial" else "active",
                            "notes": new_notes or None,
                        }).execute()
                        st.toast("Empresa creada exitosamente", icon="✅")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al crear empresa: {e}")

    # Importar empresas desde Excel
    with st.expander("📥 Importar Empresas desde Excel", expanded=False):
        imp_c1, imp_c2 = st.columns([2, 1])
        with imp_c2:
            # Boton descargar plantilla
            try:
                with open("admin/templates/plantilla_empresas.xlsx", "rb") as f:
                    st.download_button("📄 Descargar Plantilla", f, file_name="plantilla_empresas.xlsx",
                                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                       use_container_width=True)
            except FileNotFoundError:
                st.caption("Plantilla no disponible")
        with imp_c1:
            uploaded_companies = st.file_uploader("Sube el Excel con empresas", type=["xlsx"], key="upload_companies")

        if uploaded_companies:
            try:
                import openpyxl
                df_import = pd.read_excel(uploaded_companies, engine="openpyxl")
                required_cols = {"Nombre", "Pais", "Email"}
                if not required_cols.issubset(set(df_import.columns)):
                    st.error(f"Faltan columnas requeridas: {required_cols - set(df_import.columns)}")
                else:
                    st.dataframe(df_import.head(10), use_container_width=True, hide_index=True)
                    st.caption(f"{len(df_import)} empresas encontradas en el archivo")

                    if st.button("✅ Confirmar Importacion", key="confirm_import_companies", use_container_width=True):
                        imported = 0
                        errors = []
                        for idx, row in df_import.iterrows():
                            name = str(row.get("Nombre", "")).strip()
                            country = str(row.get("Pais", "")).strip().upper()
                            email = str(row.get("Email", "")).strip()
                            tax_id = str(row.get("ID Fiscal", "")).strip() if pd.notna(row.get("ID Fiscal")) else None
                            phone = str(row.get("Telefono", "")).strip() if pd.notna(row.get("Telefono")) else None
                            plan = str(row.get("Plan", "trial")).strip().lower()
                            notes = str(row.get("Notas", "")).strip() if pd.notna(row.get("Notas")) else None

                            if not name or not email:
                                errors.append(f"Fila {idx + 2}: Nombre y Email son requeridos")
                                continue
                            if country not in COUNTRY_OPTIONS:
                                errors.append(f"Fila {idx + 2}: Pais '{country}' no valido. Usar: {', '.join(COUNTRY_OPTIONS)}")
                                continue
                            try:
                                sb.table("companies").insert({
                                    "name": name,
                                    "country": country,
                                    "tax_id": tax_id,
                                    "contact_email": email,
                                    "contact_phone": phone,
                                    "plan": plan if plan in ("trial", "starter", "professional", "enterprise") else "trial",
                                    "status": "created",
                                    "notes": notes,
                                }).execute()
                                imported += 1
                            except Exception as e:
                                errors.append(f"Fila {idx + 2}: {e}")

                        if imported:
                            st.success(f"✅ {imported} empresas importadas correctamente")
                        if errors:
                            st.error(f"⚠️ {len(errors)} errores:")
                            for err in errors[:20]:
                                st.caption(err)
                        if imported:
                            st.rerun()
            except Exception as e:
                st.error(f"Error al leer archivo: {e}")

    # Tabla de empresas
    section_header("📋", "Listado de Empresas")

    filtered = companies
    if search_company:
        q = search_company.lower()
        filtered = [c for c in filtered if q in (c.get("name") or "").lower() or q in (c.get("contact_email") or "").lower()]
    if filter_status != "Todos":
        filtered = [c for c in filtered if (c.get("status") or "").lower() == filter_status]

    if filtered:
        # Table header
        st.markdown("""<div class="company-table-header">
            <span>Empresa</span><span>Pais</span><span>ID Fiscal</span><span>Email</span>
            <span>Plan</span><span>Estado</span><span>Acciones</span>
        </div>""", unsafe_allow_html=True)

        for c in filtered:
            with st.container():
                cols = st.columns([2.2, 0.7, 1.3, 2.2, 0.8, 0.8, 1.1, 0.9])
                with cols[0]:
                    st.markdown(f"**{c.get('name', 'N/A')}**")
                with cols[1]:
                    st.caption(c.get("country", ""))
                with cols[2]:
                    st.caption(c.get("tax_id", "—"))
                with cols[3]:
                    st.caption(c.get("contact_email", ""))
                with cols[4]:
                    st.caption(c.get("plan", "N/A"))
                with cols[5]:
                    st.markdown(status_badge(c.get("status")), unsafe_allow_html=True)
                cid = c.get("id", "")
                current_status = (c.get("status") or "").lower()
                with cols[6]:
                    if current_status != "suspended":
                        if st.button("🚫 Suspender", key=f"sus_{cid}", use_container_width=True):
                            try:
                                sb.table("companies").update({"status": "suspended"}).eq("id", cid).execute()
                                st.toast("Empresa suspendida", icon="🚫")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")
                    else:
                        if st.button("✅ Activar", key=f"act_{cid}", use_container_width=True):
                            try:
                                sb.table("companies").update({"status": "active"}).eq("id", cid).execute()
                                st.toast("Empresa activada", icon="✅")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")
                with cols[7]:
                    if st.button("✏️ Editar", key=f"edit_{cid}", use_container_width=True):
                        st.session_state[f"editing_company_{cid}"] = True
                st.markdown("<hr style='margin:0;border:none;border-top:1px solid #e5e7eb'>", unsafe_allow_html=True)

                # Formulario de edicion inline
                if st.session_state.get(f"editing_company_{cid}", False):
                    with st.form(f"form_edit_{cid}"):
                        ec1, ec2 = st.columns(2)
                        with ec1:
                            edit_name = st.text_input("Nombre", value=c.get("name", ""), key=f"en_{cid}")
                            current_country = c.get("country", "CL") or "CL"
                            edit_country = st.selectbox("Pais", COUNTRY_OPTIONS,
                                                        index=COUNTRY_OPTIONS.index(current_country) if current_country in COUNTRY_OPTIONS else 0,
                                                        format_func=lambda x: COUNTRY_LABELS.get(x, x), key=f"eco_{cid}")
                            edit_tax_id = st.text_input("ID Fiscal", value=c.get("tax_id", "") or "", key=f"er_{cid}")
                            edit_email = st.text_input("Email", value=c.get("contact_email", ""), key=f"ee_{cid}")
                        with ec2:
                            edit_phone = st.text_input("Telefono", value=c.get("contact_phone", "") or "", key=f"ep_{cid}")
                            edit_plan = st.selectbox("Plan", ["trial", "starter", "professional", "enterprise"],
                                                     index=["trial", "starter", "professional", "enterprise"].index(c.get("plan", "trial")),
                                                     key=f"epl_{cid}")
                            edit_notes = st.text_area("Notas", value=c.get("notes", "") or "", key=f"eno_{cid}")
                        sc1, sc2 = st.columns(2)
                        with sc1:
                            save = st.form_submit_button("Guardar", use_container_width=True)
                        with sc2:
                            cancel = st.form_submit_button("Cancelar", use_container_width=True)
                        if save:
                            try:
                                sb.table("companies").update({
                                    "name": edit_name,
                                    "country": edit_country,
                                    "tax_id": edit_tax_id or None,
                                    "contact_email": edit_email,
                                    "contact_phone": edit_phone or None,
                                    "plan": edit_plan,
                                    "notes": edit_notes or None,
                                }).eq("id", cid).execute()
                                st.session_state[f"editing_company_{cid}"] = False
                                st.toast("Empresa actualizada", icon="✅")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")
                        if cancel:
                            st.session_state[f"editing_company_{cid}"] = False
                            st.rerun()

                st.divider()
    else:
        st.info("No se encontraron empresas con los filtros actuales.")


# ══════════════════════════════════════════════
# TAB 2: RESTAURANTES
# ══════════════════════════════════════════════

with tab_restaurants:
    companies_list = safe_query(lambda: sb.table("companies").select("id, name").order("name").execute())
    company_options = {c["name"]: c["id"] for c in companies_list}

    if not company_options:
        st.info("No hay empresas registradas. Crea una empresa primero.")
    else:
        selected_company_name = st.selectbox("Seleccionar Empresa", list(company_options.keys()), key="sel_co_rest")
        selected_company_id = company_options[selected_company_name]

        restaurants = safe_query(
            lambda: sb.table("restaurants").select("*").eq("company_id", selected_company_id).execute()
        )

        # KPIs
        total_rest = len(restaurants)
        active_rest = sum(1 for r in restaurants if (r.get("status") or "active").lower() == "active")

        rk1, rk2 = st.columns(2)
        with rk1:
            st.markdown(kpi_card("🍽️", "Total Locales", total_rest), unsafe_allow_html=True)
        with rk2:
            st.markdown(kpi_card("✅", "Activos", active_rest), unsafe_allow_html=True)

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        # Nuevo restaurante
        with st.expander("➕ Nuevo Local", expanded=False):
            with st.form("form_new_rest", clear_on_submit=True):
                section_header("🔌", "Datos de Conexion Toteat")
                nr1, nr2 = st.columns(2)
                with nr1:
                    rest_name = st.text_input("Nombre del local *")
                    rest_slug = st.text_input("Slug (identificador corto)")
                    rest_api_token = st.text_input("API Token *")
                    rest_restaurant_id = st.text_input("Restaurant ID *")
                with nr2:
                    rest_local_id = st.text_input("Local ID *")
                    rest_user_id = st.text_input("User ID *")
                    rest_base_url = st.text_input("Base URL", value="https://api.toteat.com/mw/or/1.0/")

                section_header("💰", "Parametros Operacionales")
                op1, op2, op3, op4 = st.columns(4)
                with op1:
                    rest_sueldos = st.number_input("Sueldos ($)", min_value=0, value=0, key="r_sueldos")
                    rest_arriendo = st.number_input("Arriendo (UF)", min_value=0.0, value=0.0, step=0.1, key="r_arriendo")
                with op2:
                    rest_servicios = st.number_input("Servicios ($)", min_value=0, value=0, key="r_servicios")
                    rest_otros = st.number_input("Otros gastos ($)", min_value=0, value=0, key="r_otros")
                with op3:
                    rest_horas = st.number_input("Horas operacion/dia", min_value=0, value=12, key="r_horas")
                    rest_m2 = st.number_input("Metros cuadrados", min_value=0, value=0, key="r_m2")
                with op4:
                    rest_empleados = st.number_input("Num. empleados", min_value=0, value=0, key="r_empl")

                submitted_rest = st.form_submit_button("Crear Local", use_container_width=True)
                if submitted_rest:
                    if not rest_name or not rest_api_token or not rest_restaurant_id or not rest_local_id or not rest_user_id:
                        st.error("Completa todos los campos obligatorios (*)")
                    else:
                        try:
                            sb.table("restaurants").insert({
                                "company_id": selected_company_id,
                                "name": rest_name,
                                "slug": rest_slug or rest_name.lower().replace(" ", "-"),
                                "api_token": rest_api_token,
                                "restaurant_id": rest_restaurant_id,
                                "local_id": rest_local_id,
                                "user_id": rest_user_id,
                                "base_url": rest_base_url,
                                "sueldos": rest_sueldos,
                                "arriendo_uf": rest_arriendo,
                                "servicios": rest_servicios,
                                "otros": rest_otros,
                                "horas_op": rest_horas,
                                "m2": rest_m2,
                                "num_empleados": rest_empleados,
                                "status": "active",
                            }).execute()
                            st.toast("Local creado exitosamente", icon="✅")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al crear local: {e}")

        # Importar restaurantes desde Excel
        with st.expander("📥 Importar Locales desde Excel", expanded=False):
            imp_r1, imp_r2 = st.columns([2, 1])
            with imp_r2:
                try:
                    with open("admin/templates/plantilla_restaurantes.xlsx", "rb") as f:
                        st.download_button("📄 Descargar Plantilla", f, file_name="plantilla_restaurantes.xlsx",
                                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                           use_container_width=True, key="dl_rest_template")
                except FileNotFoundError:
                    st.caption("Plantilla no disponible")
            with imp_r1:
                uploaded_rests = st.file_uploader("Sube el Excel con locales", type=["xlsx"], key="upload_restaurants")

            if uploaded_rests:
                try:
                    import openpyxl
                    df_rest_import = pd.read_excel(uploaded_rests, engine="openpyxl")
                    required_cols = {"Nombre Empresa", "Nombre Local"}
                    if not required_cols.issubset(set(df_rest_import.columns)):
                        st.error(f"Faltan columnas requeridas: {required_cols - set(df_rest_import.columns)}")
                    else:
                        st.dataframe(df_rest_import.head(10), use_container_width=True, hide_index=True)
                        st.caption(f"{len(df_rest_import)} locales encontrados en el archivo")

                        # Build company name -> id map
                        all_companies = safe_query(lambda: sb.table("companies").select("id, name").execute())
                        co_map = {c["name"].strip().lower(): c["id"] for c in all_companies}

                        if st.button("✅ Confirmar Importacion", key="confirm_import_rests", use_container_width=True):
                            imported = 0
                            errors = []
                            for idx, row in df_rest_import.iterrows():
                                co_name = str(row.get("Nombre Empresa", "")).strip()
                                local_name = str(row.get("Nombre Local", "")).strip()

                                if not co_name or not local_name:
                                    errors.append(f"Fila {idx + 2}: Nombre Empresa y Nombre Local son requeridos")
                                    continue

                                co_id = co_map.get(co_name.lower())
                                if not co_id:
                                    errors.append(f"Fila {idx + 2}: Empresa '{co_name}' no encontrada")
                                    continue

                                slug = str(row.get("Slug", "")).strip() if pd.notna(row.get("Slug")) else local_name.lower().replace(" ", "-")
                                api_token = str(row.get("API Token", "")).strip() if pd.notna(row.get("API Token")) else None
                                rest_id = str(row.get("Restaurant ID", "")).strip() if pd.notna(row.get("Restaurant ID")) else None
                                local_id = str(row.get("Local ID", "1")).strip() if pd.notna(row.get("Local ID")) else "1"
                                user_id = str(row.get("User ID", "")).strip() if pd.notna(row.get("User ID")) else None
                                base_url = str(row.get("Base URL", "")).strip() if pd.notna(row.get("Base URL")) else "https://api.toteat.com/mw/or/1.0/"

                                def safe_int(val, default=0):
                                    try:
                                        return int(float(val)) if pd.notna(val) else default
                                    except (ValueError, TypeError):
                                        return default

                                def safe_float(val, default=0.0):
                                    try:
                                        return float(val) if pd.notna(val) else default
                                    except (ValueError, TypeError):
                                        return default

                                try:
                                    sb.table("restaurants").insert({
                                        "company_id": co_id,
                                        "name": local_name,
                                        "slug": slug,
                                        "api_token": api_token,
                                        "restaurant_id": rest_id,
                                        "local_id": local_id,
                                        "user_id": user_id,
                                        "base_url": base_url,
                                        "sueldos": safe_int(row.get("Sueldos")),
                                        "arriendo_uf": safe_float(row.get("Arriendo UF")),
                                        "servicios": safe_int(row.get("Servicios")),
                                        "otros": safe_int(row.get("Otros")),
                                        "horas_op": safe_int(row.get("Horas Op"), 12),
                                        "m2": safe_int(row.get("M2")),
                                        "num_empleados": safe_int(row.get("Num Empleados")),
                                        "status": "active",
                                    }).execute()
                                    imported += 1
                                except Exception as e:
                                    errors.append(f"Fila {idx + 2}: {e}")

                            if imported:
                                st.success(f"✅ {imported} locales importados correctamente")
                            if errors:
                                st.error(f"⚠️ {len(errors)} errores:")
                                for err in errors[:20]:
                                    st.caption(err)
                            if imported:
                                st.rerun()
                except Exception as e:
                    st.error(f"Error al leer archivo: {e}")

        # Tabla de restaurantes
        section_header("📋", "Locales")

        if restaurants:
            for r in restaurants:
                with st.container():
                    cols = st.columns([3, 2, 2, 1.5, 2.5])
                    with cols[0]:
                        st.markdown(f"**{r.get('name', 'N/A')}**")
                    with cols[1]:
                        st.caption(f"Slug: {r.get('slug', 'N/A')}")
                    with cols[2]:
                        st.caption(f"ID: {r.get('restaurant_id', 'N/A')}")
                    with cols[3]:
                        st.markdown(status_badge(r.get("status", "active")), unsafe_allow_html=True)
                    with cols[4]:
                        bc1, bc2, bc3 = st.columns(3)
                        rid = r.get("id", "")
                        with bc1:
                            if st.button("🔌 Test", key=f"test_{rid}"):
                                try:
                                    from toteat_api import ToteatAPI
                                    api = ToteatAPI(
                                        api_token=r.get("api_token", ""),
                                        restaurant_id=r.get("restaurant_id", ""),
                                        local_id=r.get("local_id", ""),
                                        user_id=r.get("user_id", ""),
                                        base_url=r.get("base_url", "https://api.toteat.com/mw/or/1.0/"),
                                    )
                                    today = date.today().isoformat()
                                    result = api.get_sales(today, today)
                                    st.toast("Conexion exitosa con Toteat API", icon="✅")
                                except ImportError:
                                    st.warning("No se pudo importar ToteatAPI. Verifica que toteat_api.py existe en el directorio padre.")
                                except Exception as e:
                                    st.error(f"Error de conexion: {e}")
                        with bc2:
                            if st.button("Editar", key=f"editr_{rid}", type="secondary"):
                                st.session_state[f"editing_rest_{rid}"] = True
                        with bc3:
                            if st.button("Eliminar", key=f"delr_{rid}", type="secondary"):
                                try:
                                    sb.table("restaurants").delete().eq("id", rid).execute()
                                    st.toast("Local eliminado", icon="🗑️")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {e}")

                    # Formulario edicion inline
                    if st.session_state.get(f"editing_rest_{rid}", False):
                        with st.form(f"form_editr_{rid}"):
                            er1, er2 = st.columns(2)
                            with er1:
                                ed_name = st.text_input("Nombre", value=r.get("name", ""), key=f"ern_{rid}")
                                ed_slug = st.text_input("Slug", value=r.get("slug", ""), key=f"ers_{rid}")
                                ed_token = st.text_input("API Token", value=r.get("api_token", ""), key=f"ert_{rid}")
                                ed_rid = st.text_input("Restaurant ID", value=r.get("restaurant_id", ""), key=f"erri_{rid}")
                            with er2:
                                ed_lid = st.text_input("Local ID", value=r.get("local_id", ""), key=f"erli_{rid}")
                                ed_uid = st.text_input("User ID", value=r.get("user_id", ""), key=f"erui_{rid}")
                                ed_url = st.text_input("Base URL", value=r.get("base_url", ""), key=f"erurl_{rid}")
                            sc1, sc2 = st.columns(2)
                            with sc1:
                                save_r = st.form_submit_button("Guardar", use_container_width=True)
                            with sc2:
                                cancel_r = st.form_submit_button("Cancelar", use_container_width=True)
                            if save_r:
                                try:
                                    sb.table("restaurants").update({
                                        "name": ed_name,
                                        "slug": ed_slug,
                                        "api_token": ed_token,
                                        "restaurant_id": ed_rid,
                                        "local_id": ed_lid,
                                        "user_id": ed_uid,
                                        "base_url": ed_url,
                                    }).eq("id", rid).execute()
                                    st.session_state[f"editing_rest_{rid}"] = False
                                    st.toast("Local actualizado", icon="✅")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {e}")
                            if cancel_r:
                                st.session_state[f"editing_rest_{rid}"] = False
                                st.rerun()

                    st.divider()
        else:
            st.info("No hay locales registrados para esta empresa.")


# ══════════════════════════════════════════════
# TAB 3: USUARIOS
# ══════════════════════════════════════════════

with tab_usuarios:
    companies_list_u = safe_query(lambda: sb.table("companies").select("id, name").order("name").execute())
    company_options_u = {c["name"]: c["id"] for c in companies_list_u}

    if not company_options_u:
        st.info("No hay empresas registradas. Crea una empresa primero.")
    else:
        selected_company_name_u = st.selectbox("Seleccionar Empresa", list(company_options_u.keys()), key="sel_co_usr")
        selected_company_id_u = company_options_u[selected_company_name_u]

        users = safe_query(
            lambda: sb.table("users").select("*").eq("company_id", selected_company_id_u).execute()
        )

        # KPIs
        total_users = len(users)
        active_users = sum(1 for u in users if (u.get("status") or "active").lower() == "active")
        admins = sum(1 for u in users if (u.get("role") or "").lower() == "admin")
        viewers = sum(1 for u in users if (u.get("role") or "").lower() == "viewer")

        uk1, uk2, uk3, uk4 = st.columns(4)
        with uk1:
            st.markdown(kpi_card("👥", "Total Usuarios", total_users), unsafe_allow_html=True)
        with uk2:
            st.markdown(kpi_card("✅", "Activos", active_users), unsafe_allow_html=True)
        with uk3:
            st.markdown(kpi_card("🛡️", "Admins", admins, sub_class="kpi-sub-warn"), unsafe_allow_html=True)
        with uk4:
            st.markdown(kpi_card("👁️", "Viewers", viewers), unsafe_allow_html=True)

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        # Restaurantes de la empresa para permisos
        company_restaurants = safe_query(
            lambda: sb.table("restaurants").select("id, name").eq("company_id", selected_company_id_u).execute()
        )
        rest_options = {r["name"]: r["id"] for r in company_restaurants}

        # Nuevo usuario
        with st.expander("➕ Nuevo Usuario", expanded=False):
            with st.form("form_new_user", clear_on_submit=True):
                nu1, nu2 = st.columns(2)
                with nu1:
                    user_name = st.text_input("Nombre *")
                    user_email = st.text_input("Email *")
                with nu2:
                    user_role = st.selectbox("Rol", ["admin", "manager", "viewer"])
                    user_restaurants = st.multiselect(
                        "Restaurantes con acceso",
                        options=list(rest_options.keys()),
                        key="new_user_rests",
                    )

                submitted_user = st.form_submit_button("Crear Usuario", use_container_width=True)
                if submitted_user:
                    if not user_name or not user_email:
                        st.error("Nombre y email son requeridos")
                    else:
                        try:
                            new_token = generate_token()
                            result = sb.table("users").insert({
                                "company_id": selected_company_id_u,
                                "name": user_name,
                                "email": user_email,
                                "role": user_role,
                                "token": new_token,
                                "status": "active",
                            }).execute()

                            # Asignar restaurantes
                            if result.data and user_restaurants:
                                new_user_id = result.data[0]["id"]
                                for rname in user_restaurants:
                                    rid = rest_options[rname]
                                    sb.table("user_restaurants").insert({
                                        "user_id": new_user_id,
                                        "restaurant_id": rid,
                                    }).execute()

                            st.toast("Usuario creado exitosamente", icon="✅")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al crear usuario: {e}")

        # Tabla de usuarios
        section_header("📋", "Listado de Usuarios")

        app_base_url = st.secrets.get("APP_BASE_URL", "https://agente-toteat.streamlit.app")

        if users:
            for u in users:
                with st.container():
                    cols = st.columns([2.5, 2.5, 1.5, 1.5, 3])
                    with cols[0]:
                        st.markdown(f"**{u.get('name', 'N/A')}**")
                    with cols[1]:
                        st.caption(u.get("email", ""))
                    with cols[2]:
                        role = u.get("role", "viewer")
                        role_colors = {"admin": WARNING, "manager": SUCCESS, "viewer": TEXT_SECONDARY}
                        st.markdown(
                            f'<span style="color:{role_colors.get(role, TEXT_SECONDARY)}; font-weight:700; font-size:0.82rem">{role.upper()}</span>',
                            unsafe_allow_html=True,
                        )
                    with cols[3]:
                        st.markdown(status_badge(u.get("status", "active")), unsafe_allow_html=True)
                    with cols[4]:
                        token = u.get("token", "")
                        access_link = f"{app_base_url}?token={token}"
                        uid = u.get("id", "")
                        bc1, bc2, bc3 = st.columns(3)
                        with bc1:
                            st.code(access_link, language=None)
                        with bc2:
                            current_u_status = (u.get("status") or "active").lower()
                            if current_u_status == "active":
                                if st.button("Suspender", key=f"susu_{uid}", type="secondary"):
                                    try:
                                        sb.table("users").update({"status": "suspended"}).eq("id", uid).execute()
                                        st.toast("Usuario suspendido", icon="🚫")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error: {e}")
                            else:
                                if st.button("Activar", key=f"actu_{uid}", type="secondary"):
                                    try:
                                        sb.table("users").update({"status": "active"}).eq("id", uid).execute()
                                        st.toast("Usuario activado", icon="✅")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error: {e}")
                        with bc3:
                            if st.button("Eliminar", key=f"delu_{uid}", type="secondary"):
                                try:
                                    sb.table("user_restaurants").delete().eq("user_id", uid).execute()
                                    sb.table("users").delete().eq("id", uid).execute()
                                    st.toast("Usuario eliminado", icon="🗑️")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {e}")

                    # Ultimo login
                    last_login = u.get("last_login_at")
                    if last_login:
                        st.caption(f"Ultimo login: {last_login[:16].replace('T', ' ')}")

                    st.divider()
        else:
            st.info("No hay usuarios registrados para esta empresa.")


# ══════════════════════════════════════════════
# TAB 4: FACTURACION
# ══════════════════════════════════════════════

with tab_billing:
    subscriptions = safe_query(lambda: sb.table("subscriptions").select("*, companies(name)").execute())
    payments = safe_query(lambda: sb.table("payments").select("*, companies(name)").order("payment_date", desc=True).execute())

    # KPIs
    active_subs = [s for s in subscriptions if (s.get("status") or "").lower() == "active"]
    mrr = sum(float(s.get("amount_usd") or 0) for s in active_subs)
    paying = len(active_subs)
    overdue = sum(1 for s in subscriptions if (s.get("status") or "").lower() == "overdue")
    total_revenue = sum(float(p.get("amount_usd") or 0) for p in payments if (p.get("status") or "").lower() == "paid")

    bk1, bk2, bk3, bk4 = st.columns(4)
    with bk1:
        st.markdown(kpi_card("💰", "MRR", f"${mrr:,.0f}"), unsafe_allow_html=True)
    with bk2:
        st.markdown(kpi_card("✅", "Clientes Pagando", paying), unsafe_allow_html=True)
    with bk3:
        st.markdown(kpi_card("⚠️", "Morosos", overdue, sub_class="kpi-sub-red"), unsafe_allow_html=True)
    with bk4:
        st.markdown(kpi_card("📈", "Revenue Acumulado", f"${total_revenue:,.0f}"), unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # Tabla de suscripciones
    section_header("📋", "Suscripciones")

    if subscriptions:
        sub_data = []
        for s in subscriptions:
            company_name = ""
            if isinstance(s.get("companies"), dict):
                company_name = s["companies"].get("name", "")
            sub_data.append({
                "Empresa": company_name,
                "Monto USD": f"${float(s.get('amount_usd') or 0):,.2f}",
                "Estado": (s.get("status") or "N/A").upper(),
                "Inicio": (s.get("start_date") or "")[:10],
                "Ultimo Pago": (s.get("last_payment_date") or "")[:10],
            })
        df_subs = pd.DataFrame(sub_data)
        st.dataframe(df_subs, use_container_width=True, hide_index=True)
    else:
        st.info("No hay suscripciones registradas.")

    # Tabla de pagos recientes
    section_header("💳", "Pagos Recientes")

    if payments:
        pay_data = []
        for p in payments[:20]:
            company_name = ""
            if isinstance(p.get("companies"), dict):
                company_name = p["companies"].get("name", "")
            pay_data.append({
                "Empresa": company_name,
                "Monto USD": f"${float(p.get('amount_usd') or 0):,.2f}",
                "Estado": (p.get("status") or "N/A").upper(),
                "Metodo": p.get("method", "N/A"),
                "Fecha": (p.get("payment_date") or "")[:10],
            })
        df_pays = pd.DataFrame(pay_data)
        st.dataframe(df_pays, use_container_width=True, hide_index=True)
    else:
        st.info("No hay pagos registrados.")

    # MRR Chart
    section_header("📈", "MRR Historico")

    if payments:
        try:
            pay_df = pd.DataFrame(payments)
            pay_df["payment_date"] = pd.to_datetime(pay_df["payment_date"], errors="coerce")
            pay_df["amount_usd"] = pd.to_numeric(pay_df["amount_usd"], errors="coerce").fillna(0)
            pay_df = pay_df.dropna(subset=["payment_date"])

            if not pay_df.empty:
                monthly = pay_df.set_index("payment_date").resample("MS")["amount_usd"].sum().reset_index()
                monthly.columns = ["Mes", "Revenue"]

                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=monthly["Mes"],
                    y=monthly["Revenue"],
                    mode="lines+markers",
                    line=dict(color=TOTEAT_RED, width=3),
                    marker=dict(size=8, color=TOTEAT_RED),
                    fill="tozeroy",
                    fillcolor=f"{TOTEAT_RED}15",
                    name="MRR",
                ))
                fig.update_layout(
                    **PLOTLY_LAYOUT,
                    title="Revenue Mensual (USD)",
                    yaxis_title="USD",
                    showlegend=False,
                    height=350,
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No hay datos suficientes para el grafico.")
        except Exception as e:
            st.warning(f"No se pudo generar el grafico: {e}")
    else:
        st.info("No hay datos de pagos para graficar.")


# ══════════════════════════════════════════════
# TAB 5: METRICAS
# ══════════════════════════════════════════════

with tab_metrics:
    # Cargar logs
    seven_days_ago = (date.today() - timedelta(days=7)).isoformat()
    thirty_days_ago = (date.today() - timedelta(days=30)).isoformat()

    recent_logs = safe_query(
        lambda: sb.table("usage_logs").select("*").gte("timestamp", thirty_days_ago).order("timestamp", desc=True).execute()
    )

    all_users_count = safe_query(lambda: sb.table("users").select("id", count="exact").eq("status", "active").execute())
    all_restaurants_count = safe_query(lambda: sb.table("restaurants").select("id", count="exact").eq("status", "active").execute())

    # Calcular metricas
    week_logs = [l for l in recent_logs if l.get("timestamp", "") >= seven_days_ago]
    unique_users_7d = len(set(l.get("user_id") for l in week_logs if l.get("user_id")))
    chat_queries = sum(1 for l in recent_logs if (l.get("action") or "").lower() in ("chat", "query", "message"))
    total_active_users = len(all_users_count) if isinstance(all_users_count, list) else 0
    total_active_restaurants = len(all_restaurants_count) if isinstance(all_restaurants_count, list) else 0

    mk1, mk2, mk3 = st.columns(3)
    with mk1:
        st.markdown(kpi_card("👥", "Usuarios Activos (7d)", unique_users_7d), unsafe_allow_html=True)
    with mk2:
        st.markdown(kpi_card("💬", "Queries Chat (30d)", chat_queries), unsafe_allow_html=True)
    with mk3:
        st.markdown(kpi_card("🍽️", "Locales Conectados", total_active_restaurants), unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # Logins por dia
    section_header("📈", "Logins por Dia (ultimos 30 dias)")

    login_logs = [l for l in recent_logs if (l.get("action") or "").lower() in ("login", "access", "view")]
    if login_logs:
        try:
            log_df = pd.DataFrame(login_logs)
            log_df["timestamp"] = pd.to_datetime(log_df["timestamp"], errors="coerce")
            log_df = log_df.dropna(subset=["timestamp"])

            if not log_df.empty:
                daily = log_df.set_index("timestamp").resample("D").size().reset_index(name="Logins")
                daily.columns = ["Fecha", "Logins"]

                fig_logins = go.Figure()
                fig_logins.add_trace(go.Bar(
                    x=daily["Fecha"],
                    y=daily["Logins"],
                    marker_color=TOTEAT_RED,
                    name="Logins",
                ))
                fig_logins.update_layout(
                    **PLOTLY_LAYOUT,
                    title="Logins Diarios",
                    yaxis_title="Cantidad",
                    showlegend=False,
                    height=320,
                )
                st.plotly_chart(fig_logins, use_container_width=True)
            else:
                st.info("No hay datos de login para graficar.")
        except Exception as e:
            st.warning(f"No se pudo generar el grafico: {e}")
    else:
        st.info("No hay datos de login en los ultimos 30 dias.")

    # Top usuarios por actividad
    section_header("🏆", "Top Usuarios por Actividad")

    if recent_logs:
        try:
            user_activity = {}
            for l in recent_logs:
                uid = l.get("user_id")
                if uid:
                    user_activity[uid] = user_activity.get(uid, 0) + 1

            if user_activity:
                # Obtener nombres de usuarios
                top_user_ids = sorted(user_activity.keys(), key=lambda x: user_activity[x], reverse=True)[:10]
                top_users_data = safe_query(
                    lambda: sb.table("users").select("id, name, email").in_("id", top_user_ids).execute()
                )
                user_names = {u["id"]: u.get("name", u.get("email", "N/A")) for u in top_users_data}

                top_data = []
                for uid in top_user_ids:
                    top_data.append({
                        "Usuario": user_names.get(uid, uid[:8] + "..."),
                        "Acciones": user_activity[uid],
                    })
                df_top = pd.DataFrame(top_data)
                st.dataframe(df_top, use_container_width=True, hide_index=True)
            else:
                st.info("No hay actividad de usuarios registrada.")
        except Exception as e:
            st.warning(f"Error al cargar top usuarios: {e}")
    else:
        st.info("No hay logs de actividad.")

    # Acciones mas frecuentes
    section_header("📊", "Acciones Mas Frecuentes")

    if recent_logs:
        try:
            action_counts = {}
            for l in recent_logs:
                action = l.get("action") or "unknown"
                action_counts[action] = action_counts.get(action, 0) + 1

            if action_counts:
                sorted_actions = sorted(action_counts.items(), key=lambda x: x[1], reverse=True)[:10]
                actions_df = pd.DataFrame(sorted_actions, columns=["Accion", "Cantidad"])

                fig_actions = go.Figure()
                fig_actions.add_trace(go.Bar(
                    x=actions_df["Cantidad"],
                    y=actions_df["Accion"],
                    orientation="h",
                    marker_color=TOTEAT_RED,
                ))
                fig_actions.update_layout(
                    **PLOTLY_LAYOUT,
                    title="Top 10 Acciones",
                    xaxis_title="Cantidad",
                    yaxis=dict(autorange="reversed", gridcolor=BORDER),
                    showlegend=False,
                    height=350,
                )
                st.plotly_chart(fig_actions, use_container_width=True)
            else:
                st.info("No hay acciones registradas.")
        except Exception as e:
            st.warning(f"Error al cargar acciones: {e}")
    else:
        st.info("No hay logs de actividad.")
