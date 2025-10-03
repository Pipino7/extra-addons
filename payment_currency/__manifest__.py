# -*- coding: utf-8 -*-

{
    'name': 'Monedas metodos de pagos',
    'category': 'Website / Sale / Payment',
    'author': 'Jeffry',
    'summary': 'Adquirente de pagos: Monedas permitidas o Forzar conversión a moneda',
    'website': 'https://astrolynx.cl',
    'version': "18.0",
    'description': """Monedas del adquirente de pagos o Forzar conversión a moneda""",
    'depends': [
                'payment',
            ],
    'external_dependencies': {
            'python': [],
    },
    'data': [
        'views/payment_acquirer.xml',
    ],
    'installable': True,
    'application': True,
}
