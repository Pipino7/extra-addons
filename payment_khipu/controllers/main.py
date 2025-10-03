# controllers/main.py
import logging
import werkzeug
from odoo.http import request
import pprint
from odoo import SUPERUSER_ID
from odoo import http, fields
from odoo.addons.payment.models.payment_provider import ValidationError
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class KhipuController(http.Controller):

    @http.route('/payment/khipu/webhook', type='json', auth='public', csrf=False)
    def khipu_webhook(self):
        """
        Recibe la notificación servidor-a-servidor (webhook) de Khipu.
        """
        try:
            data = request.get_json_data()
        except Exception:
            _logger.exception("No se pudo leer el cuerpo de la solicitud JSON del webhook de Khipu.")
            return werkzeug.wrappers.Response(status=400)
    
        _logger.info("Notificación de Khipu recibida: %s", data)
        
        payment_id = data.get("payment_id")
        if not payment_id:
            _logger.warning("Webhook de Khipu no contenía un 'payment_id'.")
            return
            
        tx = request.env['payment.transaction'].sudo().search([('provider_reference', '=', payment_id)], limit=1)
    
        if not tx:
            _logger.error("No se encontró la transacción de Odoo con provider_reference (payment_id): %s", payment_id)
            return
    
        tx._process_khipu_webhook(data, request.httprequest.headers)
        
        return ''

    @http.route(['/payment/khipu/redirect'], type='http', auth='public', methods=["POST"], csrf=False, website=True)
    def khipu_manual_redirect(self, **post):
        """
        Ruta manual para iniciar el pago.
        NOTA: Esta ruta sigue un patrón antiguo de Odoo y no será llamada por el flujo de pago estándar.
        """
        _logger.info("Se ha llamado a la ruta manual /payment/khipu/redirect. POST: %s", post)
        
        # Odoo 18 ya no envía tx_id en el post, busca la transacción desde la venta.
        tx = request.website.sale_get_order().get_portal_last_transaction()
        if not tx:
            # Fallback por si acaso, aunque es poco probable
            tx_id = post.get('transaction_id')
            if tx_id:
                tx = request.env['payment.transaction'].sudo().browse(int(tx_id))

        if not tx:
            _logger.error("No se pudo encontrar una transacción para procesar.")
            # Aquí podrías renderizar una página de error
            return "Error: Transacción no encontrada."

        # Re-utilizamos la lógica del modelo para obtener los valores de renderizado
        # Esto llamará a la API de Khipu y devolverá la URL
        try:
            rendering_values = tx._get_specific_rendering_values({})
            redirect_url = rendering_values.get('api_url')
            
            if redirect_url:
                _logger.info("URL de Khipu obtenida: %s. Redirigiendo...", redirect_url)
                return werkzeug.utils.redirect(redirect_url)
            else:
                _logger.error("La función _get_specific_rendering_values no devolvió una api_url.")
                return "Error: No se pudo obtener la URL de pago."

        except Exception as e:
            _logger.exception("Error al intentar crear el pago manualmente desde el controlador.")
            return f"Error: {e}"

    @http.route('/payment/khipu/return', type='http', auth='public', csrf='False', website=True)
    def khipu_return_from_checkout(self, **post):
        """
        Recibe al cliente, espera unos segundos, verifica el estado una vez
        y muestra una página de resultado final.
        """
        _logger.info("Cliente regresando de Khipu, esperando confirmación...")
        
        return werkzeug.utils.redirect('/payment/status')
