# -*- coding: utf-8 -*-
##### Este archivo conecta el módulo de credenciales digitales con el flujo de ventas.
##### Al confirmar una orden:
#####   1. Valida que haya stock digital (credenciales disponibles).
#####   2. Asigna automáticamente una credencial al producto vendido.
#####   3. Envía el correo con login/contraseña al cliente.
#####   4. Registra trazabilidad en la orden de venta.

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    has_digital_services = fields.Boolean(
        string="Tiene Servicios Digitales",
        compute='_compute_has_digital_services',
        store=True,
        help="Indica si la orden contiene productos de servicios digitales"
    )

    @api.depends('order_line', 'order_line.product_id', 'order_line.product_id.is_digital_service')
    def _compute_has_digital_services(self):
        """Detecta si la orden tiene productos digitales"""
        for order in self:
            order.has_digital_services = any(
                line.product_id.is_digital_service 
                for line in order.order_line
            )

    def action_confirm(self):
        """
        Extiende la confirmación de la venta:
        - Busca credenciales disponibles para cada producto digital.
        - Si no hay stock y es obligatorio, puede bloquear o advertir.
        - Si hay, asigna y dispara el correo automáticamente.
        """
        # Validar disponibilidad de credenciales ANTES de confirmar
        self._validate_credentials_availability()
        
        # Confirmar la venta
        res = super(SaleOrder, self).action_confirm()
        
        # Asignar credenciales después de confirmar
        for order in self:
            for line in order.order_line:
                if line.product_id.is_digital_service:
                    if line.product_id.auto_assign_credentials and not line.service_credential_id:
                        line._auto_assign_credential()
        
        return res

    def _validate_credentials_availability(self):
        """
        Valida que haya credenciales disponibles para los servicios digitales.
        Lanza UserError si no hay stock para productos con asignación automática.
        """
        for order in self:
            missing_credentials = []
            
            for line in order.order_line:
                product = line.product_id
                
                # Solo validar productos digitales con asignación automática
                if not (product.is_digital_service and product.auto_assign_credentials):
                    continue
                
                # Contar credenciales disponibles
                available_count = self.env['service.credentials'].search_count([
                    ('product_id', '=', product.id),
                    ('state', '=', 'available'),
                    ('active', '=', True)
                ])
                
                if available_count < line.product_uom_qty:
                    missing_credentials.append({
                        'product': product.display_name,
                        'needed': int(line.product_uom_qty),
                        'available': available_count,
                        'missing': int(line.product_uom_qty - available_count)
                    })
            
            if missing_credentials:
                # Construir mensaje de error detallado
                error_lines = [
                    _("⚠️ No hay suficientes credenciales disponibles:\n")
                ]
                for item in missing_credentials:
                    error_lines.append(
                        _("  • %s: Necesitas %d, disponibles %d (faltan %d)") % (
                            item['product'],
                            item['needed'],
                            item['available'],
                            item['missing']
                        )
                    )
                error_lines.append(
                    _("\n💡 Por favor, agrega más credenciales en: Servicios Digitales > Credenciales")
                )
                
                raise UserError("\n".join(error_lines))


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    service_credential_id = fields.Many2one(
        'service.credentials',
        string='Credencial Asignada',
        readonly=True,
        ondelete='set null',
        help='Credencial digital entregada al cliente para este servicio.'
    )
    
    credential_login = fields.Char(
        string='Usuario',
        related='service_credential_id.login',
        readonly=True
    )
    
    credential_password = fields.Char(
        string='Contraseña',
        related='service_credential_id.password',
        readonly=True,
        groups="sales_team.group_sale_manager"
    )
    
    credential_state = fields.Selection(
        string='Estado Credencial',
        related='service_credential_id.state',
        readonly=True
    )

    def _auto_assign_credential(self):
        """
        Asigna automáticamente credenciales al confirmar venta.
        Este método se ejecuta DESPUÉS de confirmar la orden.
        """
        for line in self:
            # Skip si no es servicio digital
            if not line.product_id.is_digital_service:
                continue
            
            # Skip si ya tiene credencial asignada
            if line.service_credential_id:
                _logger.info(
                    f"[SALE] Línea {line.id} ya tiene credencial asignada, saltando..."
                )
                continue
            
            # Buscar credencial disponible
            credential = self.env['service.credentials'].get_available_credential(
                line.product_id.id
            )
            
            if not credential:
                # Esto no debería pasar si la validación previa funcionó
                error_msg = _(
                    "⚠️ No hay credenciales disponibles para el producto: <b>%s</b><br/>"
                    "Por favor, agregue credenciales o asigne manualmente."
                ) % line.product_id.name
                
                line.order_id.message_post(
                    body=error_msg,
                    subject=_("Sin Credenciales Disponibles"),
                    message_type='notification'
                )
                
                _logger.error(
                    f"[SALE ERROR] No hay credenciales para {line.product_id.name} "
                    f"en orden {line.order_id.name}. La validación previa debió detectar esto."
                )
                
                # Si es crítico, descomentar la siguiente línea:
                # raise UserError(error_msg)
                continue
            
            # Asignar credencial
            try:
                credential.assign_to_sale_line(line)
                line.write({'service_credential_id': credential.id})
                
                # Mensaje de éxito en chatter
                line.order_id.message_post(
                    body=_(
                        "✅ Credencial asignada exitosamente:<br/>"
                        "<b>Producto:</b> %s<br/>"
                        "<b>Usuario:</b> %s<br/>"
                        "<b>Cliente:</b> %s"
                    ) % (
                        line.product_id.display_name,
                        credential.login,
                        line.order_id.partner_id.name
                    ),
                    subject=_("Credencial Asignada"),
                    message_type='notification'
                )
                
                _logger.info(
                    f"[SALE] Credencial {credential.login} asignada exitosamente a "
                    f"orden {line.order_id.name}, línea {line.id}"
                )
                
            except Exception as e:
                _logger.error(
                    f"[SALE ERROR] Error al asignar credencial: {e}",
                    exc_info=True
                )
                line.order_id.message_post(
                    body=_(
                        "❌ Error al asignar credencial para: <b>%s</b><br/>"
                        "Error: %s<br/>"
                        "<em>Contacte al administrador del sistema.</em>"
                    ) % (line.product_id.name, str(e)),
                    subject=_("Error en Asignación"),
                    message_type='notification'
                )
                # Relanzar excepción para que el admin se entere
                raise UserError(
                    _("Error al asignar credencial para %s: %s") % 
                    (line.product_id.name, str(e))
                )

    def action_assign_credential_manually(self):
        """Permite asignar manualmente una credencial"""
        self.ensure_one()
        
        if not self.product_id.is_digital_service:
            raise UserError(_("Este producto no es un servicio digital."))
        
        if self.service_credential_id:
            raise UserError(_("Esta línea ya tiene una credencial asignada."))
        
        # Buscar credencial disponible
        credential = self.env['service.credentials'].get_available_credential(
            self.product_id.id
        )
        
        if not credential:
            raise UserError(
                _("No hay credenciales disponibles para el producto: %s") % self.product_id.name
            )
        
        # Asignar
        credential.assign_to_sale_line(self)
        self.service_credential_id = credential.id
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Credencial Asignada'),
                'message': _('Se ha asignado la credencial exitosamente.'),
                'type': 'success',
                'sticky': False,
            }
        }

    def action_view_credential(self):
        """Abre el formulario de la credencial asignada"""
        self.ensure_one()
        
        if not self.service_credential_id:
            raise UserError(_("Esta línea no tiene una credencial asignada."))
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Credencial Asignada'),
            'res_model': 'service.credentials',
            'res_id': self.service_credential_id.id,
            'view_mode': 'form',
            'target': 'new',
        }
