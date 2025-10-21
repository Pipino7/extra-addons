# -*- coding: utf-8 -*-
from odoo import models

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def open_variant_credentials(self):
        """Abre la vista de credenciales usando la primera variante del template."""
        self.ensure_one()
        product = self.product_variant_id
        if product:
            return product.action_view_credentials()
        return False
