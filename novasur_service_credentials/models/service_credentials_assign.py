# -*- coding: utf-8 -*-
##### Este archivo contiene la lógica de negocio relacionada con la
##### asignación automática de credenciales a ventas y el envío de correos.

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class ServiceCredentialsAssign(models.Model):
    _inherit = "service.credentials"

    @api.model
    def get_available_credential(self, product_id):
        """
        Busca la primera credencial disponible para un producto específico.
        
        :param product_id: ID del producto
        :return: Recordset de service.credentials o False
        """
        credential = self.search([
            ('product_id', '=', product_id),
            ('state', '=', 'available'),
            ('active', '=', True)
        ], limit=1, order='id asc')
        
        if not credential:
            _logger.warning(f"No hay credenciales disponibles para el producto ID {product_id}")
        
        return credential

    def assign_to_sale_line(self, sale_line, expire_date=False):
        """
        Asigna una credencial a una línea de venta y envía correo al cliente.
        
        :param sale_line: Recordset de sale.order.line
        :param expire_date: Fecha de expiración opcional (datetime)
        :return: True si se asignó correctamente
        """
        self.ensure_one()
        
        # Validar que la credencial esté disponible
        if self.state != 'available':
            raise UserError(_("Solo se pueden asignar credenciales disponibles."))

        # Preparar valores para actualizar
        vals = {
            'state': 'assigned',
            'sale_line_id': sale_line.id,
            'assign_date': fields.Datetime.now(),
        }
        
        if expire_date:
            vals['expire_date'] = expire_date

        self.write(vals)

        # Enviar correo con credenciales al cliente
        self._send_credential_email()

        # Registrar en el chatter
        self.message_post(
            body=_("Credencial asignada a la orden %s para el cliente %s") % (
                sale_line.order_id.name,
                self.partner_id.name
            ),
            subject=_("Credencial Asignada")
        )
        
        _logger.info(
            f"Credencial {self.login} asignada exitosamente a la orden {sale_line.order_id.name}"
        )
        
        return True

    def _send_credential_email(self):
        """
        Envía el email con las credenciales al cliente.
        Método privado para separar la lógica de envío.
        """
        try:
            template = self.env.ref(
                'novasur_service_credentials.email_template_credential_assigned',
                raise_if_not_found=False
            )
            
            if not template:
                _logger.warning("No se encontró la plantilla de email para credenciales")
                return False
            
            if not self.partner_id.email:
                _logger.warning(
                    f"El cliente {self.partner_id.name} no tiene email configurado. "
                    f"No se envió la credencial."
                )
                return False
            
            # Enviar email
            template.send_mail(self.id, force_send=True)
            
            _logger.info(
                f"Correo de credenciales enviado exitosamente a {self.partner_id.email} "
                f"para el servicio {self.product_id.name}"
            )
            
            # Registrar envío en el chatter
            self.message_post(
                body=_("✅ Email enviado a %s con las credenciales de acceso") % self.partner_id.email,
                subject=_("Email Enviado")
            )
            
            return True
            
        except Exception as e:
            _logger.error(
                f"Error al enviar email de credenciales para {self.login}: {e}",
                exc_info=True
            )
            
            # Registrar fallo en el chatter
            self.message_post(
                body=_("⚠️ No se pudo enviar el email con las credenciales: %s") % str(e),
                subject=_("Error en Envío de Email")
            )
            
            return False

    def action_resend_credential_email(self):
        """
        Acción manual para reenviar el email con las credenciales.
        Útil si el envío inicial falló o el cliente lo solicitó.
        """
        for rec in self:
            if rec.state != 'assigned':
                raise UserError(
                    _("Solo se pueden enviar credenciales de cuentas asignadas.")
                )
            
            if not rec.partner_id.email:
                raise UserError(
                    _("El cliente %s no tiene un email configurado.") % rec.partner_id.name
                )
            
            if rec._send_credential_email():
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Email Reenviado'),
                        'message': _('Las credenciales han sido reenviadas exitosamente a %s') % rec.partner_id.email,
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                raise UserError(
                    _("No se pudo enviar el email. Revise los logs para más detalles.")
                )
