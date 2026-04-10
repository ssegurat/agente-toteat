import os
import json
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv
from toteat_api import ToteatAPI
from tools import TOOLS, execute_tool
from datetime import date, timedelta
import time

load_dotenv()

# ──────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────

st.set_page_config(
    page_title="Toteat Intelligence",
    page_icon="https://toteat.com/favicon.ico",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ──────────────────────────────────────────────
# TOTEAT BRAND PALETTE (Light Mode)
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

TOTEAT_LOGO_SVG = """<svg width="120" height="28" viewBox="0 0 120 28" fill="none" xmlns="http://www.w3.org/2000/svg">
<text x="0" y="22" font-family="Inter, sans-serif" font-size="22" font-weight="800" fill="#1a1a1a">tot<tspan fill="#ff4235">eat</tspan></text>
</svg>"""

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
.badge-open {{
    display: inline-block;
    background: {SUCCESS_BG};
    color: {SUCCESS};
    padding: 4px 14px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 800;
    border: 1px solid {SUCCESS}30;
}}
.badge-closed {{
    display: inline-block;
    background: {DANGER_BG};
    color: {DANGER};
    padding: 4px 14px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 800;
    border: 1px solid {DANGER}30;
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
.toteat-date {{
    font-size: 0.8rem;
    color: #4b5563;
    font-weight: 600;
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
}}
.stButton > button:hover {{
    background: #e6372c;
    box-shadow: 0 2px 8px {TOTEAT_RED}30;
}}

/* Sidebar */
section[data-testid="stSidebar"] {{
    background: {BG_SIDEBAR};
    border-right: none;
}}

/* Dataframes */
.stDataFrame {{
    border-radius: 10px;
    overflow: hidden;
    border: 1px solid {BORDER};
}}

/* Date inputs */
.stDateInput > div > div {{
    border-radius: 8px;
}}

/* Expander */
.streamlit-expanderHeader {{
    font-weight: 700;
    font-size: 0.85rem;
}}

/* Plotly container */
.stPlotlyChart {{
    background: {BG_CARD};
    border-radius: 12px;
    border: 1px solid {BORDER};
    padding: 8px;
}}

/* Metric cards in columns */
[data-testid="stVerticalBlockBorderWrapper"] {{
    border-radius: 12px;
}}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

SYSTEM_PROMPT = f"""Eres un asistente inteligente para restaurantes que usan Toteat como sistema POS.
Hoy es {date.today().isoformat()}.
Responde siempre en espanol. Usa las herramientas para consultar datos.
Si el usuario dice "hoy", "ayer", "esta semana", calcula las fechas correctas.
Presenta los datos de forma clara con tablas cuando sea apropiado.
"""

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

CHART_COLORS = [TOTEAT_RED, "#ff6b61", "#ffa099", "#ffccc8", "#1a1a1a", "#6b7280", "#22c55e", "#f59e0b"]
COLOR_SCALE = [[0, "#ffccc8"], [0.5, TOTEAT_RED], [1, "#c41e12"]]


# ── Helpers ──

def fmt(v):
    try:
        v = float(v)
        if v >= 1_000_000:
            return f"${v/1_000_000:.1f}M"
        return f"${v:,.0f}".replace(",", ".")
    except (ValueError, TypeError):
        return "$0"

def fmt_full(v):
    try:
        return f"${int(v):,}".replace(",", ".")
    except (ValueError, TypeError):
        return "$0"

def fmt_pct(v):
    try:
        return f"{float(v):.1f}%"
    except (ValueError, TypeError):
        return "0%"

def kpi(icon, label, value, sub=None, sub_type="normal", delta=None, delta_abs=None):
    sc = {"normal": "kpi-sub", "warn": "kpi-sub-warn", "red": "kpi-sub-red"}.get(sub_type, "kpi-sub")
    sub_h = f'<div class="{sc}">{sub}</div>' if sub else ""
    delta_h = ""
    if delta is not None:
        try:
            d = float(delta)
            # Formato del monto absoluto de diferencia
            abs_text = ""
            if delta_abs is not None:
                abs_val = float(delta_abs)
                if abs_val >= 0:
                    abs_text = f" ({fmt(abs_val)})"
                else:
                    abs_text = f" (-{fmt(abs(-abs_val))})"
            if d > 0:
                delta_h = f'<div style="font-size:0.72rem;font-weight:700;color:{SUCCESS};margin-top:2px;">▲ +{d:.1f}%{abs_text}</div>'
            elif d < 0:
                delta_h = f'<div style="font-size:0.72rem;font-weight:700;color:{DANGER};margin-top:2px;">▼ {d:.1f}%{abs_text}</div>'
            else:
                delta_h = f'<div style="font-size:0.72rem;font-weight:700;color:#6b7280;margin-top:2px;">= 0%{abs_text}</div>'
        except (ValueError, TypeError):
            pass
    return f'<div class="kpi"><div class="kpi-icon">{icon}</div><div class="kpi-label">{label}</div><div class="kpi-val">{value}</div>{delta_h}{sub_h}</div>'


def calc_delta(current, previous):
    """Calcula % de variacion entre periodo actual y anterior."""
    if previous and previous > 0:
        return ((current - previous) / previous) * 100
    return None

def sec(icon, text):
    st.markdown(f'<div class="sec">{icon} {text}</div>', unsafe_allow_html=True)


CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "restaurant_config.json")


def _load_restaurant_config() -> dict:
    """Carga configuracion: primero archivo local, luego Streamlit Secrets como fallback."""
    # Intentar archivo local primero
    try:
        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)
            if data:
                return data
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    # Fallback: leer desde Streamlit Secrets (para Streamlit Cloud)
    defaults = {}
    try:
        rc = st.secrets["restaurant_config"]
        defaults["sueldos"] = int(rc["sueldos"])
        defaults["arriendo_uf"] = float(rc["arriendo_uf"])
        defaults["servicios"] = int(rc["servicios"])
        defaults["otros"] = int(rc["otros"])
        defaults["horas_op"] = int(rc["horas_op"])
        defaults["m2"] = int(rc["m2"])
        defaults["num_empleados"] = int(rc["num_empleados"])
    except Exception:
        pass
    return defaults


def _save_restaurant_config(config: dict):
    """Guarda configuracion del restaurante en archivo JSON."""
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=2)
    except Exception:
        pass


def _subtract_months(d, months):
    """Resta meses a una fecha, ajustando si el dia no existe en el mes destino."""
    import calendar
    m = d.month - months
    y = d.year
    while m < 1:
        m += 12
        y -= 1
    max_day = calendar.monthrange(y, m)[1]
    return d.replace(year=y, month=m, day=min(d.day, max_day))


def _subtract_years(d, years):
    """Resta años a una fecha, ajustando para bisiesto (29 feb -> 28 feb)."""
    import calendar
    y = d.year - years
    max_day = calendar.monthrange(y, d.month)[1]
    return d.replace(year=y, day=min(d.day, max_day))


# ── API calls con cache para evitar 429 ──

def _chunked_api_call(api_fn, date_from: str, date_to: str):
    """Llama una API con rango de fechas, dividiendo en chunks de 15 dias si es necesario."""
    d_from = date.fromisoformat(date_from)
    d_to = date.fromisoformat(date_to)
    delta = (d_to - d_from).days

    if delta <= 15:
        return api_fn(date_from, date_to)

    all_data = []
    chunk_start = d_from
    first_chunk = True
    while chunk_start <= d_to:
        if not first_chunk:
            time.sleep(2)
        chunk_end = min(chunk_start + timedelta(days=14), d_to)
        raw = api_fn(chunk_start.isoformat(), chunk_end.isoformat())
        # Extraer datos segun formato de respuesta
        if isinstance(raw, list):
            all_data.extend(raw)
        elif isinstance(raw, dict):
            chunk_data = raw.get("data", [])
            if isinstance(chunk_data, list):
                all_data.extend(chunk_data)
        chunk_start = chunk_end + timedelta(days=1)
        first_chunk = False

    return {"data": all_data}

@st.cache_data(ttl=300, show_spinner=False)
def cached_get_sales(_client, date_from: str, date_to: str):
    """Ventas cacheadas por 5 minutos. Divide en chunks de 15 dias si el rango es mayor."""
    return _chunked_api_call(_client.get_sales, date_from, date_to)

@st.cache_data(ttl=300, show_spinner=False)
def cached_get_products(_client):
    """Productos cacheados por 5 minutos."""
    return _client.get_products()

@st.cache_data(ttl=60, show_spinner=False)
def cached_get_shift(_client):
    """Estado de turno cacheado por 1 minuto."""
    return _client.get_shift_status()

@st.cache_data(ttl=60, show_spinner=False)
def cached_get_tables(_client):
    """Mesas cacheadas por 1 minuto."""
    return _client.get_tables()

@st.cache_data(ttl=120, show_spinner=False)
def cached_get_cancellations(_client, date_from: str, date_to: str):
    return _chunked_api_call(_client.get_cancellation_report, date_from, date_to)

@st.cache_data(ttl=300, show_spinner=False)
def cached_get_fiscal_docs(_client, date_from: str, date_to: str):
    return _chunked_api_call(_client.get_fiscal_documents, date_from, date_to)

@st.cache_data(ttl=120, show_spinner=False)
def cached_get_collection(_client, date_str: str):
    return _client.get_collection(date_str)

@st.cache_data(ttl=300, show_spinner=False)
def cached_get_inventory(_client, date_from: str, date_to: str):
    return _client.get_inventory_state(date_from, date_to)

@st.cache_data(ttl=300, show_spinner=False)
def cached_get_accounting(_client, date_from: str, date_to: str):
    return _client.get_accounting_movements(date_from, date_to)

@st.cache_data(ttl=3600, show_spinner=False)
def get_uf_value():
    """Obtiene el valor actual de la UF desde mindicador.cl."""
    import requests
    try:
        r = requests.get("https://mindicador.cl/api/uf", timeout=10)
        data = r.json()
        return data["serie"][0]["valor"]
    except Exception:
        return None


# ── Procesamiento de ventas ──

def process_sales(data):
    if not data:
        return None

    total_sales = sum(o.get("total", 0) for o in data)
    total_gratuity = sum(o.get("gratuity", 0) for o in data)
    total_discounts = sum(o.get("discounts", 0) for o in data)
    total_cost = sum(o.get("totalCost", 0) for o in data)
    total_clients = sum(o.get("numberClients", 0) for o in data)
    num_orders = len(data)
    avg_ticket = total_sales / num_orders if num_orders else 0
    avg_per_client = total_sales / total_clients if total_clients else 0
    margin = ((total_sales - total_cost) / total_sales * 100) if total_sales else 0

    payment_map = {}
    for o in data:
        for pf in o.get("paymentForms", []):
            name = pf.get("name", "Otro")
            amt = pf.get("amount", 0)
            payment_map.setdefault(name, {"count": 0, "total": 0})
            payment_map[name]["count"] += 1
            payment_map[name]["total"] += amt

    delivery_names = {"UberEats", "Rappi", "PedidosYa", "Didi Food", "Cornershop", "iFood", "Mercat"}
    channels = {"Salon": {"orders": 0, "total": 0}, "Delivery": {"orders": 0, "total": 0}}
    delivery_detail = {}
    for o in data:
        is_delivery = False
        for pf in o.get("paymentForms", []):
            pname = pf.get("name", "")
            if pname in delivery_names:
                is_delivery = True
                delivery_detail.setdefault(pname, {"orders": 0, "total": 0})
                delivery_detail[pname]["orders"] += 1
                delivery_detail[pname]["total"] += pf.get("amount", 0)
        ch = "Delivery" if is_delivery else "Salon"
        channels[ch]["orders"] += 1
        channels[ch]["total"] += o.get("total", 0)

    families, products = {}, {}
    for o in data:
        for p in o.get("products", []):
            h = p.get("hierarchyName", "Otro")
            pname = p.get("name", "?")
            qty = p.get("quantity", 1)
            payed = p.get("payed", 0)
            cost = p.get("totalCost", 0)
            families.setdefault(h, {"qty": 0, "revenue": 0, "cost": 0})
            families[h]["qty"] += qty
            families[h]["revenue"] += payed
            families[h]["cost"] += cost
            products.setdefault(pname, {"qty": 0, "revenue": 0, "cost": 0, "family": h})
            products[pname]["qty"] += qty
            products[pname]["revenue"] += payed
            products[pname]["cost"] += cost

    hourly = {}
    for o in data:
        dt = o.get("dateOpen", "")
        if "T" in dt:
            h = int(dt.split("T")[1][:2])
            hourly.setdefault(h, {"orders": 0, "total": 0})
            hourly[h]["orders"] += 1
            hourly[h]["total"] += o.get("total", 0)

    waiters = {}
    for o in data:
        wn = o.get("waiterName", "N/A")
        waiters.setdefault(wn, {"orders": 0, "total": 0, "clients": 0, "tip": 0})
        waiters[wn]["orders"] += 1
        waiters[wn]["total"] += o.get("total", 0)
        waiters[wn]["clients"] += o.get("numberClients", 0)
        waiters[wn]["tip"] += o.get("gratuity", 0)

    return dict(
        total_sales=total_sales, total_gratuity=total_gratuity, total_discounts=total_discounts,
        total_cost=total_cost, total_clients=total_clients, num_orders=num_orders,
        avg_ticket=avg_ticket, avg_per_client=avg_per_client, margin=margin,
        payments=payment_map, channels=channels, delivery_detail=delivery_detail,
        families=families, products=products, hourly=hourly, waiters=waiters,
    )


# ── Session State & Sidebar ──

def init_session_state():
    for k in ["messages", "toteat_client", "anthropic_client"]:
        if k not in st.session_state:
            st.session_state[k] = [] if k == "messages" else None

def setup_sidebar():
    with st.sidebar:
        st.markdown("### Conexion Toteat")
        tt = st.text_input("Token", value=os.getenv("TOTEAT_API_TOKEN", ""), type="password")
        ri = st.text_input("Restaurant ID", value=os.getenv("TOTEAT_RESTAURANT_ID", ""))
        li = st.text_input("Local ID", value=os.getenv("TOTEAT_LOCAL_ID", "1"))
        ui = st.text_input("User ID", value=os.getenv("TOTEAT_USER_ID", ""))
        bu = st.text_input("Base URL", value=os.getenv("TOTEAT_BASE_URL", "https://api.toteat.com/mw/or/1.0/"))
        if tt and ri and ui:
            st.session_state.toteat_client = ToteatAPI(api_token=tt, restaurant_id=ri, local_id=li, user_id=ui, base_url=bu)
        st.markdown("---")
        st.markdown("### Chat IA")
        ak = st.text_input("Anthropic API Key", value=os.getenv("ANTHROPIC_API_KEY", ""), type="password")
        if ak:
            try:
                import anthropic
                st.session_state.anthropic_client = anthropic.Anthropic(api_key=ak)
            except Exception:
                pass
        else:
            st.session_state.anthropic_client = None


# ──────────────────────────────────────────────
# DASHBOARD
# ──────────────────────────────────────────────

def render_dashboard():
    client = st.session_state.toteat_client
    if not client:
        st.markdown(f"""<div style="text-align:center;padding:80px 20px;">
            <div style="font-size:3rem;">🍽️</div>
            <div style="font-size:1.2rem;font-weight:700;color:{TEXT_PRIMARY};margin-top:12px;">Conecta tu restaurante</div>
            <div style="color:{TEXT_SECONDARY};margin-top:8px;">Abre la barra lateral e ingresa tus credenciales de Toteat</div>
        </div>""", unsafe_allow_html=True)
        return

    today = date.today()

    # ── Header Toteat ──
    st.markdown(f"""<div class="toteat-header">
        <div class="toteat-brand">
            <div class="toteat-logo-icon">t</div>
            <div>
                <div class="toteat-title">tot<span>eat</span> Intelligence</div>
                <div class="toteat-subtitle">Panel de control de tu restaurante</div>
            </div>
        </div>
        <div class="toteat-date">{today.strftime('%A %d de %B, %Y')}</div>
    </div>""", unsafe_allow_html=True)

    # ══════════════════════════════════════════
    # VENTAS (arriba de todo)
    # ══════════════════════════════════════════
    sec("💰", "Analisis de Ventas")

    col_f, col_t, col_cmp, col_b = st.columns([2, 2, 2, 1])
    with col_f:
        sf = st.date_input("Desde", value=today, key="sf")
    with col_t:
        st2 = st.date_input("Hasta", value=today, key="st")
    with col_cmp:
        compare_opt = st.selectbox("Comparar con", [
            "Periodo anterior",
            "Mismo periodo mes anterior",
            "Mismo periodo año anterior",
            "Sin comparar",
        ], key="cmp")
    with col_b:
        st.write("")
        st.write("")
        st.button("Actualizar", key="go_sales")

    # Cargar ventas con cache
    with st.spinner("Analizando ventas..."):
        try:
            raw = cached_get_sales(client, sf.isoformat(), st2.isoformat())
            data = raw.get("data", [])
            s = process_sales(data)

            if not s:
                st.info("Sin ventas en este periodo.")
                return

            # ── Cargar periodo comparativo ──
            prev = None
            prev_label = ""
            prev_from = None
            prev_to = None
            period_days = (st2 - sf).days + 1

            if compare_opt == "Periodo anterior":
                prev_to = sf - timedelta(days=1)
                prev_from = prev_to - timedelta(days=period_days - 1)
            elif compare_opt == "Mismo periodo mes anterior":
                prev_from = _subtract_months(sf, 1)
                prev_to = _subtract_months(st2, 1)
            elif compare_opt == "Mismo periodo año anterior":
                prev_from = _subtract_years(sf, 1)
                prev_to = _subtract_years(st2, 1)

            if prev_from and prev_to:
                prev_label = f"vs {prev_from.strftime('%d/%m/%Y')} - {prev_to.strftime('%d/%m/%Y')}"
                try:
                    raw_prev = cached_get_sales(client, prev_from.isoformat(), prev_to.isoformat())
                    data_prev = raw_prev.get("data", [])
                    prev = process_sales(data_prev)
                    if not prev:
                        st.caption(f"Comparando {prev_label} — sin datos en el periodo anterior")
                except Exception as e:
                    st.caption(f"Comparando {prev_label} — no se pudo obtener datos: {e}")
                    prev = None

            # Deltas (% y monto absoluto)
            d_sales = calc_delta(s["total_sales"], prev["total_sales"]) if prev else None
            a_sales = (s["total_sales"] - prev["total_sales"]) if prev else None
            d_orders = calc_delta(s["num_orders"], prev["num_orders"]) if prev else None
            a_orders = (s["num_orders"] - prev["num_orders"]) if prev else None
            d_ticket = calc_delta(s["avg_ticket"], prev["avg_ticket"]) if prev else None
            a_ticket = (s["avg_ticket"] - prev["avg_ticket"]) if prev else None
            d_clients = calc_delta(s["total_clients"], prev["total_clients"]) if prev else None
            a_clients = (s["total_clients"] - prev["total_clients"]) if prev else None
            d_margin = calc_delta(s["margin"], prev["margin"]) if prev else None
            d_tips = calc_delta(s["total_gratuity"], prev["total_gratuity"]) if prev else None
            a_tips = (s["total_gratuity"] - prev["total_gratuity"]) if prev else None

            if prev_label:
                st.markdown(f"<div style='font-size:0.78rem;color:#6b7280;margin-bottom:8px;font-weight:600;'>Comparando {prev_label}</div>", unsafe_allow_html=True)

            # ── KPIs ──
            c1, c2, c3, c4, c5, c6 = st.columns(6)
            with c1:
                st.markdown(kpi("💵", "Venta Neta", fmt(s["total_sales"]), delta=d_sales, delta_abs=a_sales), unsafe_allow_html=True)
            with c2:
                st.markdown(kpi("🧾", "Ordenes", str(s["num_orders"]), delta=d_orders), unsafe_allow_html=True)
            with c3:
                st.markdown(kpi("🎫", "Ticket Prom.", fmt(s["avg_ticket"]), delta=d_ticket, delta_abs=a_ticket), unsafe_allow_html=True)
            with c4:
                st.markdown(kpi("👥", "Clientes", str(s["total_clients"]),
                                f"{fmt(s['avg_per_client'])} x persona", delta=d_clients), unsafe_allow_html=True)
            with c5:
                st.markdown(kpi("📊", "Margen", fmt_pct(s["margin"]),
                                f"Costo: {fmt(s['total_cost'])}", "warn" if s["margin"] < 60 else "normal",
                                delta=d_margin), unsafe_allow_html=True)
            with c6:
                st.markdown(kpi("💝", "Propinas", fmt(s["total_gratuity"]),
                                f"Desc: {fmt(s['total_discounts'])}" if s["total_discounts"] else None,
                                "red" if s["total_discounts"] > 0 else "normal",
                                delta=d_tips, delta_abs=a_tips), unsafe_allow_html=True)

            st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

            # ── Row 1: Ventas x Hora + Formas de Pago ──
            ch1, ch2 = st.columns(2)

            with ch1:
                if s["hourly"]:
                    df_h = pd.DataFrame([{"Hora": h, "Venta": v["total"], "Ordenes": v["orders"]}
                                         for h, v in sorted(s["hourly"].items())])
                    fig = go.Figure(go.Bar(
                        x=df_h["Hora"].apply(lambda x: f"{x}:00"),
                        y=df_h["Venta"],
                        marker=dict(color=df_h["Venta"], colorscale=COLOR_SCALE, cornerradius=4),
                        hovertemplate="<b>%{x}</b><br>Venta: $%{y:,.0f}<extra></extra>",
                    ))
                    fig.update_layout(title="Ventas por Hora", height=300, **PLOTLY_LAYOUT)
                    st.plotly_chart(fig, use_container_width=True)

            with ch2:
                if s["payments"]:
                    df_p = pd.DataFrame([{"Metodo": k, "Total": v["total"], "Qty": v["count"]}
                                         for k, v in s["payments"].items()]).sort_values("Total", ascending=False)
                    fig = go.Figure(go.Pie(
                        labels=df_p["Metodo"], values=df_p["Total"],
                        hole=0.55, textinfo="label+percent", textfont=dict(color="#1a1a1a", size=12), textposition="outside",
                        marker=dict(colors=CHART_COLORS),
                        hovertemplate="<b>%{label}</b><br>$%{value:,.0f}<br>%{percent}<extra></extra>",
                    ))
                    fig.update_layout(title="Formas de Pago", height=300, showlegend=False, **PLOTLY_LAYOUT)
                    st.plotly_chart(fig, use_container_width=True)

            # ── Row 2: Familias + Canales ──
            ch3, ch4 = st.columns(2)

            with ch3:
                if s["families"]:
                    df_f = pd.DataFrame([{"Familia": k, "Venta": v["revenue"], "Qty": v["qty"],
                                          "Costo": v["cost"]} for k, v in s["families"].items()])
                    df_f["Margen"] = ((df_f["Venta"] - df_f["Costo"]) / df_f["Venta"] * 100).round(1)
                    df_f = df_f.sort_values("Venta", ascending=True).tail(15)

                    fig = go.Figure(go.Bar(
                        y=df_f["Familia"], x=df_f["Venta"], orientation="h",
                        marker=dict(color=df_f["Venta"], colorscale=COLOR_SCALE, cornerradius=4),
                        hovertemplate="<b>%{y}</b><br>$%{x:,.0f}<extra></extra>",
                    ))
                    fig.update_layout(title="Top 15 Familias de Producto", height=420, **PLOTLY_LAYOUT)
                    st.plotly_chart(fig, use_container_width=True)

            with ch4:
                # Salon vs Delivery
                salon_t = s["channels"]["Salon"]["total"]
                deliv_t = s["channels"]["Delivery"]["total"]
                salon_o = s["channels"]["Salon"]["orders"]
                deliv_o = s["channels"]["Delivery"]["orders"]
                total_all = salon_t + deliv_t

                # Donut canal
                fig = go.Figure(go.Pie(
                    labels=["Salon", "Delivery"],
                    values=[salon_t, deliv_t],
                    hole=0.6, textinfo="label+percent", textfont=dict(color="#1a1a1a", size=12),
                    marker=dict(colors=[TOTEAT_RED, WARNING]),
                    hovertemplate="<b>%{label}</b><br>$%{value:,.0f}<br>%{percent}<extra></extra>",
                ))
                fig.update_layout(title="Salon vs Delivery", height=280, showlegend=False, **PLOTLY_LAYOUT)
                st.plotly_chart(fig, use_container_width=True)

                # Detalle delivery
                if s["delivery_detail"]:
                    df_del = pd.DataFrame([{"Canal": k, "Ordenes": v["orders"], "Venta": v["total"]}
                                           for k, v in s["delivery_detail"].items()]).sort_values("Venta", ascending=False)
                    colors_del = [WARNING, "#ef4444", "#8b5cf6", "#ec4899", "#06b6d4", "#84cc16"]
                    fig2 = go.Figure(go.Bar(
                        x=df_del["Canal"], y=df_del["Venta"],
                        marker=dict(color=colors_del[:len(df_del)], cornerradius=4),
                        text=df_del.apply(lambda r: f"{r['Ordenes']} ord. · {fmt(r['Venta'])}", axis=1),
                        textposition="outside", textfont=dict(color="#374151", size=11),
                        hovertemplate="<b>%{x}</b><br>$%{y:,.0f}<extra></extra>",
                    ))
                    layout = {**PLOTLY_LAYOUT}
                    layout["margin"] = dict(l=16, r=16, t=40, b=16)
                    fig2.update_layout(title="Detalle por Canal Delivery", height=300,
                                       yaxis_range=[0, df_del["Venta"].max() * 1.25], **layout)
                    st.plotly_chart(fig2, use_container_width=True)

            # ── Top Productos ──
            sec("🏆", "Top 15 Productos")
            if s["products"]:
                df_prod = pd.DataFrame([{"Producto": k, "Cantidad": v["qty"], "Venta": v["revenue"],
                                         "Costo": v["cost"], "Familia": v["family"]} for k, v in s["products"].items()])
                df_prod["Margen %"] = ((df_prod["Venta"] - df_prod["Costo"]) / df_prod["Venta"] * 100).round(1)
                df_prod = df_prod.sort_values("Venta", ascending=False).head(15)

                fig = go.Figure(go.Bar(
                    x=df_prod["Producto"], y=df_prod["Venta"],
                    marker=dict(color=df_prod["Venta"], colorscale=COLOR_SCALE, cornerradius=4),
                    text=df_prod["Cantidad"].apply(lambda x: f"{x} unidades"),
                    textposition="outside", textfont=dict(color="#374151", size=11),
                    hovertemplate="<b>%{x}</b><br>$%{y:,.0f}<extra></extra>",
                ))
                fig.update_layout(height=340, **PLOTLY_LAYOUT, xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)

                with st.expander("Ver tabla de productos con margen"):
                    ds = df_prod.copy()
                    ds["Venta"] = ds["Venta"].apply(fmt_full)
                    ds["Costo"] = ds["Costo"].apply(fmt_full)
                    st.dataframe(ds, use_container_width=True, hide_index=True)

            # ── Meseros ──
            sec("👨‍🍳", "Performance por Mesero")
            if s["waiters"]:
                df_w = pd.DataFrame([{"Mesero": k, "Ordenes": v["orders"], "Venta": v["total"],
                                      "Clientes": v["clients"], "Propina": v["tip"]}
                                     for k, v in s["waiters"].items() if k != "N/A"])
                if not df_w.empty:
                    df_w["Ticket Prom."] = (df_w["Venta"] / df_w["Ordenes"]).round(0)
                    df_w = df_w.sort_values("Venta", ascending=True)

                    fig = go.Figure(go.Bar(
                        y=df_w["Mesero"], x=df_w["Venta"], orientation="h",
                        marker=dict(color=df_w["Venta"], colorscale=COLOR_SCALE, cornerradius=4),
                        hovertemplate="<b>%{y}</b><br>$%{x:,.0f}<extra></extra>",
                    ))
                    fig.update_layout(title="Ranking de Ventas", height=max(280, len(df_w)*40), **PLOTLY_LAYOUT)
                    st.plotly_chart(fig, use_container_width=True)

                    best = df_w.iloc[-1]
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.markdown(kpi("🥇", "Top Mesero", best["Mesero"], f"Venta: {fmt(best['Venta'])}"), unsafe_allow_html=True)
                    with c2:
                        st.markdown(kpi("👥", "Total Clientes", str(int(df_w["Clientes"].sum()))), unsafe_allow_html=True)
                    with c3:
                        st.markdown(kpi("🎫", "Mejor Ticket", fmt(best["Ticket Prom."])), unsafe_allow_html=True)

                    with st.expander("Ver tabla de meseros"):
                        ws = df_w.sort_values("Venta", ascending=False).copy()
                        for col in ["Venta", "Propina", "Ticket Prom."]:
                            ws[col] = ws[col].apply(fmt_full)
                        st.dataframe(ws, use_container_width=True, hide_index=True)

            # ── Formas de pago detalle ──
            with st.expander("Ver detalle formas de pago"):
                if s["payments"]:
                    df_pay = pd.DataFrame([{"Forma de Pago": k, "Transacciones": v["count"],
                                            "Total": v["total"]} for k, v in s["payments"].items()])
                    df_pay = df_pay.sort_values("Total", ascending=False)
                    df_pay["% del Total"] = (df_pay["Total"] / df_pay["Total"].sum() * 100).round(1).apply(lambda x: f"{x}%")
                    df_pay["Total"] = df_pay["Total"].apply(fmt_full)
                    st.dataframe(df_pay, use_container_width=True, hide_index=True)

        except Exception as e:
            st.error(f"Error: {e}")

    # ══════════════════════════════════════════
    # ESTADO EN VIVO (Turno + Mesas)
    # ══════════════════════════════════════════
    sec("🏪", "Estado en Vivo")

    shift_data, table_data = {}, []
    try:
        shift_data = cached_get_shift(client).get("data", {})
    except Exception:
        pass
    try:
        table_data = cached_get_tables(client).get("data", [])
    except Exception:
        pass

    total_t = len(table_data)
    avail_t = sum(1 for t in table_data if t.get("available"))
    occup_t = total_t - avail_t
    occup_pct = round(occup_t / total_t * 100) if total_t else 0

    shift_status = shift_data.get("status", "closed")
    shift_time = ""
    sd = shift_data.get("date", "")
    if sd and "T" in sd:
        shift_time = sd.split("T")[1][:5]

    badge = '<span class="badge-open">ABIERTO</span>' if shift_status == "open" else '<span class="badge-closed">CERRADO</span>'

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(kpi("🏪", "Turno", badge, f"Desde {shift_time}" if shift_time else None), unsafe_allow_html=True)
    with c2:
        st.markdown(kpi("🪑", "Ocupacion", f"{occup_t}/{total_t}",
                        f"{occup_pct}% ocupado", "warn" if occup_pct > 75 else "normal"), unsafe_allow_html=True)
    with c3:
        st.markdown(kpi("✅", "Disponibles", str(avail_t)), unsafe_allow_html=True)
    with c4:
        total_cap = sum(t.get("capacity", 0) for t in table_data)
        st.markdown(kpi("👥", "Capacidad Total", str(total_cap), f"{total_t} mesas"), unsafe_allow_html=True)

    if table_data:
        by_sector = {}
        for t in table_data:
            s = t.get("sectorName", "General")
            by_sector.setdefault(s, {"total": 0, "available": 0, "capacity": 0})
            by_sector[s]["total"] += 1
            if t.get("available"):
                by_sector[s]["available"] += 1
            by_sector[s]["capacity"] += t.get("capacity", 0)
        if len(by_sector) > 1:
            with st.expander("Ver ocupacion por sector"):
                rows = [{"Sector": sn, "Mesas": sv["total"], "Ocupadas": sv["total"]-sv["available"],
                         "Libres": sv["available"], "Ocupacion": f"{round((sv['total']-sv['available'])/sv['total']*100)}%",
                         "Capacidad": sv["capacity"]} for sn, sv in by_sector.items()]
                st.dataframe(rows, use_container_width=True, hide_index=True)

    # ══════════════════════════════════════════
    # DOCUMENTOS FISCALES
    # ══════════════════════════════════════════
    sec("📄", "Documentos Fiscales")
    try:
        with st.spinner("Cargando documentos fiscales..."):
            raw_fiscal = cached_get_fiscal_docs(client, sf.isoformat(), st2.isoformat())
            if isinstance(raw_fiscal, list):
                fiscal_data = raw_fiscal
            elif isinstance(raw_fiscal, dict):
                fiscal_data = raw_fiscal.get("data", [])
            else:
                fiscal_data = []

            if fiscal_data:
                total_docs = len(fiscal_data)
                boletas = [d for d in fiscal_data if d.get("type", d.get("documentType", "")).lower() in ("boleta", "receipt", "ticket")]
                facturas = [d for d in fiscal_data if d.get("type", d.get("documentType", "")).lower() in ("factura", "invoice")]
                # Si no se clasificaron, intentar por otro campo
                if not boletas and not facturas:
                    for d in fiscal_data:
                        dtype = str(d.get("type", d.get("documentType", ""))).lower()
                        if "boleta" in dtype or "receipt" in dtype or "ticket" in dtype:
                            boletas.append(d)
                        elif "factura" in dtype or "invoice" in dtype:
                            facturas.append(d)
                        else:
                            boletas.append(d)  # Por defecto a boletas

                total_boletas = len(boletas)
                total_facturas = len(facturas)
                monto_boletas = sum(d.get("total", d.get("amount", 0)) for d in boletas)
                monto_facturas = sum(d.get("total", d.get("amount", 0)) for d in facturas)
                monto_total = monto_boletas + monto_facturas

                # KPIs
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    st.markdown(kpi("📄", "Total Documentos", str(total_docs)), unsafe_allow_html=True)
                with c2:
                    st.markdown(kpi("🧾", "Boletas", str(total_boletas), f"{fmt(monto_boletas)}"), unsafe_allow_html=True)
                with c3:
                    st.markdown(kpi("📑", "Facturas", str(total_facturas), f"{fmt(monto_facturas)}"), unsafe_allow_html=True)
                with c4:
                    st.markdown(kpi("💰", "Monto Total", fmt(monto_total)), unsafe_allow_html=True)

                st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

                # Graficos: Pie por cantidad y por monto
                ch1, ch2 = st.columns(2)
                with ch1:
                    if total_boletas or total_facturas:
                        fig = go.Figure(go.Pie(
                            labels=["Boletas", "Facturas"],
                            values=[total_boletas, total_facturas],
                            hole=0.55, textinfo="label+percent+value",
                            textfont=dict(color="#1a1a1a", size=12), textposition="outside",
                            marker=dict(colors=[TOTEAT_RED, "#1a1a1a"]),
                            hovertemplate="<b>%{label}</b><br>%{value} docs<br>%{percent}<extra></extra>",
                        ))
                        fig.update_layout(title="Documentos por Tipo (Cantidad)", height=300, showlegend=False, **PLOTLY_LAYOUT)
                        st.plotly_chart(fig, use_container_width=True)

                with ch2:
                    if monto_boletas or monto_facturas:
                        fig = go.Figure(go.Pie(
                            labels=["Boletas", "Facturas"],
                            values=[monto_boletas, monto_facturas],
                            hole=0.55, textinfo="label+percent",
                            textfont=dict(color="#1a1a1a", size=12), textposition="outside",
                            marker=dict(colors=[TOTEAT_RED, "#1a1a1a"]),
                            hovertemplate="<b>%{label}</b><br>$%{value:,.0f}<br>%{percent}<extra></extra>",
                        ))
                        fig.update_layout(title="Documentos por Tipo (Monto)", height=300, showlegend=False, **PLOTLY_LAYOUT)
                        st.plotly_chart(fig, use_container_width=True)

                # Tabla detalle
                with st.expander("Ver detalle de documentos fiscales"):
                    rows_fiscal = []
                    for d in fiscal_data:
                        rows_fiscal.append({
                            "Fecha": str(d.get("date", d.get("createdAt", "")))[:16].replace("T", " "),
                            "Tipo": d.get("type", d.get("documentType", "N/A")),
                            "Numero": d.get("number", d.get("documentNumber", d.get("folio", "N/A"))),
                            "Monto": fmt_full(d.get("total", d.get("amount", 0))),
                        })
                    if rows_fiscal:
                        st.dataframe(rows_fiscal, use_container_width=True, hide_index=True)
            else:
                st.info("Sin documentos fiscales en este periodo.")
    except Exception as e:
        st.error(f"Error al cargar documentos fiscales: {e}")

    # ── Menu ──
    sec("📋", "Menu del Restaurante")
    try:
        with st.spinner(""):
            products = cached_get_products(client)
            data = products.get("data", products)
            if isinstance(data, list):
                for cat in data:
                    cn = cat.get("categoryName", cat.get("name", "?"))
                    items = cat.get("products", cat.get("items", []))
                    if items:
                        with st.expander(f"**{cn}** — {len(items)} productos"):
                            rows = [{"Producto": p.get("productName", p.get("name", "")),
                                     "Precio": fmt_full(p.get("price", p.get("productPrice", 0))),
                                     "Estado": "Disponible" if p.get("available", p.get("active", True)) else "No disponible"}
                                    for p in items]
                            st.dataframe(rows, use_container_width=True, hide_index=True)
    except Exception as e:
        st.error(f"Error: {e}")

    # ══════════════════════════════════════════
    # RECAUDACION / CAJA
    # ══════════════════════════════════════════
    sec("💰", "Recaudacion del Dia")
    try:
        col_coll_date, col_coll_btn = st.columns([3, 1])
        with col_coll_date:
            coll_date = st.date_input("Dia de recaudacion", value=today, key="coll_date")
        with col_coll_btn:
            st.write("")
            st.write("")
            st.button("Consultar", key="go_coll")

        with st.spinner("Consultando recaudacion..."):
            # Obtener medios de pago desde las ventas del dia
            raw_coll_sales = cached_get_sales(client, coll_date.isoformat(), coll_date.isoformat())
            coll_sales_data = raw_coll_sales.get("data", [])

            # Obtener info de cajas desde collection API
            raw_coll = cached_get_collection(client, coll_date.isoformat())
            coll_data = raw_coll.get("data", raw_coll) if isinstance(raw_coll, dict) else raw_coll

            # Extraer medios de pago desde ventas
            payment_methods = {}
            total_recaudado = 0
            for order in coll_sales_data:
                for pf in order.get("paymentForms", []):
                    method = pf.get("name", "Otro")
                    amount = float(pf.get("amount", 0))
                    payment_methods[method] = payment_methods.get(method, 0) + amount
                    total_recaudado += amount

            # Extraer info de cajas desde collection
            cajas_info = []
            if isinstance(coll_data, dict):
                shifts = coll_data.get("shifts", {})
                for shift_id, shift in shifts.items():
                    shift_name = shift.get("name", f"Turno {shift_id}")
                    registers = shift.get("registers", {})
                    for reg_id, reg_list in registers.items():
                        if isinstance(reg_list, list):
                            for reg in reg_list:
                                cajas_info.append({
                                    "Turno": shift_name,
                                    "Caja": reg.get("registerName", f"Caja {reg_id}"),
                                    "Apertura": reg.get("openedDate", "")[:16].replace("T", " "),
                                    "Cierre": reg.get("closedDate", "")[:16].replace("T", " ") if reg.get("closedDate") else "Abierta",
                                })

            if not coll_sales_data:
                st.info("Sin ventas registradas para este dia.")
            else:
                # KPIs
                num_medios = len(payment_methods)
                num_ordenes = len(coll_sales_data)
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    st.markdown(kpi("💰", "Total Recaudado", fmt(total_recaudado)), unsafe_allow_html=True)
                with c2:
                    st.markdown(kpi("🧾", "Ordenes del Dia", str(num_ordenes)), unsafe_allow_html=True)
                with c3:
                    st.markdown(kpi("💳", "Medios de Pago", str(num_medios)), unsafe_allow_html=True)
                with c4:
                    top_method = max(payment_methods, key=payment_methods.get) if payment_methods else "N/A"
                    top_amount = payment_methods.get(top_method, 0) if payment_methods else 0
                    st.markdown(kpi("🥇", "Medio Principal", top_method, f"{fmt(top_amount)}"), unsafe_allow_html=True)

                if payment_methods and len(payment_methods) > 1:
                    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
                    ch_coll1, ch_coll2 = st.columns(2)

                    with ch_coll1:
                        df_coll = pd.DataFrame([{"Medio de Pago": k, "Monto": v} for k, v in payment_methods.items()])
                        df_coll = df_coll.sort_values("Monto", ascending=False)
                        fig = go.Figure(go.Pie(
                            labels=df_coll["Medio de Pago"], values=df_coll["Monto"],
                            hole=0.55, textinfo="label+percent", textfont=dict(color="#1a1a1a", size=12),
                            textposition="outside",
                            marker=dict(colors=CHART_COLORS),
                            hovertemplate="<b>%{label}</b><br>$%{value:,.0f}<br>%{percent}<extra></extra>",
                        ))
                        fig.update_layout(title="Recaudacion por Medio de Pago", height=340, showlegend=False, **PLOTLY_LAYOUT)
                        st.plotly_chart(fig, use_container_width=True)

                    with ch_coll2:
                        df_coll_display = df_coll.copy()
                        df_coll_display["% del Total"] = (df_coll_display["Monto"] / df_coll_display["Monto"].sum() * 100).round(1).apply(lambda x: f"{x}%")
                        df_coll_display["Monto"] = df_coll_display["Monto"].apply(fmt_full)
                        st.dataframe(df_coll_display, use_container_width=True, hide_index=True)

            if cajas_info:
                with st.expander("Ver detalle de cajas"):
                    st.dataframe(cajas_info, use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Error al cargar recaudacion: {e}")

    # ══════════════════════════════════════════
    # INVENTARIO
    # ══════════════════════════════════════════
    sec("📦", "Estado de Inventario")
    try:
        with st.spinner("Consultando inventario..."):
            raw_inv = cached_get_inventory(client, sf.isoformat(), st2.isoformat())
            inv_data = raw_inv.get("data", raw_inv) if isinstance(raw_inv, dict) else raw_inv

            if not inv_data:
                st.info("Sin datos de inventario para este periodo.")
            else:
                items_list = []
                if isinstance(inv_data, list):
                    items_list = inv_data
                elif isinstance(inv_data, dict):
                    items_list = inv_data.get("items", inv_data.get("movements", inv_data.get("products", [])))
                    if not items_list and isinstance(inv_data, dict):
                        items_list = [inv_data]

                total_items = len(items_list)
                total_movements = 0
                low_stock_items = []

                rows_inv = []
                for item in items_list:
                    name = item.get("productName", item.get("name", item.get("product", "?")))
                    stock = item.get("stock", item.get("currentStock", item.get("quantity", 0)))
                    min_stock = item.get("minStock", item.get("minimumStock", item.get("reorderPoint", 0)))
                    movements = item.get("movements", item.get("totalMovements", 0))
                    unit = item.get("unit", item.get("unitName", ""))

                    if isinstance(movements, (int, float)):
                        total_movements += abs(int(movements))
                    elif isinstance(movements, list):
                        total_movements += len(movements)

                    try:
                        stock_val = float(stock)
                        min_val = float(min_stock) if min_stock else 0
                        if min_val > 0 and stock_val <= min_val:
                            low_stock_items.append(name)
                        estado = "Bajo" if (min_val > 0 and stock_val <= min_val) else "Normal"
                    except (ValueError, TypeError):
                        stock_val = stock
                        estado = "?"

                    rows_inv.append({
                        "Producto": name,
                        "Stock Actual": stock,
                        "Stock Minimo": min_stock if min_stock else "-",
                        "Unidad": unit,
                        "Estado": estado,
                    })

                # KPIs
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.markdown(kpi("📦", "Items en Inventario", str(total_items)), unsafe_allow_html=True)
                with c2:
                    sub_low = f"{len(low_stock_items)} items bajo minimo" if low_stock_items else "Todo en orden"
                    sub_type_low = "red" if low_stock_items else "normal"
                    st.markdown(kpi("⚠️", "Stock Bajo", str(len(low_stock_items)), sub_low, sub_type_low), unsafe_allow_html=True)
                with c3:
                    st.markdown(kpi("🔄", "Movimientos", str(total_movements)), unsafe_allow_html=True)

                # Alerta de items con stock bajo
                if low_stock_items:
                    st.markdown(
                        f"<div style='background:{WARNING_BG};border:1px solid {WARNING}30;border-radius:10px;"
                        f"padding:12px 16px;margin:10px 0;font-size:0.85rem;color:#92400e;'>"
                        f"<strong>Atencion:</strong> Los siguientes items podrian estar por agotarse: "
                        f"<strong>{', '.join(low_stock_items[:10])}</strong>"
                        f"{'...' if len(low_stock_items) > 10 else ''}. "
                        f"Se recomienda revisar proveedores y programar reposicion.</div>",
                        unsafe_allow_html=True,
                    )

                if rows_inv:
                    with st.expander("Ver tabla de inventario"):
                        st.dataframe(rows_inv, use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Error al cargar inventario: {e}")

    # ══════════════════════════════════════════
    # MOVIMIENTOS CONTABLES
    # ══════════════════════════════════════════
    sec("📒", "Movimientos Contables")
    try:
        with st.spinner("Consultando movimientos contables..."):
            raw_acc = cached_get_accounting(client, sf.isoformat(), st2.isoformat())
            acc_data = raw_acc.get("data", raw_acc) if isinstance(raw_acc, dict) else raw_acc

            if not acc_data:
                st.info("Sin movimientos contables para este periodo.")
            else:
                mov_list = []
                if isinstance(acc_data, list):
                    mov_list = acc_data
                elif isinstance(acc_data, dict):
                    mov_list = acc_data.get("movements", acc_data.get("items", acc_data.get("data", [])))
                    if not mov_list and isinstance(acc_data, dict):
                        mov_list = [acc_data]

                total_ingresos = 0
                total_egresos = 0
                rows_acc = []

                for mov in mov_list:
                    concepto = mov.get("concept", mov.get("description", mov.get("name", "?")))
                    tipo = mov.get("type", mov.get("movementType", mov.get("category", "")))
                    monto = float(mov.get("amount", mov.get("total", 0)))
                    fecha = mov.get("date", mov.get("createdAt", ""))

                    is_ingreso = tipo.lower() in ("ingreso", "income", "in", "credit", "venta", "sale") if isinstance(tipo, str) and tipo else monto >= 0

                    if is_ingreso:
                        total_ingresos += abs(monto)
                    else:
                        total_egresos += abs(monto)

                    rows_acc.append({
                        "Fecha": str(fecha)[:10] if len(str(fecha)) >= 10 else str(fecha),
                        "Concepto": concepto,
                        "Tipo": "Ingreso" if is_ingreso else "Egreso",
                        "Monto": fmt_full(abs(monto)),
                    })

                balance = total_ingresos - total_egresos

                # KPIs
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.markdown(kpi("📈", "Total Ingresos", fmt(total_ingresos)), unsafe_allow_html=True)
                with c2:
                    st.markdown(kpi("📉", "Total Egresos", fmt(total_egresos)), unsafe_allow_html=True)
                with c3:
                    balance_sub = "Positivo" if balance >= 0 else "Negativo"
                    balance_type = "normal" if balance >= 0 else "red"
                    st.markdown(kpi("💹", "Balance Neto", fmt(balance), balance_sub, balance_type), unsafe_allow_html=True)

                st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

                # Grafico de barras Ingresos vs Egresos
                if total_ingresos > 0 or total_egresos > 0:
                    fig = go.Figure(data=[
                        go.Bar(
                            x=["Ingresos", "Egresos"],
                            y=[total_ingresos, total_egresos],
                            marker=dict(color=[SUCCESS, DANGER], cornerradius=4),
                            text=[fmt(total_ingresos), fmt(total_egresos)],
                            textposition="outside",
                            textfont=dict(color="#374151", size=12),
                            hovertemplate="<b>%{x}</b><br>$%{y:,.0f}<extra></extra>",
                        )
                    ])
                    fig.update_layout(
                        title="Ingresos vs Egresos",
                        height=320,
                        yaxis_range=[0, max(total_ingresos, total_egresos) * 1.25],
                        **PLOTLY_LAYOUT,
                    )
                    st.plotly_chart(fig, use_container_width=True)

                if rows_acc:
                    with st.expander("Ver tabla de movimientos contables"):
                        st.dataframe(rows_acc, use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Error al cargar movimientos contables: {e}")


# ──────────────────────────────────────────────
# CHAT
# ──────────────────────────────────────────────

def render_chat():
    if not st.session_state.anthropic_client:
        st.markdown(f"""<div style="text-align:center;padding:60px 20px;">
            <div style="font-size:3rem;">🤖</div>
            <div style="font-size:1.2rem;font-weight:700;color:{TEXT_PRIMARY};margin-top:12px;">Chat IA</div>
            <div style="color:{TEXT_SECONDARY};margin-top:8px;">Agrega tu Anthropic API Key en la barra lateral.</div>
        </div>""", unsafe_allow_html=True)
        return
    if not st.session_state.toteat_client:
        st.warning("Configura Toteat primero.")
        return

    import anthropic
    for msg in st.session_state.messages:
        if msg["role"] == "user" and isinstance(msg["content"], str):
            with st.chat_message("user"):
                st.markdown(msg["content"])
        elif msg["role"] == "assistant":
            text = msg["content"] if isinstance(msg["content"], str) else None
            if isinstance(msg["content"], list):
                for block in msg["content"]:
                    if hasattr(block, "text"):
                        text = block.text
                        break
            if text:
                with st.chat_message("assistant"):
                    st.markdown(text)

    if prompt := st.chat_input("Pregunta sobre tu restaurante..."):
        with st.chat_message("user"):
            st.markdown(prompt)
        api_messages = list(st.session_state.messages)
        api_messages.append({"role": "user", "content": prompt})
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("assistant"):
            with st.spinner("Pensando..."):
                try:
                    response = st.session_state.anthropic_client.messages.create(
                        model="claude-sonnet-4-20250514", max_tokens=4096,
                        system=SYSTEM_PROMPT, tools=TOOLS, messages=api_messages)
                    while response.stop_reason == "tool_use":
                        tbs = [b for b in response.content if b.type == "tool_use"]
                        api_messages.append({"role": "assistant", "content": response.content})
                        trs = [{"type": "tool_result", "tool_use_id": tb.id,
                                "content": execute_tool(tb.name, tb.input, st.session_state.toteat_client)} for tb in tbs]
                        api_messages.append({"role": "user", "content": trs})
                        response = st.session_state.anthropic_client.messages.create(
                            model="claude-sonnet-4-20250514", max_tokens=4096,
                            system=SYSTEM_PROMPT, tools=TOOLS, messages=api_messages)
                    answer = next((b.text for b in response.content if hasattr(b, "text")), "Sin respuesta.")
                    st.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                except Exception as e:
                    st.error(f"Error: {e}")


# ──────────────────────────────────────────────
# KPIs GASTRONOMICOS
# ──────────────────────────────────────────────

def _kpi_color(value, green_range, yellow_range):
    """Retorna 'normal', 'warn' o 'red' segun rangos."""
    lo_g, hi_g = green_range
    lo_y, hi_y = yellow_range
    if lo_g <= value <= hi_g:
        return "normal"
    if lo_y <= value <= hi_y:
        return "warn"
    return "red"


def _gauge_chart(title, value, suffix, green_range, red_threshold, max_val=100):
    """Crea un chart tipo gauge con indicador de color."""
    lo_g, hi_g = green_range
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number=dict(suffix=suffix, font=dict(size=28, color=TEXT_PRIMARY, family="Nunito Sans")),
        title=dict(text=title, font=dict(size=13, color=TEXT_PRIMARY, family="Nunito Sans", weight=700)),
        gauge=dict(
            axis=dict(range=[0, max_val], tickfont=dict(size=10, color=TEXT_SECONDARY)),
            bar=dict(color=TOTEAT_RED),
            bgcolor="white",
            borderwidth=1,
            bordercolor=BORDER,
            steps=[
                dict(range=[0, lo_g], color="#fef2f2"),
                dict(range=[lo_g, hi_g], color="#f0fdf4"),
                dict(range=[hi_g, red_threshold], color="#fffbeb"),
                dict(range=[red_threshold, max_val], color="#fef2f2"),
            ],
            threshold=dict(
                line=dict(color=DANGER, width=2),
                thickness=0.75,
                value=red_threshold,
            ),
        ),
    ))
    fig.update_layout(
        height=220,
        margin=dict(l=20, r=20, t=50, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Nunito Sans, Inter, sans-serif"),
    )
    return fig


def render_kpis():
    client = st.session_state.toteat_client
    if not client:
        st.markdown(f"""<div style="text-align:center;padding:80px 20px;">
            <div style="font-size:3rem;">📈</div>
            <div style="font-size:1.2rem;font-weight:700;color:{TEXT_PRIMARY};margin-top:12px;">Conecta tu restaurante</div>
            <div style="color:{TEXT_SECONDARY};margin-top:8px;">Abre la barra lateral e ingresa tus credenciales de Toteat</div>
        </div>""", unsafe_allow_html=True)
        return

    today = date.today()

    # ── Selector de mes ──
    import calendar
    col_hdr, col_month, col_year = st.columns([4, 1, 1])
    with col_hdr:
        st.markdown(f"""<div class="toteat-brand" style="padding:12px 0;">
            <div class="toteat-logo-icon">t</div>
            <div>
                <div class="toteat-title">KPIs <span>Gastronomicos</span></div>
                <div class="toteat-subtitle">Indicadores clave de gestion</div>
            </div>
        </div>""", unsafe_allow_html=True)
    with col_month:
        meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                 "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        kpi_month = st.selectbox("Mes", meses, index=today.month - 1, key="kpi_month")
        selected_month = meses.index(kpi_month) + 1
    with col_year:
        kpi_year = st.number_input("Año", min_value=2020, max_value=today.year,
                                    value=today.year, step=1, key="kpi_year")

    first_of_month = date(kpi_year, selected_month, 1)
    last_day = calendar.monthrange(kpi_year, selected_month)[1]
    end_of_month = date(kpi_year, selected_month, last_day)

    is_current_month = (kpi_year == today.year and selected_month == today.month)
    partial_note = f' — <span style="color:{WARNING};">Mes en curso, datos parciales al {today.strftime("%d/%m")}</span>' if is_current_month else ""

    st.markdown(f"""<div style="font-size:0.8rem;color:{TEXT_SECONDARY};margin-bottom:4px;font-weight:600;">
        Analizando: {kpi_month} {kpi_year} (01 al {last_day}/{selected_month:02d}/{kpi_year}) — {last_day} dias{partial_note}
    </div>""", unsafe_allow_html=True)

    # ══════════════════════════════════════════
    # SECCION 1: INGRESO DE GASTOS MENSUALES
    # ══════════════════════════════════════════
    sec("💸", "Gastos y Parametros del Restaurante")

    uf_val = get_uf_value()
    uf_display = f"${uf_val:,.0f} CLP".replace(",", ".") if uf_val else "No disponible"

    # Cargar config guardada
    config = _load_restaurant_config()

    st.markdown(f"""<div style="font-size:0.8rem;color:{TEXT_SECONDARY};margin-bottom:8px;">
        Valor UF hoy: <b>{uf_display}</b> — Estos datos se guardan automaticamente y persisten entre sesiones.
    </div>""", unsafe_allow_html=True)

    gc1, gc2, gc3, gc4 = st.columns(4)
    with gc1:
        sueldos = st.number_input("Sueldos del mes (CLP)", min_value=0, step=100000,
                                  value=config.get("sueldos", 0), key="input_sueldos")
    with gc2:
        arriendo_uf = st.number_input("Arriendo (UF)", min_value=0.0, step=1.0, format="%.1f",
                                      value=float(config.get("arriendo_uf", 0.0)), key="input_arriendo")
        arriendo_clp = arriendo_uf * uf_val if uf_val else 0
        if arriendo_uf > 0 and uf_val:
            st.caption(f"= {fmt(arriendo_clp)} CLP")
    with gc3:
        servicios = st.number_input("Servicios basicos (CLP)", min_value=0, step=50000,
                                    value=config.get("servicios", 0), key="input_servicios")
    with gc4:
        otros = st.number_input("Otros gastos fijos (CLP)", min_value=0, step=50000,
                                value=config.get("otros", 0), key="input_otros")

    gc5, gc6, gc7, _ = st.columns([1, 1, 1, 1])
    with gc5:
        horas_op = st.number_input("Horas operacion/dia", min_value=1, max_value=24, step=1,
                                   value=config.get("horas_op", 12), key="input_horas")
    with gc6:
        m2 = st.number_input("Metros cuadrados", min_value=1, step=10,
                             value=config.get("m2", 100), key="input_m2")
    with gc7:
        num_empleados = st.number_input("Num. empleados", min_value=1, step=1,
                                        value=config.get("num_empleados", 10), key="input_empleados")

    # Guardar automaticamente si cambiaron los valores
    new_config = {
        "sueldos": sueldos, "arriendo_uf": arriendo_uf, "servicios": servicios,
        "otros": otros, "horas_op": horas_op, "m2": m2, "num_empleados": num_empleados,
    }
    if new_config != config:
        _save_restaurant_config(new_config)

    gastos_fijos = sueldos + arriendo_clp + servicios + otros

    # ── Cargar datos del mes seleccionado ──
    with st.spinner(f"Cargando datos de {kpi_month} {kpi_year}..."):
        try:
            raw = cached_get_sales(client, first_of_month.isoformat(), end_of_month.isoformat())
            data = raw.get("data", [])
            s = process_sales(data)
        except Exception as e:
            st.error(f"Error al cargar ventas: {e}")
            return

        if not s:
            st.info(f"Sin ventas registradas en {kpi_month} {kpi_year}.")
            return

        days_in_period = (end_of_month - first_of_month).days + 1

        # Cargar mesas para capacidad
        table_data = []
        try:
            table_data = cached_get_tables(client).get("data", [])
        except Exception:
            pass

    total_ventas = s["total_sales"]
    total_cost = s["total_cost"]
    num_orders = s["num_orders"]
    total_clients = s["total_clients"]
    total_tables = len(table_data)
    total_seats = sum(t.get("capacity", 0) for t in table_data)
    dias_periodo = (end_of_month - first_of_month).days + 1

    # ══════════════════════════════════════════
    # CALCULOS DE KPIs
    # ══════════════════════════════════════════

    # Financieros
    food_cost_pct = (total_cost / total_ventas * 100) if total_ventas else 0
    labor_cost_pct = (sueldos / total_ventas * 100) if total_ventas else 0
    rent_cost_pct = (arriendo_clp / total_ventas * 100) if total_ventas else 0
    prime_cost_pct = food_cost_pct + labor_cost_pct
    margen_bruto = total_ventas - total_cost
    resultado_op = total_ventas - total_cost - sueldos - arriendo_clp - servicios - otros
    punto_equilibrio = gastos_fijos / (1 - food_cost_pct / 100) if food_cost_pct < 100 else 0

    # Operativos
    ticket_promedio = total_ventas / num_orders if num_orders else 0
    gasto_cliente = total_ventas / total_clients if total_clients else 0
    revpash = total_ventas / (total_seats * horas_op * dias_periodo) if (total_seats and horas_op and dias_periodo) else 0
    rotacion_mesas = num_orders / total_tables if total_tables else 0
    venta_m2 = total_ventas / m2 if m2 else 0

    # ══════════════════════════════════════════
    # SECCION 2: KPIs FINANCIEROS
    # ══════════════════════════════════════════
    sec("💰", "KPIs Financieros")

    # Helper para explicaciones educativas
    def kpi_tip(text):
        st.markdown(f'<div style="font-size:0.7rem;color:{TEXT_SECONDARY};line-height:1.4;margin-top:4px;padding:6px 8px;background:{BORDER_LIGHT};border-radius:6px;">{text}</div>', unsafe_allow_html=True)

    # Gauges
    g1, g2, g3, g4 = st.columns(4)
    with g1:
        fig = _gauge_chart("Food Cost %", round(food_cost_pct, 1), "%",
                           green_range=(28, 35), red_threshold=40)
        st.plotly_chart(fig, use_container_width=True)
        fc_color = _kpi_color(food_cost_pct, (28, 35), (22, 40))
        st.markdown(kpi("🥩", "Food Cost", fmt_pct(food_cost_pct),
                        f"Meta: 28-35% · {fmt(total_cost)}", fc_color), unsafe_allow_html=True)
        kpi_tip("<b>Costo de alimentos sobre ventas.</b> Mide cuanto de cada $100 que vendes se va en ingredientes. Si sube, revisa proveedores, merma o porciones.")

    with g2:
        fig = _gauge_chart("Labor Cost %", round(labor_cost_pct, 1), "%",
                           green_range=(20, 30), red_threshold=35)
        st.plotly_chart(fig, use_container_width=True)
        lc_color = _kpi_color(labor_cost_pct, (20, 30), (15, 35))
        if sueldos == 0:
            st.caption("Ingresa sueldos para calcular Labor Cost")
        else:
            st.markdown(kpi("👨‍🍳", "Labor Cost", fmt_pct(labor_cost_pct),
                            f"Meta: ≤30% · {fmt(sueldos)}", lc_color), unsafe_allow_html=True)
        kpi_tip("<b>Costo de personal sobre ventas.</b> Incluye sueldos, imposiciones y beneficios. Si es muy alto, necesitas vender mas o ajustar dotacion en turnos bajos.")

    with g3:
        fig = _gauge_chart("Rent Cost %", round(rent_cost_pct, 1), "%",
                           green_range=(5, 8), red_threshold=10)
        st.plotly_chart(fig, use_container_width=True)
        rc_color = _kpi_color(rent_cost_pct, (5, 8), (3, 10))
        if arriendo_uf == 0:
            st.caption("Ingresa arriendo para calcular Rent Cost")
        else:
            st.markdown(kpi("🏠", "Rent Cost", fmt_pct(rent_cost_pct),
                            f"Meta: ≤8-10% · {fmt(arriendo_clp)}", rc_color), unsafe_allow_html=True)
        kpi_tip("<b>Costo de arriendo sobre ventas.</b> Si supera el 10%, el local no genera suficiente venta para justificar su ubicacion. Renegociar arriendo o aumentar ventas.")

    with g4:
        fig = _gauge_chart("Prime Cost %", round(prime_cost_pct, 1), "%",
                           green_range=(50, 60), red_threshold=65, max_val=100)
        st.plotly_chart(fig, use_container_width=True)
        pc_color = _kpi_color(prime_cost_pct, (50, 60), (45, 65))
        st.markdown(kpi("📊", "Prime Cost", fmt_pct(prime_cost_pct),
                        "Meta: ≤60-65% (Food+Labor)", pc_color), unsafe_allow_html=True)
        kpi_tip("<b>El KPI mas importante.</b> Suma Food Cost + Labor Cost. Si supera 65%, el negocio no es sostenible. Es la primera alarma que debes mirar cada mes.")

    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

    # Cards financieros
    f1, f2, f3 = st.columns(3)
    with f1:
        st.markdown(kpi("📈", "Margen Bruto", fmt(margen_bruto),
                        f"Ventas: {fmt(total_ventas)} — Costo: {fmt(total_cost)}"), unsafe_allow_html=True)
        kpi_tip("<b>Lo que queda despues de pagar ingredientes.</b> De aqui salen sueldos, arriendo y gastos. Si es bajo, revisa precios de carta o costos de recetas.")
    with f2:
        res_color = "normal" if resultado_op > 0 else "red"
        st.markdown(kpi("🏦", "Resultado Operacional", fmt(resultado_op),
                        f"Gastos fijos: {fmt(gastos_fijos)}", res_color), unsafe_allow_html=True)
        kpi_tip("<b>Ganancia o perdida real del mes.</b> Ventas menos todos los costos (ingredientes + sueldos + arriendo + servicios + otros). Si es negativo, estas perdiendo plata.")
    with f3:
        st.markdown(kpi("⚖️", "Punto de Equilibrio", fmt(punto_equilibrio),
                        "Venta minima para cubrir costos fijos"), unsafe_allow_html=True)
        kpi_tip("<b>Cuanto necesitas vender para no perder.</b> Cada peso por debajo es perdida, cada peso por encima es ganancia. Dividelo por dias del mes para saber tu meta diaria.")

    # Barra de progreso hacia punto de equilibrio
    if punto_equilibrio > 0:
        progreso = min(total_ventas / punto_equilibrio, 1.0)
        progreso_pct = round(progreso * 100, 1)
        bar_color = SUCCESS if progreso >= 1.0 else (WARNING if progreso >= 0.7 else DANGER)
        st.markdown(f"""<div style="margin:12px 0 4px 0;font-size:0.78rem;font-weight:700;color:{TEXT_PRIMARY};">
            Progreso al punto de equilibrio: {progreso_pct}%
        </div>
        <div style="background:{BORDER};border-radius:6px;height:10px;overflow:hidden;">
            <div style="background:{bar_color};width:{min(progreso_pct, 100)}%;height:100%;border-radius:6px;transition:width 0.5s;"></div>
        </div>""", unsafe_allow_html=True)

    # Desglose de costos (pie chart)
    if gastos_fijos > 0 or total_cost > 0:
        st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
        dc1, dc2 = st.columns(2)
        with dc1:
            cost_labels = []
            cost_values = []
            if total_cost > 0:
                cost_labels.append("Costo Ingredientes")
                cost_values.append(total_cost)
            if sueldos > 0:
                cost_labels.append("Sueldos")
                cost_values.append(sueldos)
            if arriendo_clp > 0:
                cost_labels.append("Arriendo")
                cost_values.append(arriendo_clp)
            if servicios > 0:
                cost_labels.append("Servicios")
                cost_values.append(servicios)
            if otros > 0:
                cost_labels.append("Otros")
                cost_values.append(otros)

            if cost_labels:
                fig = go.Figure(go.Pie(
                    labels=cost_labels, values=cost_values,
                    hole=0.55, textinfo="label+percent",
                    textfont=dict(color="#1a1a1a", size=11), textposition="outside",
                    marker=dict(colors=[TOTEAT_RED, "#ff6b61", "#ffa099", WARNING, TEXT_SECONDARY]),
                    hovertemplate="<b>%{label}</b><br>$%{value:,.0f}<br>%{percent}<extra></extra>",
                ))
                fig.update_layout(title="Desglose de Costos", height=300, showlegend=False, **PLOTLY_LAYOUT)
                st.plotly_chart(fig, use_container_width=True)

        with dc2:
            # Waterfall de resultado
            cat_names = ["Ventas", "Food Cost", "Sueldos", "Arriendo", "Servicios", "Otros", "Resultado"]
            cat_values = [total_ventas, -total_cost, -sueldos, -arriendo_clp, -servicios, -otros, resultado_op]
            measures = ["absolute", "relative", "relative", "relative", "relative", "relative", "total"]

            fig = go.Figure(go.Waterfall(
                x=cat_names, y=cat_values, measure=measures,
                connector=dict(line=dict(color=BORDER)),
                increasing=dict(marker=dict(color=SUCCESS)),
                decreasing=dict(marker=dict(color=TOTEAT_RED)),
                totals=dict(marker=dict(color="#1a1a1a" if resultado_op >= 0 else DANGER)),
                textposition="outside",
                text=[fmt(abs(v)) for v in cat_values],
                textfont=dict(size=10, color=TEXT_SECONDARY),
            ))
            fig.update_layout(title="Cascada de Resultado Operacional", height=300, **PLOTLY_LAYOUT)
            st.plotly_chart(fig, use_container_width=True)

    # ══════════════════════════════════════════
    # SECCION 3: KPIs OPERATIVOS
    # ══════════════════════════════════════════
    sec("⚙️", "KPIs Operativos")

    st.markdown(f"""<div style="font-size:0.78rem;color:{TEXT_SECONDARY};margin-bottom:10px;">
        Periodo: {first_of_month.strftime('%d/%m/%Y')} al {end_of_month.strftime('%d/%m/%Y')} ({dias_periodo} dias)
        — {total_seats} asientos en {total_tables} mesas — {horas_op}h diarias — {m2} m²
    </div>""", unsafe_allow_html=True)

    o1, o2, o3, o4 = st.columns(4)
    with o1:
        st.markdown(kpi("🎫", "Ticket Promedio", fmt(ticket_promedio),
                        f"{num_orders} ordenes"), unsafe_allow_html=True)
        kpi_tip("<b>Gasto promedio por cuenta.</b> Subir el ticket es la forma mas facil de aumentar ventas sin mas clientes. Estrategias: sugerencia de postres, maridaje, promociones por mesa.")
    with o2:
        st.markdown(kpi("👤", "Gasto por Cliente", fmt(gasto_cliente),
                        f"{total_clients} clientes"), unsafe_allow_html=True)
        kpi_tip("<b>Cuanto gasta cada persona.</b> A diferencia del ticket (por mesa), este mide por persona. Util para comparar almuerzos (1-2 personas) vs cenas (grupos).")
    with o3:
        revpash_color = "normal" if revpash > 0 else "warn"
        st.markdown(kpi("💺", "RevPASH", fmt(revpash),
                        "Ingreso por asiento por hora", revpash_color), unsafe_allow_html=True)
        kpi_tip("<b>Revenue Per Available Seat Hour.</b> Mide cuanto genera cada asiento por hora. Si es bajo en ciertos turnos, considera promociones en esos horarios o reducir mesas activas.")
    with o4:
        rotacion_str = f"{rotacion_mesas:.1f}"
        st.markdown(kpi("🔄", "Rotacion de Mesas", rotacion_str,
                        f"{num_orders} ordenes / {total_tables} mesas"), unsafe_allow_html=True)
        kpi_tip("<b>Cuantas veces se usa cada mesa.</b> Una rotacion de 2 significa que en promedio cada mesa atendio 2 servicios. Mejorar: reducir tiempos de servicio, optimizar reservas.")

    o5, o6, _, _ = st.columns(4)
    with o5:
        st.markdown(kpi("📐", "Venta por m²", fmt(venta_m2),
                        f"{m2} m² de local"), unsafe_allow_html=True)
        kpi_tip("<b>Productividad del espacio.</b> Cuanto genera cada metro cuadrado. Si es bajo, el local esta subutilizado. Opciones: delivery, eventos, reorganizar layout.")
    with o6:
        venta_diaria = total_ventas / dias_periodo if dias_periodo else 0
        st.markdown(kpi("📅", "Venta Diaria Prom.", fmt(venta_diaria),
                        f"{dias_periodo} dias operados"), unsafe_allow_html=True)
        kpi_tip("<b>Meta diaria de referencia.</b> Divide tu punto de equilibrio por los dias del mes para saber cuanto necesitas vender cada dia como minimo.")

    # Tabla resumen de todos los KPIs
    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
    with st.expander("Ver tabla resumen de KPIs"):
        kpi_rows = [
            {"KPI": "Food Cost %", "Valor": fmt_pct(food_cost_pct), "Meta": "28-35%",
             "Estado": "OK" if 28 <= food_cost_pct <= 35 else ("Alerta" if food_cost_pct <= 40 else "Critico")},
            {"KPI": "Labor Cost %", "Valor": fmt_pct(labor_cost_pct), "Meta": "≤30%",
             "Estado": "OK" if labor_cost_pct <= 30 else ("Alerta" if labor_cost_pct <= 35 else "Critico")},
            {"KPI": "Rent Cost %", "Valor": fmt_pct(rent_cost_pct), "Meta": "≤8-10%",
             "Estado": "OK" if rent_cost_pct <= 8 else ("Alerta" if rent_cost_pct <= 10 else "Critico")},
            {"KPI": "Prime Cost %", "Valor": fmt_pct(prime_cost_pct), "Meta": "≤60-65%",
             "Estado": "OK" if prime_cost_pct <= 60 else ("Alerta" if prime_cost_pct <= 65 else "Critico")},
            {"KPI": "Margen Bruto", "Valor": fmt(margen_bruto), "Meta": "—", "Estado": "—"},
            {"KPI": "Resultado Operacional", "Valor": fmt(resultado_op), "Meta": "> $0",
             "Estado": "OK" if resultado_op > 0 else "Critico"},
            {"KPI": "Punto de Equilibrio", "Valor": fmt(punto_equilibrio), "Meta": "—",
             "Estado": "Cubierto" if total_ventas >= punto_equilibrio else "No alcanzado"},
            {"KPI": "Ticket Promedio", "Valor": fmt(ticket_promedio), "Meta": "—", "Estado": "—"},
            {"KPI": "Gasto por Cliente", "Valor": fmt(gasto_cliente), "Meta": "—", "Estado": "—"},
            {"KPI": "RevPASH", "Valor": fmt(revpash), "Meta": "—", "Estado": "—"},
            {"KPI": "Rotacion de Mesas", "Valor": f"{rotacion_mesas:.1f}", "Meta": "—", "Estado": "—"},
            {"KPI": "Venta por m²", "Valor": fmt(venta_m2), "Meta": "—", "Estado": "—"},
        ]
        st.dataframe(kpi_rows, use_container_width=True, hide_index=True)


# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────

def main():
    init_session_state()
    setup_sidebar()
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📈 KPIs Gastronomicos", "💬 Chat IA"])
    with tab1:
        render_dashboard()
    with tab2:
        render_kpis()
    with tab3:
        render_chat()

if __name__ == "__main__":
    main()
