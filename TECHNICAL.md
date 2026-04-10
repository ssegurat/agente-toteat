# Documentacion Tecnica — Toteat Intelligence

---

## 1. Arquitectura del Sistema

### Flujo General

```
Usuario (Browser)
    |
    v
Streamlit App (app.py)
    |
    |-- [Cache Layer] -- st.cache_data (TTL por tipo)
    |       |
    |       v
    |   ToteatAPI (toteat_api.py)
    |       |
    |       |-- retry + backoff (429)
    |       v
    |   API REST Toteat (api.toteat.com)
    |
    |-- [Multi-Local] -- multi_local.py
    |       |
    |       |-- Token auth (URL query params)
    |       |-- Config loader (Streamlit Secrets)
    |       |-- Client factory (ToteatAPI por local)
    |       v
    |   N instancias ToteatAPI (una por sucursal)
    |
    |-- [Chat IA] -- Anthropic Claude API
    |       |
    |       |-- tools.py (definiciones + ejecucion)
    |       v
    |   Claude claude-sonnet-4 (tool use loop)
    |
    |-- [UF] -- mindicador.cl/api/uf
    |
    v
Dashboard / KPIs / Chat (renderizado HTML + Plotly)
```

### Session State Management

Streamlit recarga el script completo en cada interaccion. El estado se mantiene via `st.session_state`:

| Key | Tipo | Proposito |
|---|---|---|
| `toteat_client` | ToteatAPI | Cliente API (modo single) |
| `anthropic_client` | anthropic.Anthropic | Cliente Claude |
| `messages` | list | Historial de chat (modo single) |
| `messages_{local_key}` | list | Historial de chat por local |
| `messages_red` | list | Historial de chat consolidado |
| `toteat_clients` | dict | Clientes API por local (modo multi) |

### Estrategia de Cache

Se usa `@st.cache_data` con diferentes TTL segun la frecuencia de cambio de los datos:

| Funcion | TTL | Razon |
|---|---|---|
| `cached_get_sales` | 300s (5 min) | Ventas no cambian con frecuencia |
| `cached_get_products` | 300s (5 min) | Menu estable |
| `cached_get_shift` | 60s (1 min) | Estado en vivo, mas volatil |
| `cached_get_tables` | 60s (1 min) | Ocupacion cambia constantemente |
| `cached_get_collection` | 120s (2 min) | Recaudacion del dia |
| `cached_get_fiscal_docs` | 300s (5 min) | Documentos estables |
| `cached_get_inventory` | 300s (5 min) | Inventario moderadamente estable |
| `cached_get_accounting` | 300s (5 min) | Movimientos estables |
| `get_uf_value` | 3600s (1 hora) | UF cambia una vez al dia |

**Parametro `local_key`**: Todas las funciones cached reciben un `local_key` (default: `"default"`) que se incluye en la firma de la funcion. Streamlit usa la firma completa como clave de cache, lo que asegura que datos de diferentes restaurantes no se mezclen.

**Parametro `_client` con underscore**: Los parametros que empiezan con `_` son excluidos del hash de cache por Streamlit. Esto permite pasar la instancia de ToteatAPI (no hasheable) sin romper el caching.

---

## 2. Modulos

### app.py — Aplicacion Principal

Estructura interna del archivo (~2880 lineas):

1. **Imports y configuracion de pagina** (lineas 1-24)
2. **Paleta de colores y CSS** (lineas 26-250) — Variables de marca Toteat, CSS custom inyectado via `st.markdown`
3. **System prompt y configuracion Plotly** (lineas 254-273) — Layout base para graficos
4. **Helpers** (lineas 276-334) — `fmt()`, `fmt_full()`, `fmt_pct()`, `kpi()`, `calc_delta()`, `sec()`
5. **Persistencia de config** (lineas 337-493) — `_load_kpi_history()`, `_save_kpi_history()`, `_load_month_expenses()`, `_save_month_expenses()`, `_load_restaurant_defaults()`, `_save_restaurant_defaults()`
6. **Funciones de fecha** (lineas 495-513) — `_subtract_months()`, `_subtract_years()` para periodos comparativos
7. **Cache layer** (lineas 515-596) — `_chunked_api_call()` y todas las funciones `cached_get_*`
8. **Procesamiento de ventas** (lineas 598-680) — `process_sales()` que transforma datos crudos en metricas
9. **Session state y sidebar** (lineas 683-711) — `init_session_state()`, `setup_sidebar()`
10. **render_dashboard()** (lineas 717-997) — Dashboard principal con ventas, graficos, mesas, menu, recaudacion, inventario y contabilidad
11. **render_chat()** (lineas 1442-1506) — Chat IA con loop de tool use
12. **render_kpis()** (lineas 1508-1976) — KPIs gastronomicos con gauges, gastos mensuales, historial
13. **Vistas consolidadas** (lineas 1978-2799) — `render_consolidated_dashboard()`, `render_consolidated_kpis()`, `render_consolidated_chat()`
14. **main()** (lineas 2806-2883) — Entry point con routing multi-local/single

### multi_local.py — Logica Multi-Sucursal

Funciones:

- `is_multi_local_mode()` — Detecta si existe seccion `[locals]` en Streamlit Secrets
- `load_locals_config()` — Lee configuracion de locales desde Secrets, retorna dict por slug
- `load_token_permissions()` — Lee `[tokens]` desde Secrets, mapea token a lista de local_keys. Soporta `["*"]` como comodin
- `authenticate_by_token()` — Lee `?token=` de query params, valida contra permisos
- `get_clients_for_locals()` — Crea instancias ToteatAPI por local, cachea en session_state
- `get_local_config()` — Extrae parametros operativos de un local (sueldos, arriendo_uf, servicios, etc.)

### tools.py — Herramientas del Chat IA

**`TOOLS`**: Lista de 11 definiciones de herramientas en formato Anthropic (name, description, input_schema):

| Tool | Parametros | API Call |
|---|---|---|
| `get_products` | ninguno | `client.get_products()` |
| `get_sales` | date_from, date_to | `client.get_sales()` |
| `get_sales_by_waiter` | date_from, date_to | `client.get_sales_by_waiter()` |
| `get_collection` | date | `client.get_collection()` |
| `get_tables` | ninguno | `client.get_tables()` |
| `get_shift_status` | ninguno | `client.get_shift_status()` |
| `get_order_status` | order_ids | `client.get_order_status()` |
| `get_cancellation_report` | date_from, date_to | `client.get_cancellation_report()` |
| `get_fiscal_documents` | date_from, date_to | `client.get_fiscal_documents()` |
| `get_inventory_state` | date_from, date_to | `client.get_inventory_state()` |
| `get_accounting_movements` | date_from, date_to | `client.get_accounting_movements()` |

**`execute_tool()`**: Recibe nombre, input y cliente. Ejecuta la llamada API correspondiente y retorna JSON string. Envuelto en try/except que retorna errores como JSON.

**`execute_tool_multi()`**: Itera sobre todos los clientes (locales), ejecuta la misma herramienta en cada uno con `time.sleep(1)` entre llamadas. Retorna resultados agrupados por nombre de local.

### toteat_api.py — Cliente REST

Clase `ToteatAPI` con:

- **Autenticacion**: Via query parameters (`xir`, `xil`, `xiu`, `xapitoken`), no headers
- **Retry automatico**: `_request_with_retry()` con hasta 5 reintentos en HTTP 429
- **Backoff exponencial**: [3, 6, 12, 20, 30] segundos entre reintentos
- **Timeout**: 30 segundos por request
- **Formato de fechas**: Convierte `YYYY-MM-DD` a `YYYYMMDD` internamente via `_format_date()`

Metodos publicos: `get_products()`, `get_sales()`, `get_sales_by_waiter()`, `get_collection()`, `get_tables()`, `get_shift_status()`, `get_order_status()`, `get_cancellation_report()`, `get_fiscal_documents()`, `get_inventory_state()`, `get_accounting_movements()`

---

## 3. Flujo de Autenticacion Multi-Local

```
1. Usuario accede con ?token=ABC123
       |
       v
2. authenticate_by_token()
   - Lee st.query_params["token"]
   - Si no hay token -> (None, [])
       |
       v
3. load_token_permissions()
   - Lee st.secrets["tokens"]
   - Mapea: "ABC123" -> ["local1", "local2"]
   - Si el valor es ["*"] -> expande a todos los locales
       |
       v
4. Retorna (token, allowed_local_keys)
       |
       v
5. main() valida que token y allowed_locals existan
   - Si no -> muestra pagina de acceso restringido
       |
       v
6. load_locals_config() -> dict con config de cada local
       |
       v
7. get_clients_for_locals(allowed_locals, locals_config)
   - Crea ToteatAPI por cada local permitido
   - Cachea en st.session_state.toteat_clients
       |
       v
8. Selector de local en UI
   - "Red Completa" -> vistas consolidadas
   - Local individual -> render_dashboard/kpis/chat con client y local_key
```

**Fallback a modo legacy**: Si `is_multi_local_mode()` retorna `False` (no hay `[locals]` en Secrets), la app funciona en modo single-restaurant con sidebar para ingresar credenciales manualmente.

---

## 4. Estrategia de Cache en Detalle

### Chunking para rangos largos

`_chunked_api_call()` resuelve la limitacion de 15 dias por consulta de la API de Toteat:

1. Calcula el delta de dias entre `date_from` y `date_to`
2. Si <= 15 dias, llama una sola vez
3. Si > 15 dias, divide en chunks de 15 dias
4. Agrega `time.sleep(2)` entre chunks (excepto el primero)
5. Combina resultados: extrae `data` de cada respuesta y concatena las listas
6. Retorna `{"data": all_data}`

### Aislamiento por local

```python
@st.cache_data(ttl=300, show_spinner=False)
def cached_get_sales(_client, date_from: str, date_to: str, local_key: str = "default"):
```

- `_client`: Prefijo `_` lo excluye del hash (ToteatAPI no es hasheable)
- `local_key`: Incluido en el hash, asegura cache separado por restaurante
- `date_from`, `date_to`: Incluidos en el hash, cache por periodo

### UF con cache largo

```python
@st.cache_data(ttl=3600, show_spinner=False)
def get_uf_value():
```

Consulta `mindicador.cl/api/uf` una vez por hora para obtener el valor de la UF en CLP.

---

## 5. KPIs Gastronomicos

### Formulas de Calculo

| KPI | Formula |
|---|---|
| Food Cost % | `(total_cost / total_ventas) * 100` |
| Labor Cost % | `(sueldos / total_ventas) * 100` |
| Rent Cost % | `(arriendo_clp / total_ventas) * 100` |
| Prime Cost % | `food_cost_pct + labor_cost_pct` |
| Margen Bruto | `total_ventas - total_cost` |
| Resultado Operacional | `total_ventas - total_cost - sueldos - arriendo_clp - servicios - otros` |
| Punto de Equilibrio | `gastos_fijos / (1 - food_cost_pct / 100)` |
| Ticket Promedio | `total_ventas / num_orders` |
| Gasto por Cliente | `total_ventas / total_clients` |
| RevPASH | `total_ventas / (total_seats * horas_op * dias_periodo)` |
| Rotacion de Mesas | `num_orders / total_tables` |
| Venta por m2 | `total_ventas / m2` |
| Venta Diaria Prom. | `total_ventas / dias_periodo` |

### Rangos Objetivo (Semaforo)

| KPI | Verde | Amarillo | Rojo |
|---|---|---|---|
| Food Cost % | 28-35% | 22-28% o 35-40% | <22% o >40% |
| Labor Cost % | 20-30% | 15-20% o 30-35% | <15% o >35% |
| Rent Cost % | 5-8% | 3-5% o 8-10% | <3% o >10% |
| Prime Cost % | 50-60% | 45-50% o 60-65% | <45% o >65% |

La funcion `_kpi_color(value, green_range, yellow_range)` determina el color. Los charts tipo gauge usan `_gauge_chart()` con la misma logica visual.

### Historial de KPIs

- **`_save_kpi_history(year, month, kpis)`**: Guarda un dict de KPIs bajo la clave `"YYYY-MM"` en `kpi_history.json`
- **`_load_kpi_history()`**: Lee todo el historial del archivo
- **`_get_best_kpi(kpi_name, higher_is_better)`**: Recorre el historial y retorna `(mejor_valor, mes)`. Para KPIs como Food Cost, `higher_is_better=False` (menor es mejor)
- **`kpi_record()`** dentro de `render_kpis()`: Genera el texto del record para mostrar en la tarjeta KPI (ej: "Mejor: $12M (Mar 2025) · -5.2%")

### Gastos por Mes

Dos capas de persistencia:

1. **Archivo local** (`restaurant_config.json`): Estructura `{"months": {"2025-03": {"sueldos": 3500000, ...}}}`
2. **Streamlit Secrets** (fallback): Para Streamlit Cloud donde no hay filesystem persistente

La funcion `_load_month_expenses()` intenta primero el archivo local y luego los Secrets.

---

## 6. Chat IA

### System Prompt

El prompt incluye:
- Rol: asistente inteligente para restaurantes con Toteat
- Fecha actual (para interpretar "hoy", "ayer", "esta semana")
- Idioma: espanol
- En modo multi-local: lista de locales disponibles e instruccion de comparar

### Loop de Tool Use

```
1. Usuario envia mensaje
2. Se construye api_messages con historial + nuevo mensaje
3. Claude responde (puede incluir tool_use blocks)
4. WHILE response.stop_reason == "tool_use":
   a. Extraer tool_use blocks del response
   b. Agregar response como assistant message
   c. Por cada tool_use:
      - Single: execute_tool(name, input, client)
      - Multi:  execute_tool_multi(name, input, clients, locals_config)
   d. Agregar tool_results como user message
   e. Llamar Claude de nuevo
5. Extraer texto final de response.content
6. Guardar en session_state
```

### Multi-Local Chat

`execute_tool_multi()` ejecuta la herramienta en cada local secuencialmente con 1 segundo de delay entre cada uno. Retorna un JSON con los resultados organizados por nombre de local:

```json
{
  "Restaurante Centro": { "data": [...] },
  "Restaurante Providencia": { "data": [...] }
}
```

Claude recibe esta estructura y puede comparar entre locales en su respuesta.

---

## 7. Manejo de Errores

### Retry con Backoff Exponencial

En `toteat_api.py`, `_request_with_retry()`:

```
Intento 1 -> 429 -> sleep(3s)
Intento 2 -> 429 -> sleep(6s)
Intento 3 -> 429 -> sleep(12s)
Intento 4 -> 429 -> sleep(20s)
Intento 5 -> 429 -> sleep(30s)
Intento 6 -> raise_for_status()
```

### Secciones del Dashboard

Cada seccion del dashboard (ventas, turno, mesas, fiscal, inventario, contabilidad) esta envuelta en su propio `try/except`. Si una seccion falla, las demas siguen funcionando normalmente y se muestra un `st.error()` localizado.

### Formatos de Respuesta Flexibles

`process_sales()` y las funciones de rendering manejan multiples formatos de respuesta:
- Respuesta como `list` directa
- Respuesta como `dict` con clave `"data"`
- Campos con nombres alternativos (ej: `"type"` o `"documentType"`, `"total"` o `"amount"`)

### Herramientas del Chat

`execute_tool()` envuelve cada llamada en try/except y retorna errores como JSON `{"error": "mensaje"}`, permitiendo que Claude interprete el error y responda al usuario.

---

## 8. Deployment

### Streamlit Community Cloud

1. Conectar repositorio GitHub a Streamlit Cloud
2. Configurar Secrets en la interfaz web de Streamlit Cloud (formato TOML)
3. Streamlit Cloud ejecuta `streamlit run app.py` automaticamente
4. Auto-deploy en cada push a la rama principal

### Configuracion del Tema

En `.streamlit/config.toml`:
- Tema light con color primario rojo Toteat (`#ff4235`)
- Fondo `#f7f8fa`, cards `#ffffff`
- `headless = true` para deployment
- `gatherUsageStats = false`

### Secrets como Variables de Entorno

En modo local, las variables vienen de `.env` via `python-dotenv`. En Streamlit Cloud, vienen de `st.secrets` que se configuran en la interfaz web.

---

## 9. Decisiones Tecnicas y Trade-offs

### Por que Streamlit y no React/Next.js

- **Velocidad de desarrollo**: Una sola persona puede construir un dashboard completo en Python sin necesidad de frontend separado
- **Ecosistema data**: Integracion nativa con Pandas, Plotly, y el modelo mental de data pipelines
- **Hosting gratuito**: Streamlit Community Cloud ofrece hosting sin costo
- **Trade-off**: Menos control sobre la UI, limitaciones en interactividad compleja, recargas completas del script en cada interaccion

### Por que cache en vez de base de datos

- **Simplicidad**: No requiere infraestructura adicional (PostgreSQL, Redis, etc.)
- **Adecuado para el caso de uso**: Los datos vienen de la API de Toteat en tiempo real, no necesitan persistencia a largo plazo
- **TTL ajustable**: Diferentes tiempos de cache segun la volatilidad del dato
- **Trade-off**: Los archivos JSON locales (`restaurant_config.json`, `kpi_history.json`) no persisten en Streamlit Cloud entre reinicios. La solucion futura seria migrar a una base de datos.

### Por que tokens en URL en vez de login

- **Simplicidad para el usuario**: Un link es mas facil que un formulario de login
- **Sin gestion de passwords**: No hay que almacenar hashes, manejar recuperacion, etc.
- **Facil de compartir**: El administrador genera links con diferentes niveles de acceso
- **Trade-off**: Menos seguro que un sistema de autenticacion completo. Los tokens viajan en la URL (visible en logs de servidor, historial del browser). Adecuado para herramientas internas, no para datos altamente sensibles.

### Rate Limiting: Chunking + Retry + Sleep

La API de Toteat tiene un rate limit estricto (~3 req/min). La estrategia combina tres mecanismos:

1. **Cache**: Reduce llamadas repetidas (TTL de 1-5 minutos)
2. **Chunking**: Divide rangos largos en periodos de 15 dias con sleep(2) entre chunks
3. **Retry con backoff**: Si llega un 429, espera progresivamente mas tiempo
4. **Sleep entre locales**: En modo multi-sucursal, 1 segundo entre cada local

**Trade-off**: La carga inicial puede ser lenta (especialmente con rangos largos y multiples locales), pero las cargas subsiguientes son instantaneas gracias al cache.
