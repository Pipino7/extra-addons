# -*- coding: utf-8 -*-

{
    'name': 'Mail SendGrid API',
    'version': '18.0.1.0.0',
    'summary': 'Envío de correos desde Odoo mediante la API REST de SendGrid (sin SMTP)',
    'description': """
        Integración con SendGrid API para envío de emails
        ==================================================
        
        * Envío de correos mediante API REST (HTTPS, puerto 443)
        * No depende de SMTP (ideal para servidores con SMTP bloqueado)
        * Compatible con DigitalOcean, AWS, Google Cloud, etc.
        * Configuración simple mediante parámetros del sistema
        * Logs detallados de envíos
        * Gestión de errores robusta
        * API fácil de usar desde cualquier módulo
    """,
    'category': 'Tools',
    'author': 'Felipe Dev / Novasur',
    'website': 'https://www.novasur.cl',
    'depends': ['base', 'mail'],
    'external_dependencies': {
        'python': ['requests'],
    },
    'data': [
        'views/res_config_settings_views.xml',
        'data/ir_config_parameter.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
