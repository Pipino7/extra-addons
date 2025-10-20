# -*- coding: utf-8 -*-

from odoo import models, fields, api






class ProductProduct(models.Model):class ProductProduct(models.Model):

    _inherit = 'product.product'    _inherit = 'product.product'

        

    is_digital_service = fields.Boolean(    is_digital_service = fields.Boolean(

        string="Es Servicio Digital",        string="Es Servicio Digital",

        help="Marque si este producto requiere asignación de credenciales"        help="Marque si este producto requiere asignación de credenciales"

    )    )

        

    auto_assign_credentials = fields.Boolean(    auto_assign_credentials = fields.Boolean(

        string="Asignar Credenciales Automáticamente",        string="Asignar Credenciales Automáticamente",

        help="Si está marcado, se asignará automáticamente una credencial al confirmar la venta"        help="Si está marcado, se asignará automáticamente una credencial al confirmar la venta"

    )    )

        

    credential_ids = fields.One2many(    credential_ids = fields.One2many(

        'service.credentials',        'service.credentials',

        'product_id',        'product_id',

        string='Credenciales'        string='Credenciales'

    )    )

        

    credential_count = fields.Integer(    credential_count = fields.Integer(

        string='Total Credenciales',        string='Total Credenciales',

        compute='_compute_credential_stats',        compute='_compute_credential_stats',

        store=False        store=False

    )    )

        

    available_credential_count = fields.Integer(    available_credential_count = fields.Integer(

        string='Credenciales Disponibles',        string='Credenciales Disponibles',

        compute='_compute_credential_stats',        compute='_compute_credential_stats',

        store=False        store=False

    )    )

        

    assigned_credential_count = fields.Integer(    assigned_credential_count = fields.Integer(

        string='Credenciales Asignadas',        string='Credenciales Asignadas',

        compute='_compute_credential_stats',        compute='_compute_credential_stats',

        store=False        store=False

    )    )



    @api.depends('credential_ids', 'credential_ids.state')    @api.depends('credential_ids', 'credential_ids.state')

    def _compute_credential_stats(self):    def _compute_credential_stats(self):

        """Calcula estadísticas de credenciales"""        """Calcula estadísticas de credenciales"""

        for product in self:        for product in self:

            credentials = product.credential_ids.filtered(lambda c: c.active)            credentials = product.credential_ids.filtered(lambda c: c.active)

            product.credential_count = len(credentials)            product.credential_count = len(credentials)

            product.available_credential_count = len(            product.available_credential_count = len(

                credentials.filtered(lambda c: c.state == 'available')                credentials.filtered(lambda c: c.state == 'available')

            )            )

            product.assigned_credential_count = len(            product.assigned_credential_count = len(

                credentials.filtered(lambda c: c.state == 'assigned')                credentials.filtered(lambda c: c.state == 'assigned')

            )            )



    def action_view_credentials(self):    def action_view_credentials(self):

        """Abre la vista de credenciales del producto"""        """Abre la vista de credenciales del producto"""

        self.ensure_one()        self.ensure_one()

        action = self.env.ref('novasur_service_credentials.action_service_credentials').read()[0]        action = self.env.ref('novasur_service_credentials.action_service_credentials').read()[0]

        action['domain'] = [('product_id', '=', self.id)]        action['domain'] = [('product_id', '=', self.id)]

        action['context'] = {        action['context'] = {

            'default_product_id': self.id,            'default_product_id': self.id,

            'search_default_product_id': self.id,            'search_default_product_id': self.id,

        }        }

        return action        return action

