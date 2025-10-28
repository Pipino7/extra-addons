# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ProductProduct(models.Model):
    _inherit = 'product.product'

    # 🔹 Campos adicionales
    is_digital_service = fields.Boolean(
        string="Es Servicio Digital",
        help="Marque si este producto requiere asignación de credenciales"
    )

    auto_assign_credentials = fields.Boolean(
        string="Asignar Credenciales Automáticamente",
        help="Si está marcado, se asignará automáticamente una credencial al confirmar la venta"
    )

    credential_ids = fields.One2many(
        'service.credentials',
        'product_id',
        string='Credenciales'
    )

    credential_count = fields.Integer(
        string='Total Credenciales',
        compute='_compute_credential_stats',
        store=False
    )

    available_credential_count = fields.Integer(
        string='Credenciales Disponibles',
        compute='_compute_credential_stats',
        store=False
    )

    assigned_credential_count = fields.Integer(
        string='Credenciales Asignadas',
        compute='_compute_credential_stats',
        store=False
    )

    @api.depends('credential_ids', 'credential_ids.state')
    def _compute_credential_stats(self):
        """Calcula estadísticas de credenciales."""
        for product in self:
            credentials = product.credential_ids.filtered(lambda c: c.active)
            product.credential_count = len(credentials)
            product.available_credential_count = len(
                credentials.filtered(lambda c: c.state == 'available')
            )
            product.assigned_credential_count = len(
                credentials.filtered(lambda c: c.state == 'assigned')
            )

    def action_view_credentials(self):
        """Abre la vista de credenciales del producto."""
        self.ensure_one()
        action = self.env.ref('novasur_service_credentials.action_service_credentials').read()[0]
        action['domain'] = [('product_id', '=', self.id)]
        action['context'] = {
            'default_product_id': self.id,
            'search_default_product_id': self.id,
        }
        return action

    def open_variant_credentials(self):
        """
        Alias de action_view_credentials para compatibilidad con product.template.
        Abre la vista de credenciales del producto.
        """
        return self.action_view_credentials()
