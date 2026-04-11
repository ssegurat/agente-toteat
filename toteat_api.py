import time
import requests


class ToteatAPI:
    """Cliente para la API de Toteat. Thread-safe (sin Session compartida)."""

    MAX_RETRIES = 2
    RETRY_BACKOFF = [2, 5]

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

    def _request_with_retry(self, url, timeout=15, **kwargs):
        """GET con retry en 429. Thread-safe (usa requests.get directo)."""
        for attempt in range(self.MAX_RETRIES):
            response = requests.get(url, timeout=timeout, **kwargs)
            if response.status_code == 429:
                wait = self.RETRY_BACKOFF[min(attempt, len(self.RETRY_BACKOFF) - 1)]
                time.sleep(wait)
                continue
            response.raise_for_status()
            return response.json()
        # Último intento
        response = requests.get(url, timeout=timeout, **kwargs)
        response.raise_for_status()
        return response.json()

    def _get(self, endpoint: str, params: dict = None, timeout: int = 15) -> dict:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        all_params = self._auth_params()
        if params:
            all_params.update(params)
        return self._request_with_retry(url, timeout=timeout, params=all_params)

    @staticmethod
    def _format_date(date_str: str) -> str:
        return date_str.replace("-", "")

    def get_tables(self) -> dict:
        return self._get("tables", timeout=8)

    def get_shift_status(self) -> dict:
        return self._get("shiftstatus", timeout=8)

    def get_products(self) -> dict:
        return self._get("products", {"activeProducts": "true"}, timeout=10)

    def get_collection(self, date: str) -> dict:
        return self._get("collection", {"date": self._format_date(date)}, timeout=10)

    def get_sales(self, date_from: str, date_to: str) -> dict:
        return self._get("sales", {
            "ini": self._format_date(date_from),
            "end": self._format_date(date_to),
        })

    def get_sales_by_waiter(self, date_from: str, date_to: str) -> dict:
        return self._get("salesbywaiter", {
            "initial_date": self._format_date(date_from),
            "final_date": self._format_date(date_to),
        })

    def get_order_status(self, order_ids: str, detail: bool = False) -> dict:
        return self._get("orderstatus", {"ic": order_ids, "det": str(detail).lower()})

    def get_cancellation_report(self, date_from: str, date_to: str) -> dict:
        return self._get("orders/cancellation-report", {
            "ini": self._format_date(date_from),
            "end": self._format_date(date_to),
        })

    def get_fiscal_documents(self, date_from: str, date_to: str) -> dict:
        return self._get("fiscaldocuments", {
            "ini": self._format_date(date_from),
            "end": self._format_date(date_to),
        })

    def get_inventory_state(self, date_from: str, date_to: str) -> dict:
        return self._get("inventorystate", {
            "initial_date": self._format_date(date_from),
            "final_date": self._format_date(date_to),
        })

    def get_accounting_movements(self, date_from: str, date_to: str) -> dict:
        return self._get("accountingmovements", {
            "initial_date": self._format_date(date_from),
            "final_date": self._format_date(date_to),
        })
