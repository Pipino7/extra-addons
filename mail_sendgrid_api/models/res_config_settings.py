# -*- coding: utf-8 -*-
##### Extiende la configuración de Odoo para incluir opciones de SendGrid

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    sendgrid_api_key = fields.Char(
        string="SendGrid API Key",
        config_parameter='sendgrid.api_key',
        help="Clave de API de SendGrid. Obtén una en: https://app.sendgrid.com/settings/api_keys"
    )

    sendgrid_default_from_email = fields.Char(
        string="Email Remitente por Defecto",
        config_parameter='sendgrid.default_from_email',
        help="Email que aparecerá como remitente por defecto"
    )

    sendgrid_default_from_name = fields.Char(
        string="Nombre Remitente por Defecto",
        config_parameter='sendgrid.default_from_name',
        help="Nombre que aparecerá como remitente por defecto"
    )

    sendgrid_enabled = fields.Boolean(
        string="Usar SendGrid para envío de emails",
        config_parameter='sendgrid.enabled',
        help="Si está activado, se usará SendGrid en lugar de SMTP"
    )

    def action_test_sendgrid_connection(self):
        """Prueba la conexión con SendGrid"""
        self.ensure_one()
        
        if not self.sendgrid_api_key:
            raise UserError(_("Por favor, configura primero la API Key de SendGrid"))
        
        result = self.env['sendgrid.mailer'].test_connection()
        
        if result['success']:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Conexión Exitosa'),
                    'message': result['message'],
                    'type': 'success',
                    'sticky': False,
                }
            }
        else:
            raise UserError(result['message'])
