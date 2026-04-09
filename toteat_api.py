import time
import requests


class ToteatAPI:
    """Cliente para la API de Toteat. Autenticación via query parameters."""

    MAX_RETRIES = 5
    RETRY_BACKOFF = [3, 6, 12, 20, 30]  # segundos de espera por intento

    def __init__(self, api_token: str, restaurant_id: str, local_id: str, user_id: str,
                 base_url: str = "https://api.toteat.com/mw/or/1.0/"):
        self.api_token = api_token
        self.restaurant_id = restaurant_id
        self.local_id = local_id
        self.user_id = user_id
        self.base_url = base_url.rstrip("/")

    def _auth_params(self) -> dict:
        return {
            "xir": self.restaurant_id,
            "xil": self.local_id,
            "xiu": self.user_id,
            "xapitoken": self.api_token,
        }

    def _request_with_retry(self, method, url, **kwargs):
        """Ejecuta request con retry automático en caso de 429."""
        for attempt in range(self.MAX_RETRIES):
            response = method(url, timeout=30, **kwargs)
            if response.status_code == 429:
                wait = self.RETRY_BACKOFF[min(attempt, len(self.RETRY_BACKOFF) - 1)]
                time.sleep(wait)
                continue
            response.raise_for_status()
            return response.json()
        # Último intento sin catch
        response.raise_for_status()
        return response.json()

    def _get(self, endpoint: str, params: dict = None) -> dict:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        all_params = self._auth_params()
        if params:
            all_params.update(params)
        return self._request_with_retry(requests.get, url, params=all_params)

    def _post(self, endpoint: str, params: dict = None, data: dict = None) -> dict:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        all_params = self._auth_params()
        if params:
            all_params.update(params)
        return self._request_with_retry(requests.post, url, params=all_params, json=data)

    @staticmethod
    def _format_date(date_str: str) -> str:
        """Convierte YYYY-MM-DD a YYYYMMDD."""
        return date_str.replace("-", "")

    def get_products(self) -> dict:
        """Obtener el menú/productos del restaurante."""
        return self._get("products", {"activeProducts": "true"})

    def get_sales(self, date_from: str, date_to: str) -> dict:
        """Obtener ventas de un período. Fechas en formato YYYY-MM-DD."""
        return self._get("sales", {
            "ini": self._format_date(date_from),
            "end": self._format_date(date_to),
        })

    def get_sales_by_waiter(self, date_from: str, date_to: str) -> dict:
        """Obtener ventas agrupadas por mesero. Fechas en formato YYYY-MM-DD."""
        return self._get("salesbywaiter", {
            "initial_date": self._format_date(date_from),
            "final_date": self._format_date(date_to),
        })

    def get_collection(self, date: str) -> dict:
        """Obtener recaudación de un día. Fecha en formato YYYY-MM-DD."""
        return self._get("collection", {"date": self._format_date(date)})

    def get_tables(self) -> dict:
        """Obtener listado de mesas disponibles."""
        return self._get("tables")

    def get_shift_status(self) -> dict:
        """Obtener estado del turno actual."""
        return self._get("shiftstatus")

    def get_order_status(self, order_ids: str, detail: bool = False) -> dict:
        """Consultar estado de órdenes específicas."""
        return self._get("orderstatus", {
            "ic": order_ids,
            "det": str(detail).lower(),
        })

    def get_cancellation_report(self, date_from: str, date_to: str) -> dict:
        """Obtener reporte de órdenes canceladas. Fechas en formato YYYY-MM-DD."""
        return self._get("orders/cancellation-report", {
            "ini": self._format_date(date_from),
            "end": self._format_date(date_to),
        })

    def get_fiscal_documents(self, date_from: str, date_to: str) -> dict:
        """Obtener documentos fiscales emitidos. Fechas en formato YYYY-MM-DD."""
        return self._get("fiscaldocuments", {
            "ini": self._format_date(date_from),
            "end": self._format_date(date_to),
        })

    def get_inventory_state(self, date_from: str, date_to: str) -> dict:
        """Obtener estado y movimientos de inventario. Fechas en formato YYYY-MM-DD."""
        return self._get("inventorystate", {
            "initial_date": self._format_date(date_from),
            "final_date": self._format_date(date_to),
        })

    def get_accounting_movements(self, date_from: str, date_to: str) -> dict:
        """Obtener movimientos contables. Fechas en formato YYYY-MM-DD."""
        return self._get("accountingmovements", {
            "initial_date": self._format_date(date_from),
            "final_date": self._format_date(date_to),
        })
