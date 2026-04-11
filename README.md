# Toteat AI

**Dashboard inteligente para restaurantes que usan Toteat como sistema POS.**

Toteat AI transforma los datos de tu restaurante en decisiones accionables. Visualiza ventas en tiempo real, monitorea KPIs gastronomicos criticos, compara periodos y conversa con una IA que entiende tu negocio.

[Screenshots proximamente]

---

## Funcionalidades

### Dashboard de Ventas en Tiempo Real
- **KPIs principales**: Venta neta, ordenes, ticket promedio, clientes, margen y propinas
- **Graficos interactivos**: Ventas por hora (heatmap), formas de pago (donut), familias de producto (barras horizontales), canales salon vs delivery
- **Top 15 productos** con margen por item
- **Performance por mesero**: ranking de ventas, ticket promedio, clientes atendidos y propinas
- **Detalle de delivery** por plataforma (UberEats, Rappi, PedidosYa, etc.)

### Comparacion con Periodos Anteriores
- Periodo anterior (misma cantidad de dias)
- Mismo periodo del mes anterior
- Mismo periodo del ano anterior
- Variacion porcentual y absoluta en cada KPI

### KPIs Gastronomicos
- **Food Cost %** — Costo de ingredientes sobre ventas (meta: 28-35%)
- **Labor Cost %** — Costo de personal sobre ventas (meta: <=30%)
- **Rent Cost %** — Arriendo sobre ventas (meta: <=8-10%)
- **Prime Cost %** — Food + Labor (meta: <=60-65%)
- **Margen Bruto, Resultado Operacional, Punto de Equilibrio**
- **RevPASH** — Revenue Per Available Seat Hour
- **Rotacion de mesas, Venta por m2, Ticket promedio, Gasto por cliente**
- Graficos tipo gauge con semaforo verde/amarillo/rojo
- Cascada de resultado operacional (waterfall chart)
- Barra de progreso hacia el punto de equilibrio

### Gastos Mensuales por Mes
- Ingreso de sueldos, arriendo (en UF), servicios y otros gastos por cada mes
- Conversion automatica de UF a CLP usando la API de mindicador.cl
- Parametros operativos: horas de operacion, metros cuadrados, numero de empleados
- Persistencia automatica en archivo JSON local

### Historial de KPIs y Records
- Guardado automatico del historial de KPIs por mes
- Visualizacion del mejor registro historico en cada tarjeta KPI
- Indicador de nuevo record cuando se supera el mejor mes

### Tooltips Educativos
- Cada KPI incluye una explicacion en lenguaje simple de que mide, por que importa y que hacer si esta fuera de rango

### Chat IA con Claude
- Consultas en lenguaje natural sobre los datos del restaurante
- Usa herramientas (tool use) para acceder a ventas, menu, mesas, turnos y mas
- En modo multi-sucursal, consulta todos los locales simultaneamente y compara

### Recaudacion Diaria
- Desglose por medio de pago extraido de las ventas del dia
- Informacion de cajas y turnos desde el endpoint de collection

### Estado en Vivo
- Estado del turno actual (abierto/cerrado)
- Ocupacion de mesas por sector
- Capacidad total del restaurante

### Menu del Restaurante
- Listado completo de productos por categoria
- Precios y estado de disponibilidad

### Documentos Fiscales
- Boletas y facturas emitidas en el periodo
- Desglose por tipo y monto

### Inventario y Contabilidad
- Estado de inventario con alertas de stock bajo
- Movimientos contables con balance ingresos vs egresos

### Soporte Multi-Sucursal
- Vista consolidada "Red Completa" que agrega datos de todos los locales
- Comparativa de KPIs entre locales (tabla y graficos)
- Estado en vivo por local
- Chat IA que consulta todos los locales a la vez

### Autenticacion por Token via URL
- Acceso mediante `?token=MI_TOKEN` en la URL
- Permisos configurables por local (incluyendo comodin `*` para todos)
- Sin login, sin passwords — ideal para compartir links de acceso

---

## Arquitectura Tecnica

| Componente | Tecnologia |
|---|---|
| Frontend/Backend | Python + Streamlit |
| Graficos | Plotly (go + express) |
| Procesamiento | Pandas |
| IA | Anthropic Claude API (claude-sonnet-4) |
| POS API | Toteat REST API |
| Valor UF | mindicador.cl API |
| Hosting | Streamlit Community Cloud |

---

## Instalacion Local

```bash
# Clonar el repositorio
git clone <url-del-repo>
cd "Agente IA Toteat"

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales de Toteat y Anthropic

# Ejecutar
streamlit run app.py
```

### Variables de entorno (.env)

```env
ANTHROPIC_API_KEY=tu-api-key-de-anthropic
TOTEAT_API_TOKEN=tu-token-de-toteat
TOTEAT_RESTAURANT_ID=tu-restaurant-id
TOTEAT_LOCAL_ID=1
TOTEAT_USER_ID=tu-user-id-api
TOTEAT_BASE_URL=https://api.toteat.com/mw/or/1.0/
```

---

## Configuracion de Secrets (Streamlit Cloud)

### Modo Single Restaurant

```toml
ANTHROPIC_API_KEY = "sk-ant-..."
TOTEAT_API_TOKEN = "tu-token"
TOTEAT_RESTAURANT_ID = "123"
TOTEAT_LOCAL_ID = "1"
TOTEAT_USER_ID = "456"
TOTEAT_BASE_URL = "https://api.toteat.com/mw/or/1.0/"

[restaurant_config]
sueldos = 3500000
arriendo_uf = 80.0
servicios = 350000
otros = 200000
horas_op = 12
m2 = 120
num_empleados = 15
```

### Modo Multi-Sucursal

```toml
ANTHROPIC_API_KEY = "sk-ant-..."

[locals.local1]
name = "Restaurante Centro"
api_token = "token-local-1"
restaurant_id = "100"
local_id = "1"
user_id = "200"
base_url = "https://api.toteat.com/mw/or/1.0/"
sueldos = 3500000
arriendo_uf = 80.0
servicios = 350000
otros = 200000
horas_op = 12
m2 = 120
num_empleados = 15

[locals.local2]
name = "Restaurante Providencia"
api_token = "token-local-2"
restaurant_id = "101"
local_id = "1"
user_id = "201"
base_url = "https://api.toteat.com/mw/or/1.0/"
sueldos = 4000000
arriendo_uf = 95.0
servicios = 400000
otros = 250000
horas_op = 14
m2 = 150
num_empleados = 18

[tokens]
token_admin = ["*"]
token_gerente_centro = ["local1"]
token_gerente_provi = ["local2"]
token_franquicia = ["local1", "local2"]
```

---

## Estructura del Proyecto

```
app.py                  # Aplicacion principal Streamlit (dashboard, KPIs, chat, vistas consolidadas)
multi_local.py          # Logica multi-sucursal (autenticacion, config, routing de clientes)
tools.py                # Herramientas del chat IA (definiciones para Claude + ejecucion)
toteat_api.py           # Cliente REST para API de Toteat con retry y backoff
requirements.txt        # Dependencias Python
.env.example            # Template de variables de entorno
.streamlit/config.toml  # Configuracion de tema Streamlit (colores, fuentes)
restaurant_config.json  # Gastos mensuales y parametros (auto-generado, gitignored)
kpi_history.json        # Historial de KPIs por mes (auto-generado, gitignored)
```

---

## API de Toteat — Endpoints Utilizados

| Endpoint | Metodo | Estado | Descripcion |
|---|---|---|---|
| `/products` | GET | Funciona | Menu completo con categorias y precios |
| `/sales` | GET | Funciona | Ventas con detalle de productos, pagos y meseros |
| `/salesbywaiter` | GET | Funciona | Ventas agrupadas por mesero |
| `/collection` | GET | Limitado | Recaudacion del dia (no retorna medios de pago) |
| `/tables` | GET | Funciona | Listado de mesas con estado y sector |
| `/shiftstatus` | GET | Funciona | Estado del turno actual |
| `/orderstatus` | GET | Funciona | Estado de ordenes por ID |
| `/fiscaldocuments` | GET | Funciona | Boletas y facturas emitidas |
| `/inventorystate` | GET | Funciona | Estado y movimientos de inventario |
| `/accountingmovements` | GET | Funciona | Movimientos contables |
| `/orders/cancellation-report` | GET | No disponible | Endpoint no accesible en API publica |

---

## Limitaciones Conocidas

- **Rate limit**: La API de Toteat permite ~3 requests/minuto. Mitigado con retry automatico con backoff exponencial (3s, 6s, 12s, 20s, 30s) y cache de Streamlit.
- **Maximo 15 dias por consulta de ventas**: Rangos mayores se dividen automaticamente en chunks de 15 dias con sleep entre cada uno.
- **Collection API limitada**: El endpoint de collection no retorna medios de pago en su respuesta. La seccion de recaudacion extrae los medios de pago directamente de los datos de ventas.
- **Cancelaciones no disponibles**: El endpoint `/orders/cancellation-report` no esta accesible en la API publica de Toteat.
- **Multi-local con sleep**: Las consultas multi-sucursal incluyen `time.sleep(1)` entre locales para evitar rate limiting, lo que puede hacer mas lenta la carga con muchos locales.
- **Persistencia local**: Los archivos `restaurant_config.json` y `kpi_history.json` se guardan en el servidor. En Streamlit Cloud, estos archivos no persisten entre reinicios del servidor.

---

## Contribucion

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -m 'Agrega nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

---

## Base de Datos (Supabase)

El modulo de administracion y facturacion usa **Supabase** (PostgreSQL) como backend.

| Dato | Valor |
|------|-------|
| Proyecto | Toteat AI |
| Region | South America (Sao Paulo) |
| Plan | Free (500MB, suficiente para miles de usuarios) |
| Dashboard | https://supabase.com/dashboard/project/kdeirfyatgmnxwzccrqi |
| Project URL | `https://kdeirfyatgmnxwzccrqi.supabase.co` |

### Tablas principales
- `companies` — Empresas/cadenas de restaurantes
- `restaurants` — Locales con credenciales Toteat y params operativos
- `users` — Usuarios con roles (admin, manager, viewer) y tokens de acceso
- `user_restaurants` — Permisos usuario-local
- `subscriptions` — Suscripciones Mercado Pago
- `payments` — Historial de pagos
- `invitations` — Invitaciones virales al equipo
- `usage_logs` — Metricas de uso

---

## Roadmap

### Fase 1: MVP Admin (En desarrollo)
- CRUD empresas, locales, usuarios
- Conexion dashboard con Supabase (reemplazar Secrets)
- Test de conexion de credenciales Toteat

### Fase 1.5: Sistema de Invitaciones Viral
- "Invitar miembro del equipo" desde el dashboard
- Cada usuario nuevo = +$19/mes automatico
- Gestion de equipo (roles, permisos, locales)

### Fase 2: Facturacion
- Mercado Pago (suscripciones recurrentes)
- Landing page self-service con trial de 7 dias
- Panel de facturacion (MRR, morosidad, pagos)

### Fase 3: Metricas de Uso
- DAU/WAU/MAU, features mas usadas, churn risk
- Reportes de negocio (MRR, LTV, churn rate)

### Fase 4: App Stores
- PWA instalable desde navegador
- Wrapper nativo para Google Play y Apple App Store

### Fase 5: Mejoras Avanzadas
- Planes (Basico $19 / Pro $49 / Enterprise custom)
- Notificaciones (email, WhatsApp, push)
- API propia para integraciones

---

## Modelo de Negocio

| Concepto | Detalle |
|----------|---------|
| Precio | USD $19/mes por usuario + impuestos |
| Trial | 7 dias gratis, sin tarjeta requerida |
| Cobro | Mercado Pago, suscripcion recurrente |
| Crecimiento | Invitaciones virales (cada usuario invita a su equipo) |

---

## Licencia

Proyecto privado. Todos los derechos reservados.
