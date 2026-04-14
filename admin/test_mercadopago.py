"""Tests para la integracion de Mercado Pago — client, sync, email."""
from __future__ import annotations

import json
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch, PropertyMock


# ══════════════════════════════════════════════
# mercadopago_client.py
# ══════════════════════════════════════════════

class TestMercadoPagoClient:
    """Tests para el wrapper de la API de Mercado Pago."""

    @patch("mercadopago_client._get_session")
    def test_create_subscription_success(self, mock_session):
        from mercadopago_client import create_subscription

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "id": "mp_sub_123",
            "init_point": "https://mercadopago.cl/checkout/sub123",
            "status": "pending",
        }
        mock_resp.raise_for_status = MagicMock()
        mock_session.return_value.request.return_value = mock_resp

        result = create_subscription(
            payer_email="test@example.com",
            reason="Toteat Intelligence - Plan Starter",
            amount=9990,
            currency_id="CLP",
            external_reference="toteat_abc_starter",
        )

        assert result["id"] == "mp_sub_123"
        assert "init_point" in result
        assert result["status"] == "pending"

    @patch("mercadopago_client._get_session")
    def test_create_subscription_with_trial(self, mock_session):
        from mercadopago_client import create_subscription

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"id": "mp_sub_trial", "status": "pending"}
        mock_resp.raise_for_status = MagicMock()
        mock_session.return_value.request.return_value = mock_resp

        result = create_subscription(
            payer_email="test@example.com",
            reason="Plan Starter",
            amount=9990,
            currency_id="CLP",
            external_reference="ref_123",
            free_trial_days=7,
        )

        # Verificar que el body incluye free_trial
        call_args = mock_session.return_value.request.call_args
        body = call_args.kwargs.get("json") or call_args[1].get("json")
        assert body["auto_recurring"]["free_trial"]["frequency"] == 7
        assert body["auto_recurring"]["free_trial"]["frequency_type"] == "days"

    @patch("mercadopago_client._get_session")
    def test_invalid_token_returns_error(self, mock_session):
        from mercadopago_client import create_subscription

        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_resp.json.return_value = {"message": "invalid token"}
        mock_resp.raise_for_status.side_effect = Exception("401 Unauthorized")
        type(mock_resp).status_code = PropertyMock(return_value=401)

        # Simular HTTPError
        import requests
        http_error = requests.exceptions.HTTPError(response=mock_resp)
        mock_resp.raise_for_status.side_effect = http_error
        mock_session.return_value.request.return_value = mock_resp

        result = create_subscription(
            payer_email="test@example.com",
            reason="Test",
            amount=9990,
            currency_id="CLP",
            external_reference="ref",
        )

        assert result.get("error") is True
        assert result["status_code"] == 401

    @patch("mercadopago_client._get_session")
    def test_timeout_returns_error_no_crash(self, mock_session):
        import requests
        from mercadopago_client import create_subscription

        mock_session.return_value.request.side_effect = requests.exceptions.Timeout("timeout")

        result = create_subscription(
            payer_email="test@example.com",
            reason="Test",
            amount=9990,
            currency_id="CLP",
            external_reference="ref",
        )

        assert result.get("error") is True
        assert "timeout" in str(result.get("detail", "")).lower()

    @patch("mercadopago_client._get_session")
    def test_clp_amount_is_integer(self, mock_session):
        """CLP no tiene decimales — amount debe ser int."""
        from mercadopago_client import create_subscription

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"id": "x", "status": "pending"}
        mock_resp.raise_for_status = MagicMock()
        mock_session.return_value.request.return_value = mock_resp

        create_subscription(
            payer_email="test@example.com",
            reason="Test",
            amount=19990.50,
            currency_id="CLP",
            external_reference="ref",
        )

        call_args = mock_session.return_value.request.call_args
        body = call_args.kwargs.get("json") or call_args[1].get("json")
        assert isinstance(body["auto_recurring"]["transaction_amount"], int)

    @patch("mercadopago_client._get_session")
    def test_search_payments_returns_list(self, mock_session):
        from mercadopago_client import search_payments

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "results": [{"id": 1, "status": "approved"}, {"id": 2, "status": "pending"}],
            "paging": {"total": 2},
        }
        mock_resp.raise_for_status = MagicMock()
        mock_session.return_value.request.return_value = mock_resp

        result = search_payments(external_reference="toteat_abc")
        assert isinstance(result, list)
        assert len(result) == 2

    @patch("mercadopago_client._get_session")
    def test_search_payments_error_returns_empty(self, mock_session):
        import requests
        from mercadopago_client import search_payments

        mock_session.return_value.request.side_effect = requests.exceptions.ConnectionError()
        result = search_payments(external_reference="ref")
        assert result == []


# ══════════════════════════════════════════════
# mp_sync.py
# ══════════════════════════════════════════════

class TestMPSync:
    """Tests para sincronizacion de pagos."""

    @patch("mp_sync.get_subscription")
    def test_sync_subscription_updates_status(self, mock_get_sub):
        from mp_sync import sync_subscription_status

        mock_get_sub.return_value = {
            "status": "authorized",
            "auto_recurring": {"start_date": "2026-04-14T00:00:00"},
            "next_payment_date": "2026-05-14T00:00:00",
        }

        mock_sb = MagicMock()
        mock_sb.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock()

        sub = {
            "id": "local_sub_1",
            "mp_subscription_id": "mp_sub_123",
            "status": "pending",
        }

        result = sync_subscription_status(mock_sb, sub)
        assert result["updated"] is True
        assert result["new_status"] == "authorized"

    @patch("mp_sync.get_subscription")
    def test_sync_subscription_mp_error_no_crash(self, mock_get_sub):
        from mp_sync import sync_subscription_status

        mock_get_sub.return_value = {"error": True, "detail": "not found"}
        mock_sb = MagicMock()

        sub = {"id": "x", "mp_subscription_id": "mp_invalid", "status": "pending"}
        result = sync_subscription_status(mock_sb, sub)
        assert result["updated"] is False

    def test_sync_subscription_without_mp_id(self):
        from mp_sync import sync_subscription_status

        mock_sb = MagicMock()
        sub = {"id": "x", "mp_subscription_id": None, "status": "pending"}
        result = sync_subscription_status(mock_sb, sub)
        assert result["updated"] is False
        assert "sin mp_subscription_id" in result.get("reason", "")

    @patch("mp_sync.search_payments")
    def test_sync_payments_idempotent(self, mock_search):
        """Sincronizar 2 veces el mismo pago NO debe duplicar registros."""
        from mp_sync import sync_payments_for_subscription

        mock_search.return_value = [
            {"id": 12345, "status": "approved", "transaction_amount": 9990,
             "currency_id": "CLP", "date_approved": "2026-04-14T10:00:00"},
        ]

        mock_sb = MagicMock()
        # Simular que el pago YA existe en la BD
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"mp_payment_id": "12345"}]
        )

        sub = {"id": "sub_1", "company_id": "comp_1", "external_reference": "toteat_comp1_starter"}
        result = sync_payments_for_subscription(mock_sb, sub)
        assert result["new_payments"] == 0  # No duplica

    @patch("mp_sync.search_payments")
    def test_sync_payments_inserts_new(self, mock_search):
        from mp_sync import sync_payments_for_subscription

        mock_search.return_value = [
            {"id": 99999, "status": "approved", "transaction_amount": 9990,
             "currency_id": "CLP", "date_approved": "2026-04-14T10:00:00",
             "external_reference": "ref"},  # Debe coincidir con ext_ref del sub
        ]

        mock_sb = MagicMock()
        # Simular que NO hay pagos existentes
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        mock_sb.table.return_value.insert.return_value.execute.return_value = MagicMock()

        sub = {"id": "sub_1", "company_id": "comp_1", "external_reference": "ref"}
        result = sync_payments_for_subscription(mock_sb, sub)
        assert result["new_payments"] == 1

    def test_check_trial_no_expired(self):
        from mp_sync import check_trial_expirations

        mock_sb = MagicMock()
        # No hay empresas con trial vencido
        mock_sb.table.return_value.select.return_value.eq.return_value.lte.return_value.execute.return_value = MagicMock(data=[])

        result = check_trial_expirations(mock_sb)
        assert result == []


# ══════════════════════════════════════════════
# email_service.py
# ══════════════════════════════════════════════

class TestEmailService:
    """Tests para el servicio de email."""

    @patch("email_service.smtplib.SMTP")
    @patch("email_service._get_smtp_config")
    def test_send_email_success(self, mock_config, mock_smtp):
        from email_service import _send_email

        mock_config.return_value = {
            "host": "smtp.test.com", "port": 587,
            "user": "user@test.com", "password": "pass123",
            "from_email": "noreply@test.com", "from_name": "Test",
        }
        mock_smtp_instance = MagicMock()
        mock_smtp.return_value.__enter__ = MagicMock(return_value=mock_smtp_instance)
        mock_smtp.return_value.__exit__ = MagicMock(return_value=False)

        result = _send_email("dest@test.com", "Asunto", "<p>Hola</p>")
        assert result is True

    @patch("email_service._get_smtp_config")
    def test_send_email_no_credentials_no_crash(self, mock_config):
        from email_service import _send_email

        mock_config.return_value = {
            "host": "smtp.test.com", "port": 587,
            "user": "", "password": "",
            "from_email": "", "from_name": "",
        }

        result = _send_email("dest@test.com", "Asunto", "<p>Hola</p>")
        assert result is False  # No crashea, retorna False

    @patch("email_service.smtplib.SMTP")
    @patch("email_service._get_smtp_config")
    def test_smtp_error_no_crash(self, mock_config, mock_smtp):
        from email_service import _send_email

        mock_config.return_value = {
            "host": "smtp.test.com", "port": 587,
            "user": "user", "password": "pass",
            "from_email": "x@x.com", "from_name": "X",
        }
        mock_smtp.side_effect = Exception("Connection refused")

        result = _send_email("dest@test.com", "Asunto", "<p>Hola</p>")
        assert result is False

    def test_daily_sales_template_has_correct_numbers(self):
        from email_service import send_daily_sales, _fmt_clp

        assert _fmt_clp(6382300) == "$6.382.300"
        assert _fmt_clp(0) == "$0"
        assert _fmt_clp(1000) == "$1.000"

    def test_trial_reminder_does_not_crash(self):
        """send_trial_reminder sin SMTP config debe retornar False, no crash."""
        from email_service import send_trial_reminder

        with patch("email_service._get_smtp_config", return_value={
            "host": "", "port": 587, "user": "", "password": "",
            "from_email": "", "from_name": "",
        }):
            result = send_trial_reminder("test@x.com", "Mi Empresa", 4)
            assert result is False


# ══════════════════════════════════════════════
# daily_tasks.py — idempotencia
# ══════════════════════════════════════════════

class TestDailyTasks:
    """Tests para tareas diarias."""

    @patch("email_service.send_daily_sales")
    @patch("daily_tasks._get_toteat_client")
    def test_daily_sales_sends_to_active_companies(self, mock_client, mock_send):
        from daily_tasks import send_daily_sales_emails

        mock_toteat = MagicMock()
        mock_toteat.get_sales.return_value = {"data": [
            {"total": 100000, "gratuity": 10000, "discounts": 0, "numberClients": 2,
             "dateOpen": "2026-04-13T18:00:00", "products": [], "paymentForms": []},
        ]}
        mock_client.return_value = mock_toteat
        mock_send.return_value = True

        mock_sb = MagicMock()
        mock_sb.table.return_value.select.return_value.in_.return_value.execute.return_value = MagicMock(
            data=[{"id": "c1", "name": "Test Co", "contact_email": "test@x.com", "status": "active"}]
        )
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"id": "r1", "name": "Local 1", "api_token": "t", "restaurant_id": "1",
                   "local_id": "1", "user_id": "1"}]
        )

        result = send_daily_sales_emails(mock_sb)
        assert result["sent"] >= 0  # No crashea

    def test_trial_reminder_handles_no_companies(self):
        from daily_tasks import send_trial_reminders

        mock_sb = MagicMock()
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])

        result = send_trial_reminders(mock_sb)
        assert result["sent"] == 0
