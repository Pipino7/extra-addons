# -*- coding: utf-8 -*-
import base64
import hashlib
import hmac
import json
import logging
import requests
from werkzeug import urls
from odoo import fields, api, models, _
from odoo.exceptions import ValidationError
from odoo.addons.payment.models.payment_provider import ValidationError

_logger = logging.getLogger(__name__)

KHIPU_API_BASE = "https://payment-api.khipu.com"
KHIPU_API_SANDBOX = "https://payment-api.khipu.com" 


class PaymentProviderKhipu(models.Model):
    _inherit = "payment.provider"

    code = fields.Selection(
        selection_add=[("khipu", "Khipu")], 
        ondelete={"khipu": "set default"}
    )
    khipu_api_key = fields.Char(
        string="API Key (x-api-key)", 
        help="La llave secreta de tu cuenta de Khipu.",
    )
    khipu_webhook_secret = fields.Char(
        string="Webhook Secret (firma)",
        help="El secreto para validar la autenticidad de los webhooks de Khipu.",
    )
    khipu_sandbox_mode = fields.Boolean(
        string="Modo Sandbox",
        help="Activa este modo para usar el entorno de pruebas de Khipu (si aplica)."
    )

    def _get_khipu_api_url(self):
        """ Devuelve la URL base de la API de Khipu según el modo. """
        self.ensure_one()
        if self.khipu_sandbox_mode:
            return KHIPU_API_SANDBOX
        return KHIPU_API_BASE

    def _get_webhook_url(self):
        """ Construye la URL para las notificaciones (webhook). """
        return f"{self.get_base_url()}/payment/khipu/webhook"

    def _khipu_make_request(self, endpoint, payload=None, method='POST'):
        """ Método centralizado para hacer llamadas a la API de Khipu. """
        self.ensure_one()
        if not self.khipu_api_key:
            raise ValidationError(_("La API Key de Khipu no está configurada."))
    
        url = f"{self._get_khipu_api_url()}{endpoint}"
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.khipu_api_key,
            "accept": "application/json",
        }
        
        try:
            if method == 'POST':
                resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
            else: # GET
                resp = requests.get(url, headers=headers, timeout=30)
            
            resp.raise_for_status() # Lanza una excepción para errores HTTP 4xx/5xx
        except requests.exceptions.RequestException as e:
            _logger.error("¡¡ERROR CAPTURADO AL CONECTAR CON KHIPU!! Detalles: %s", e)
            _logger.exception("Error de conexión con Khipu: %s", e)
            raise ValidationError(_("No se pudo conectar con Khipu. Por favor, intente de nuevo más tarde."))
        
        return resp.json()


class PaymentTransactionKhipu(models.Model):
    _inherit = 'payment.transaction'

    def _get_specific_rendering_values(self, processing_values):
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'khipu':
            return res
    
        _logger.info("INSPECCIONANDO MÉTODOS DISPONIBLES: %s", dir(self))
        base_url = self.provider_id.get_base_url()
        # Construimos las URLs completas manualmente, apuntando a nuestros controladores.
        return_url = urls.url_join(base_url, '/payment/khipu/return')
        cancel_url = urls.url_join(base_url, '/payment/process')

        payload = {
            "amount": self.amount,
            "currency": self.currency_id.name,
            "subject": self.reference,
            "transaction_id": self.reference,
            "return_url": return_url,      # <- Usamos la URL que construimos
            "cancel_url": cancel_url,
            "notify_url": self.provider_id._get_webhook_url(),
            "notify_api_version": "3.0",
        }
        
        response_data = self.provider_id._khipu_make_request('/v3/payments', payload=payload, method='POST')
    
        payment_id = response_data.get('payment_id')
        payment_url = response_data.get('payment_url')
        if not (payment_id and payment_url):
            raise ValidationError(_("Respuesta inválida de Khipu (faltan payment_id o payment_url)."))
    
        self.provider_reference = payment_id
    
        return {'api_url': payment_url}

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """
        Encuentra la transacción de Khipu usando los datos del webhook.
        """
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != 'khipu' or len(tx) == 1:
            return tx

        payment_id = notification_data.get('payment_id')
        if not payment_id:
            raise ValidationError("Khipu: " + _("El webhook no contenía un 'payment_id'."))

        tx = self.search([
            ('provider_reference', '=', payment_id),
            ('provider_code', '=', 'khipu')
        ], limit=1)
        
        if not tx:
            raise ValidationError(
                "Khipu: " + _("No se encontró ninguna transacción con la referencia: %s", payment_id)
            )
        return tx

    def _process_feedback_data(self, data):
        if self.provider_code != 'khipu':
            return

        status = (data.get("status") or "done").lower()

        if status == "done":
            _logger.info("Pago de Khipu exitoso para la transacción %s. Marcando como 'Hecho'.", self.reference)
            self._set_done()
        elif status in ("pending", "verifying"):
            self._set_pending()
        else:
            detail = (data.get("status_detail") or "").lower()
            error_message = _("Pago en Khipu fallido o cancelado. Estado: %s (%s)", status, detail)
            self._set_error(error_message)

    def _khipu_verify_payment_status(self):
        """ Llama a la API de Khipu para obtener el estado actual del pago. """
        self.ensure_one()
        if not self.provider_reference:
            return

        # Llama a la API de Khipu para obtener el estado
        response_data = self.provider_id._khipu_make_request(
            f'/v3/payments/{self.provider_reference}', 
            method='GET'
        )
        
        # Reutiliza el método de procesamiento estándar
        self._process_feedback_data(response_data)

    def _process_khipu_webhook(self, data, headers):
        """
        Procesa los datos del webhook directamente, sin validación de firma.
        """
        _logger.info(
            "Procesando notificación de Khipu para la transacción %s sin validación de firma.",
            self.reference
        )
        self._process_feedback_data(data)
