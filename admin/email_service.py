"""Servicio de email — recordatorios de trial + resumen diario de ventas."""
from __future__ import annotations

import html
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import streamlit as st

logger = logging.getLogger("toteat.email")

# ── Configuracion ──

def _get_smtp_config() -> dict:
    """Lee config SMTP desde secrets."""
    return {
        "host": st.secrets.get("SMTP_HOST", "smtp.gmail.com"),
        "port": int(st.secrets.get("SMTP_PORT", 587)),
        "user": st.secrets.get("SMTP_USER", ""),
        "password": st.secrets.get("SMTP_PASSWORD", ""),
        "from_email": st.secrets.get("EMAIL_FROM", "hola@toteat-ia.com"),
        "from_name": st.secrets.get("EMAIL_FROM_NAME", "Toteat Intelligence"),
    }


def _send_email(to: str, subject: str, html_body: str) -> bool:
    """Envia un email via SMTP. Retorna True si fue exitoso."""
    config = _get_smtp_config()
    if not config["user"] or not config["password"]:
        logger.warning("[EMAIL] SMTP no configurado — email no enviado a %s", to)
        return False

    msg = MIMEMultipart("alternative")
    msg["From"] = f"{config['from_name']} <{config['from_email']}>"
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP(config["host"], config["port"], timeout=15) as server:
            server.starttls()
            server.login(config["user"], config["password"])
            server.send_message(msg)
        logger.info("[EMAIL] Enviado a %s: %s", to, subject)
        return True
    except Exception as e:
        logger.error("[EMAIL] Error enviando a %s: %s", to, e)
        return False


# ── Templates HTML ──

STYLE = """
<style>
  body { font-family: 'DM Sans', Arial, sans-serif; color: #1f2937; }
  .container { max-width: 600px; margin: 0 auto; padding: 24px; }
  .header { background: #E8553D; color: white; padding: 20px 24px; border-radius: 12px 12px 0 0; }
  .header h1 { margin: 0; font-family: 'Space Grotesk', sans-serif; font-size: 22px; }
  .body { background: #f9fafb; padding: 24px; border: 1px solid #e5e7eb; border-top: none; border-radius: 0 0 12px 12px; }
  .metric { background: white; border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px; margin: 8px 0; text-align: center; }
  .metric .value { font-size: 28px; font-weight: 700; color: #E8553D; }
  .metric .label { font-size: 12px; color: #6b7280; text-transform: uppercase; }
  .btn { display: inline-block; background: #E8553D; color: white; padding: 12px 32px; border-radius: 8px; text-decoration: none; font-weight: 700; margin-top: 16px; }
  .footer { text-align: center; color: #9ca3af; font-size: 12px; margin-top: 24px; }
  table { width: 100%; border-collapse: collapse; margin: 12px 0; }
  td, th { padding: 8px 12px; text-align: left; border-bottom: 1px solid #e5e7eb; font-size: 14px; }
  th { background: #f3f4f6; font-weight: 600; font-size: 12px; text-transform: uppercase; color: #6b7280; }
</style>
"""


def _base_template(title: str, body_html: str) -> str:
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">{STYLE}</head>
<body>
<div class="container">
  <div class="header"><h1>{title}</h1></div>
  <div class="body">{body_html}</div>
  <div class="footer">Toteat Intelligence — Datos que impulsan tu restaurante</div>
</div>
</body></html>"""


# ── Emails de Trial ──

def send_trial_reminder(to: str, company_name: str, days_left: int) -> bool:
    """Email recordatorio de trial (dia 3, 5)."""
    company_name = html.escape(company_name)
    subject = f"Te quedan {days_left} dias de prueba — {company_name}"
    body = f"""
    <p>Hola,</p>
    <p>Tu periodo de prueba de <strong>Toteat Intelligence</strong> para <strong>{company_name}</strong>
    termina en <strong>{days_left} dias</strong>.</p>
    <p>Estas aprovechando:</p>
    <ul>
      <li>Dashboard de ventas en tiempo real</li>
      <li>Chat IA para consultar datos al instante</li>
      <li>KPIs gastronomicos automaticos</li>
      <li>Email diario con resumen de ventas</li>
    </ul>
    <p>Suscribete para no perder acceso:</p>
    <a href="https://toteat-ia.streamlit.app" class="btn">Suscribirme ahora</a>
    <p style="color:#6b7280;font-size:13px;margin-top:20px;">
    Si no te suscribes, al terminar el trial solo podras ver la venta del dia.
    Todo el detalle, chat IA y KPIs se bloquean.</p>
    """
    return _send_email(to, subject, _base_template("Toteat Intelligence", body))


def send_trial_expired(to: str, company_name: str) -> bool:
    """Email de trial expirado (dia 7)."""
    company_name = html.escape(company_name)
    subject = f"Tu trial ha expirado — {company_name}"
    body = f"""
    <p>Hola,</p>
    <p>El periodo de prueba de <strong>Toteat Intelligence</strong> para <strong>{company_name}</strong>
    ha <strong>expirado</strong>.</p>
    <p>A partir de ahora solo puedes ver la venta del dia.
    Chat IA, KPIs, detalle por mesero/producto y exportaciones estan bloqueados.</p>
    <p>Suscribete para recuperar el acceso completo:</p>
    <a href="https://toteat-ia.streamlit.app" class="btn">Suscribirme — desde $19 USD/mes</a>
    <p style="color:#6b7280;font-size:13px;margin-top:20px;">
    Seguiras recibiendo el email diario con tu venta para que no pierdas el pulso de tu negocio.</p>
    """
    return _send_email(to, subject, _base_template("Trial Expirado", body))


# ── Email Diario de Ventas ──

def _fmt_clp(n: float) -> str:
    """Formatea CLP: $1.234.567"""
    return f"${int(n):,}".replace(",", ".")


def send_daily_sales(
    to: str,
    company_name: str,
    local_name: str,
    fecha: str,
    venta_bruta: float,
    venta_neta: float,
    num_ordenes: int,
    num_clientes: int,
    ticket_promedio: float,
    propinas: float,
    top_products: list[tuple[str, int, float]] | None = None,
) -> bool:
    """Email diario con resumen de ventas del dia anterior."""
    company_name = html.escape(company_name)
    local_name = html.escape(local_name)
    subject = f"Ventas {fecha} — {local_name} — {_fmt_clp(venta_bruta)}"

    products_html = ""
    if top_products:
        rows = "".join(
            f"<tr><td>{html.escape(name)}</td><td style='text-align:right'>{qty}</td><td style='text-align:right'>{_fmt_clp(rev)}</td></tr>"
            for name, qty, rev in top_products[:5]
        )
        products_html = f"""
        <h3 style="margin-top:20px;font-size:16px;">Top 5 Productos</h3>
        <table>
          <tr><th>Producto</th><th style="text-align:right">Uds</th><th style="text-align:right">Ingreso</th></tr>
          {rows}
        </table>
        """

    body = f"""
    <p>Buenos dias, aqui tienes el resumen de ventas de <strong>{local_name}</strong> del <strong>{fecha}</strong>:</p>

    <table>
      <tr><td><strong>Venta bruta</strong></td><td style="text-align:right;font-size:20px;font-weight:700;color:#E8553D">{_fmt_clp(venta_bruta)}</td></tr>
      <tr><td><strong>Venta neta (s/IVA)</strong></td><td style="text-align:right;font-weight:700">{_fmt_clp(venta_neta)}</td></tr>
      <tr><td>Ordenes</td><td style="text-align:right">{num_ordenes}</td></tr>
      <tr><td>Clientes</td><td style="text-align:right">{num_clientes}</td></tr>
      <tr><td>Ticket promedio</td><td style="text-align:right">{_fmt_clp(ticket_promedio)}</td></tr>
      <tr><td>Propinas</td><td style="text-align:right">{_fmt_clp(propinas)}</td></tr>
    </table>

    {products_html}

    <p style="margin-top:20px;">
      <a href="https://toteat-ia.streamlit.app" class="btn">Ver detalle completo</a>
    </p>
    """
    return _send_email(to, subject, _base_template(f"Ventas {fecha} — {company_name}", body))
