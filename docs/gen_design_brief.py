"""Genera el PDF del Design Brief de Agente Toteat."""
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch, mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether
)

# Brand colors
RED = HexColor("#ff4235")
DARK = HexColor("#1a1a1a")
GRAY = HexColor("#6b7280")
LIGHT_BG = HexColor("#f7f8fa")
BORDER = HexColor("#e5e7eb")
SUCCESS = HexColor("#22c55e")
WARNING = HexColor("#f59e0b")
DANGER = HexColor("#ef4444")

def build_pdf(output_path):
    doc = SimpleDocTemplate(
        output_path, pagesize=letter,
        leftMargin=0.75*inch, rightMargin=0.75*inch,
        topMargin=0.75*inch, bottomMargin=0.75*inch,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    styles.add(ParagraphStyle("DocTitle", parent=styles["Title"], fontSize=22, textColor=DARK,
                              fontName="Helvetica-Bold", spaceAfter=6))
    styles.add(ParagraphStyle("DocSubtitle", parent=styles["Normal"], fontSize=11, textColor=GRAY,
                              spaceAfter=20))
    styles.add(ParagraphStyle("SectionTitle", parent=styles["Heading1"], fontSize=14, textColor=RED,
                              fontName="Helvetica-Bold", spaceBefore=24, spaceAfter=8,
                              borderWidth=0, borderPadding=0))
    styles.add(ParagraphStyle("SubSection", parent=styles["Heading2"], fontSize=11, textColor=DARK,
                              fontName="Helvetica-Bold", spaceBefore=14, spaceAfter=6))
    styles.add(ParagraphStyle("Body", parent=styles["Normal"], fontSize=9.5, textColor=DARK,
                              leading=14, spaceAfter=6))
    styles.add(ParagraphStyle("BodySmall", parent=styles["Normal"], fontSize=8.5, textColor=GRAY,
                              leading=12, spaceAfter=4))
    styles.add(ParagraphStyle("CodeBlock", parent=styles["Normal"], fontSize=8, fontName="Courier",
                              textColor=DARK, backColor=LIGHT_BG, leading=11, spaceAfter=6,
                              leftIndent=12, rightIndent=12, spaceBefore=4))
    styles.add(ParagraphStyle("TableHeader", parent=styles["Normal"], fontSize=8, fontName="Helvetica-Bold",
                              textColor=white, alignment=TA_CENTER))
    styles.add(ParagraphStyle("TableCell", parent=styles["Normal"], fontSize=8, textColor=DARK,
                              leading=11))

    story = []

    # ─── COVER ───
    story.append(Spacer(1, 1.5*inch))
    story.append(Paragraph("AGENTE TOTEAT", styles["DocTitle"]))
    story.append(Paragraph("Design Assessment Brief", ParagraphStyle("CoverSub", parent=styles["DocTitle"],
                            fontSize=16, textColor=GRAY)))
    story.append(Spacer(1, 12))
    story.append(HRFlowable(width="100%", thickness=3, color=RED))
    story.append(Spacer(1, 20))
    story.append(Paragraph("Documento para evaluacion de UX/UI por disenador experto", styles["DocSubtitle"]))
    story.append(Paragraph("<b>Producto:</b> Dashboard de inteligencia para restaurantes (Toteat POS)", styles["Body"]))
    story.append(Paragraph("<b>Plataforma:</b> Streamlit (Python) desplegado en Streamlit Cloud", styles["Body"]))
    story.append(Paragraph("<b>Usuarios target:</b> Duenos, gerentes y administradores de restaurantes", styles["Body"]))
    story.append(Paragraph("<b>Dispositivo principal:</b> Movil (90% de usuarios)", styles["Body"]))
    story.append(Paragraph("<b>Paises:</b> Chile, Argentina, Peru, Colombia, Costa Rica, Mexico", styles["Body"]))
    story.append(Paragraph("<b>URLs de acceso:</b>", styles["Body"]))
    story.append(Paragraph("App usuario: agente-toteat-*.streamlit.app", styles["BodySmall"]))
    story.append(Paragraph("Admin: toteat-ia.streamlit.app", styles["BodySmall"]))
    story.append(PageBreak())

    # ─── 1. STACK TECNOLOGICO ───
    story.append(Paragraph("1. Stack Tecnologico", styles["SectionTitle"]))
    story.append(HRFlowable(width="100%", thickness=1, color=RED))
    story.append(Spacer(1, 8))

    stack_data = [
        ["Componente", "Tecnologia", "Notas"],
        ["Frontend", "Streamlit (Python)", "Framework de dashboards. No permite HTML/CSS/JS puro. Todo se renderiza via componentes de Streamlit con inyeccion de CSS custom."],
        ["Graficos", "Plotly (plotly.graph_objects)", "Gauges, barras, donuts, waterfall. Configurados como staticPlot (sin interactividad) para compatibilidad movil."],
        ["Backend / API", "API REST Toteat", "api.toteat.com/mw/or/1.0/ - 11 endpoints GET. Auth via query params. Rate limit: 3 req simultaneos."],
        ["Base de datos", "Supabase (PostgreSQL)", "Para admin panel, usuarios, suscripciones. Los datos de ventas vienen de la API de Toteat."],
        ["Deploy", "Streamlit Cloud (Free tier)", "Auto-deploy desde GitHub. Limitaciones de performance en free tier."],
        ["Iconos", "Emoji nativo (Unicode)", "No se usa libreria de iconos. Emojis como indicadores visuales en headers, KPIs, badges."],
    ]
    t = Table(stack_data, colWidths=[1.2*inch, 1.5*inch, 4.3*inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), DARK),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("LEADING", (0, 0), (-1, -1), 11),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, LIGHT_BG]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t)

    story.append(Spacer(1, 12))
    story.append(Paragraph("<b>Limitaciones de Streamlit para el disenador:</b>", styles["Body"]))
    story.append(Paragraph("- No se pueden crear componentes HTML/CSS/JS puros (todo pasa por st.markdown con unsafe_allow_html)", styles["BodySmall"]))
    story.append(Paragraph("- El layout es columnar (st.columns) con proporciones fijas, no CSS Grid/Flexbox libre", styles["BodySmall"]))
    story.append(Paragraph("- Los inputs (text, number, select) usan componentes nativos de Streamlit, no se pueden customizar completamente", styles["BodySmall"]))
    story.append(Paragraph("- Cada interaccion del usuario hace un 'rerun' completo de la app (recarga toda la pagina)", styles["BodySmall"]))
    story.append(Paragraph("- No hay routing/navegacion SPA — se usan tabs (st.tabs) para secciones", styles["BodySmall"]))

    # ─── 2. PALETA DE COLORES ───
    story.append(PageBreak())
    story.append(Paragraph("2. Paleta de Colores", styles["SectionTitle"]))
    story.append(HRFlowable(width="100%", thickness=1, color=RED))
    story.append(Spacer(1, 8))

    story.append(Paragraph("2.1 Colores Primarios y de Marca", styles["SubSection"]))
    colors_primary = [
        ["Nombre", "Hex", "Uso"],
        ["TOTEAT_RED", "#ff4235", "Color primario de marca. CTAs, acentos, bordes de seccion, logo."],
        ["TOTEAT_RED_HOVER", "#ffa099", "Estado hover de elementos rojos."],
        ["TOTEAT_RED_LIGHT", "#fff1f0", "Fondo suave rojo para hover de filas."],
        ["TOTEAT_RED_BG", "#ff42350d", "Overlay transparente (~5% opacidad)."],
    ]
    t = Table(colors_primary, colWidths=[1.8*inch, 1.2*inch, 4*inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), RED),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("LEADING", (0, 0), (-1, -1), 11),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, LIGHT_BG]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t)

    story.append(Spacer(1, 10))
    story.append(Paragraph("2.2 Fondos y Superficies", styles["SubSection"]))
    colors_bg = [
        ["Nombre", "Hex", "Uso"],
        ["BG_PAGE", "#f7f8fa", "Fondo principal de la app (gris muy claro)."],
        ["BG_CARD", "#ffffff", "Fondo de tarjetas KPI, contenedores."],
        ["BG_SIDEBAR", "#1a1a1a", "Fondo sidebar (oscuro, admin)."],
        ["BORDER", "#e5e7eb", "Bordes, divisores, lineas."],
        ["BORDER_LIGHT", "#f3f4f6", "Bordes suaves, fondos de tooltips."],
    ]
    t = Table(colors_bg, colWidths=[1.8*inch, 1.2*inch, 4*inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), DARK),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, LIGHT_BG]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t)

    story.append(Spacer(1, 10))
    story.append(Paragraph("2.3 Colores Semanticos", styles["SubSection"]))
    colors_sem = [
        ["Nombre", "Hex", "BG", "Uso"],
        ["SUCCESS", "#22c55e", "#f0fdf4", "Positivo, crecimiento, disponible, badge activo."],
        ["WARNING", "#f59e0b", "#fffbeb", "Alerta, precaucion, badge trial."],
        ["DANGER", "#ef4444", "#fef2f2", "Error, critico, badge suspendido, KPI negativo."],
    ]
    t = Table(colors_sem, colWidths=[1.2*inch, 1*inch, 1*inch, 3.8*inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), DARK),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, LIGHT_BG]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t)

    story.append(Spacer(1, 10))
    story.append(Paragraph("2.4 Colores de Texto", styles["SubSection"]))
    colors_txt = [
        ["Nombre", "Hex", "Uso"],
        ["TEXT_PRIMARY", "#1a1a1a", "Texto principal, titulos, valores KPI."],
        ["TEXT_SECONDARY", "#6b7280", "Texto secundario, labels, captions."],
        ["TEXT_MUTED", "#9ca3af", "Texto deshabilitado, placeholders."],
    ]
    t = Table(colors_txt, colWidths=[1.8*inch, 1.2*inch, 4*inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), DARK),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, LIGHT_BG]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t)

    # ─── 3. TIPOGRAFIA ───
    story.append(PageBreak())
    story.append(Paragraph("3. Tipografia", styles["SectionTitle"]))
    story.append(HRFlowable(width="100%", thickness=1, color=RED))
    story.append(Spacer(1, 8))

    story.append(Paragraph("<b>Fuente primaria:</b> Nunito Sans (Google Fonts) - pesos 300 a 900", styles["Body"]))
    story.append(Paragraph("<b>Fuente secundaria:</b> Inter (Google Fonts) - pesos 400 a 800", styles["Body"]))
    story.append(Paragraph("<b>Fallback:</b> sans-serif", styles["Body"]))
    story.append(Spacer(1, 8))

    typo_data = [
        ["Componente", "Tamano", "Peso", "Color", "Extras"],
        ["Titulo pagina", "1.25rem", "800", "#1a1a1a", "Nunito Sans"],
        ["Header seccion", "0.95rem", "800", "#1a1a1a", "Border-bottom 2px red"],
        ["KPI Label", "0.68rem", "700", "#374151", "UPPERCASE, letter-spacing 0.08em"],
        ["KPI Valor", "1.6rem", "800", "#1a1a1a", "Mobile: 1.3rem"],
        ["KPI Sub", "0.73rem", "600", "Semantico", "SUCCESS/WARNING/DANGER"],
        ["Body text", "0.85rem", "400", "#1a1a1a", "Leading 14px"],
        ["Caption", "0.78rem", "600", "#6b7280", "Para metadata, comparaciones"],
        ["Badge", "0.72rem", "800", "Semantico", "Pill shape, border-radius 20px"],
        ["Boton", "0.82rem", "700", "white", "Mobile: 0.95rem, min-h 48px"],
        ["Wizard titulo", "1.4rem", "800", "#1a1a1a", "Centrado, line-height 1.3"],
        ["Tooltip/tip", "0.78rem", "400", "#6b7280", "Fondo #f3f4f6, border-radius 10px"],
        ["Gauge numero", "28px", "400", "#1a1a1a", "Plotly indicator"],
    ]
    t = Table(typo_data, colWidths=[1.4*inch, 0.8*inch, 0.6*inch, 0.9*inch, 3.3*inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), DARK),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
        ("LEADING", (0, 0), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, LIGHT_BG]),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t)

    # ─── 4. COMPONENTES ───
    story.append(PageBreak())
    story.append(Paragraph("4. Componentes UI", styles["SectionTitle"]))
    story.append(HRFlowable(width="100%", thickness=1, color=RED))
    story.append(Spacer(1, 8))

    components = [
        ("KPI Card (.kpi)", "Tarjeta principal de metricas. Fondo blanco, border 1px #e5e7eb, border-radius 12px, padding 16px 20px, min-height 90px, shadow 0 1px 3px rgba(0,0,0,0.04). Contiene: icono emoji, label uppercase, valor grande, subtexto semantico, delta %, record historico."),
        ("Badge (.badge-*)", "Indicador de estado. Pill shape (border-radius 20px), padding 4px 14px, font-size 0.72rem, weight 800. Variantes: active (verde), trial (amarillo), suspended (rojo), created (indigo)."),
        ("Section Header (.sec)", "Titulo de seccion con linea roja inferior. Font 0.95rem weight 800, border-bottom 2px solid #ff4235, margin 28px 0 12px 0. Incluye emoji + texto."),
        ("Gauge (Plotly Indicator)", "Medidor semicircular para KPIs porcentuales (Food Cost, Labor Cost, etc). Rangos de color: verde (meta), amarillo (precaucion), rojo (critico). Numero central 28px. Configurado como staticPlot."),
        ("Progress Bar", "Barra horizontal para progreso (punto de equilibrio, avance del mes). Fondo #e5e7eb, relleno con color semantico (rojo marca, verde, amarillo), height 10px, border-radius 6px."),
        ("Wizard Form", "Formulario de onboarding mobile-first. Max-width 480px centrado. Secciones con icono grande, titulo, input, tip explicativo. Un solo submit al final."),
        ("Tabs (st.tabs)", "3 tabs principales: Dashboard, KPIs Gastronomicos, Chat IA. Tab activo fondo negro (#1a1a1a) texto blanco. Tab inactivo gris."),
        ("Expander", "Seccion colapsable para datos secundarios (gastos, tablas detalle). Header bold 0.85rem. Usado para no saturar la vista principal."),
        ("Donut Chart", "Grafico de torta con agujero central (hole 0.55-0.6). Labels afuera. Colores de la paleta de charts. Sin interactividad (staticPlot)."),
        ("Waterfall Chart", "Cascada financiera: Ventas - Costos = Resultado. Verde para positivo, rojo para negativo, negro para totales."),
    ]
    for name, desc in components:
        story.append(Paragraph(f"<b>{name}</b>", styles["SubSection"]))
        story.append(Paragraph(desc, styles["Body"]))

    # ─── 5. LAYOUT Y RESPONSIVE ───
    story.append(PageBreak())
    story.append(Paragraph("5. Layout y Responsive", styles["SectionTitle"]))
    story.append(HRFlowable(width="100%", thickness=1, color=RED))
    story.append(Spacer(1, 8))

    story.append(Paragraph("5.1 Estructura General", styles["SubSection"]))
    story.append(Paragraph("Max-width: 1400px. Padding-top: 0.6rem. La app usa layout='wide' de Streamlit. El sidebar esta colapsado por defecto y oculto en movil.", styles["Body"]))
    story.append(Spacer(1, 6))

    story.append(Paragraph("5.2 Patrones de Columnas", styles["SubSection"]))
    layout_data = [
        ["Patron", "Uso", "Ejemplo"],
        ["6 columnas iguales", "KPI cards principales", "Venta, Ordenes, Ticket, Clientes, Margen, Propinas"],
        ["4 columnas iguales", "Gauges financieros", "Food Cost, Labor Cost, Rent Cost, Prime Cost"],
        ["3 columnas iguales", "Cards secundarios", "Margen Bruto, Resultado Op., Punto Equilibrio"],
        ["2 columnas iguales", "Charts lado a lado", "Pie + Tabla, Donut + Detalle"],
        ["[2, 2, 2, 1]", "Filtros con boton", "Desde + Hasta + Comparar + Actualizar"],
        ["[4, 1, 1]", "Header con selectores", "Titulo + Mes + Ano"],
    ]
    t = Table(layout_data, colWidths=[1.5*inch, 2*inch, 3.5*inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), DARK),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, LIGHT_BG]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t)

    story.append(Spacer(1, 10))
    story.append(Paragraph("5.3 Mobile (Breakpoint 768px)", styles["SubSection"]))
    story.append(Paragraph("- Padding lateral: 1rem (reducido)", styles["Body"]))
    story.append(Paragraph("- Columnas: flex-wrap (se apilan verticalmente)", styles["Body"]))
    story.append(Paragraph("- Inputs: font-size 1.1rem, min-height 48px (touch target)", styles["Body"]))
    story.append(Paragraph("- Botones: min-height 48px, font-size 0.95rem", styles["Body"]))
    story.append(Paragraph("- KPI cards: padding reducido a 12px, valor 1.3rem", styles["Body"]))
    story.append(Paragraph("- Sidebar: oculto (display none)", styles["Body"]))
    story.append(Paragraph("- Graficos Plotly: staticPlot=true (sin zoom/pan que interfiere con scroll)", styles["Body"]))

    # ─── 6. ESTRUCTURA DE LA APP ───
    story.append(Spacer(1, 12))
    story.append(Paragraph("6. Estructura de la App (User-facing)", styles["SectionTitle"]))
    story.append(HRFlowable(width="100%", thickness=1, color=RED))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Tab 1: Dashboard", styles["SubSection"]))
    story.append(Paragraph("Header (logo + fecha) > Pronostico del Mes (3 cards + barra progreso) > Analisis de Ventas (filtros + 6 KPI cards + comparacion) > Ventas por Hora (bar chart) > Formas de Pago (donut) > Top 15 Familias (horizontal bar) > Salon vs Delivery (donut) > Top 15 Productos (bar) > Performance Meseros (tabla + bar) > Estado en Vivo (turno + mesas) > Documentos Fiscales > Menu > Recaudacion > Inventario > Movimientos Contables", styles["Body"]))

    story.append(Paragraph("Tab 2: KPIs Gastronomicos", styles["SubSection"]))
    story.append(Paragraph("Selector mes/ano > Gastos del Restaurante (expander con wizard) > KPIs Financieros (4 gauges: Food/Labor/Rent/Prime Cost con valores proyectados) > Cards financieros (Margen Bruto, Resultado Op., Punto Equilibrio + barra progreso) > Desglose Costos (pie) > Cascada Resultado (waterfall) > KPIs Operativos (Ticket, Gasto/Cliente, RevPASH, Rotacion, Venta/m2, Venta Diaria)", styles["Body"]))

    story.append(Paragraph("Tab 3: Chat IA", styles["SubSection"]))
    story.append(Paragraph("Chat conversacional con Claude/Anthropic. El usuario puede preguntar sobre sus datos (ventas, tendencias, comparaciones). El asistente tiene acceso a las mismas APIs.", styles["Body"]))

    # ─── 7. PROBLEMAS CONOCIDOS ───
    story.append(PageBreak())
    story.append(Paragraph("7. Problemas Conocidos de UX/UI", styles["SectionTitle"]))
    story.append(HRFlowable(width="100%", thickness=1, color=RED))
    story.append(Spacer(1, 8))

    problems = [
        ("Performance en primera carga", "30-60 segundos para cargar el dashboard completo. La API de Toteat es lenta (~5-8s por endpoint) y hay 8 endpoints secuenciales. Cache de 5 minutos mitiga recargas."),
        ("6 KPI cards en movil", "En pantalla de 375px, 6 columnas se comprimen demasiado. Los valores y deltas se cortan. Necesitan apilarse o reagruparse."),
        ("Graficos Plotly en movil", "Aunque staticPlot elimina el zoom accidental, los graficos son muy anchos para movil. Labels se superponen en donuts y bars."),
        ("Seccion de gastos en KPIs", "7+ inputs numericos en una pantalla. El wizard de onboarding ayuda en primera vez, pero la edicion posterior sigue siendo un formulario largo."),
        ("Sin dark mode", "Solo tema claro. No hay toggle de tema."),
        ("Emojis como iconos", "Renderizan diferente en cada OS/navegador. No hay consistencia visual entre Android, iOS, y desktop."),
        ("Sin onboarding visual", "No hay tour guiado, tooltips de primer uso, ni animaciones de bienvenida mas alla del wizard de gastos."),
        ("Scroll infinito", "El dashboard es una pagina muy larga. No hay anchor links ni navegacion interna para saltar a secciones."),
    ]
    for name, desc in problems:
        story.append(Paragraph(f"<b>{name}</b>", styles["SubSection"]))
        story.append(Paragraph(desc, styles["Body"]))

    # ─── 8. QUE ESPERAMOS DEL ASSESSMENT ───
    story.append(Spacer(1, 12))
    story.append(Paragraph("8. Que Esperamos del Assessment", styles["SectionTitle"]))
    story.append(HRFlowable(width="100%", thickness=1, color=RED))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Pedimos una evaluacion experta de:", styles["Body"]))
    asks = [
        "1. Jerarquia visual y flujo de informacion - El orden de las secciones es correcto? El usuario encuentra lo importante rapido?",
        "2. Experiencia movil - Propuesta concreta para los 6 KPI cards, graficos y tablas en 375px. Como reorganizar sin perder informacion.",
        "3. Consistencia visual - La paleta de colores es coherente? Los componentes siguen un sistema de diseno consistente?",
        "4. Onboarding y primera impresion - Como mejorar el wizard. Propuesta de tour guiado o progressive disclosure.",
        "5. Microinteracciones y feedback - Loading states, transiciones, estados vacios, mensajes de error.",
        "6. Accesibilidad - Contraste de colores, tamanos de touch target, navegacion por teclado.",
        "7. Propuesta de mejora global - Mockups o wireframes de como deberia verse el dashboard ideal en movil y desktop.",
        "8. Sistema de iconos - Propuesta para reemplazar emojis por una libreria consistente (compatible con Streamlit).",
    ]
    for ask in asks:
        story.append(Paragraph(ask, styles["Body"]))

    # Build
    doc.build(story)
    print(f"PDF generado: {output_path}")


if __name__ == "__main__":
    build_pdf("/Users/ssegura1974/Agente IA Toteat/docs/design_brief_agente_toteat.pdf")
