# -*- coding: utf-8 -*-

{
    'name': 'Novasur - Servicios Digitales',
    'version': '18.0.1.0.0',
    'summary': 'Gestión de credenciales digitales (Spotify, Netflix, YouTube, etc.)',
    'description': """
        Gestión de Credenciales de Servicios Digitales
        ==============================================
        
        * Asignación automática de credenciales a ventas
        * Control de estados y expiración automática
        * Notificaciones por email a clientes
        * Reinicio y reciclaje de cuentas
        * Reportes y estadísticas
        * Integración completa con productos y ventas
    """,
    'author': 'Novasur',
    'website': 'https://www.novasur.cl',
    'category': 'Sales',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'sale_management',
        'product',
        'mail',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron.xml',
        'data/mail_template.xml',
        'views/service_credentials_views.xml',
        'views/product_product_views.xml',
        'views/sale_order_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
