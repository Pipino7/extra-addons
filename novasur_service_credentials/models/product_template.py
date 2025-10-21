# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # Campos duplicados visuales (mismos que en product.product)
    is_digital_service = fields.Boolean(
        string="Es Servicio Digital",
        help="Marque si este producto requiere asignación de credenciales"
    )

    auto_assign_credentials = fields.Boolean(
        string="Asignar Credenciales Automáticamente",
        help="Si está marcado, se asignará automáticamente una credencial al confirmar la venta"
    )

    # 🔹 Campos de resumen relacionados con la variante principal
    credential_count = fields.Integer(
        string='Total Credenciales',
        related='product_variant_id.credential_count',
        store=False
    )

    available_credential_count = fields.Integer(
        string='Credenciales Disponibles',
        related='product_variant_id.available_credential_count',
        store=False
    )

    assigned_credential_count = fields.Integer(
        string='Credenciales Asignadas',
        related='product_variant_id.assigned_credential_count',
        store=False
    )

    def open_variant_credentials(self):
        """Abre las credenciales de la primera variante del producto template."""
        self.ensure_one()
        product = self.product_variant_id
        if product:
            return product.action_view_credentials()
        return False
