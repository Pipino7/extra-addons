# -*- coding: utf-8 -*-
##### Archivo principal del modelo de credenciales digitales.
##### Define los campos, validaciones y métodos base (sin lógica de asignación ni cron).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import base64
import logging

_logger = logging.getLogger(__name__)


class ServiceCredentials(models.Model):
    _name = "service.credentials"
    _description = "Credenciales de servicios digitales"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "product_id, state, login"
    _rec_name = "login"

    ##### Campos principales #####
    
    product_id = fields.Many2one(
        "product.product",
        string="Servicio",
        required=True,
        ondelete='restrict',
        tracking=True,
        help="Producto o servicio digital (Spotify, Netflix, etc.)"
    )

    login = fields.Char(
        string="Correo / Usuario",
        required=True,
        tracking=True,
        help="Email o nombre de usuario para acceder al servicio"
    )

    password = fields.Char(
        string="Contraseña",
        compute='_compute_password',
        inverse='_inverse_password',
        store=False,
        groups="base.group_system",
        help="Contraseña desencriptada (solo visible para administradores del sistema)"
    )

    password_encrypted = fields.Binary(
        string="Contraseña Encriptada",
        groups="base.group_system"
    )

    state = fields.Selection([
        ('available', 'Disponible'),
        ('assigned', 'Asignado'),
        ('expired', 'Expirado'),
        ('pending_reset', 'Pendiente de reinicio'),
    ], string="Estado", default="available", tracking=True, required=True)

    ##### Campos relacionados con ventas #####
    
    sale_line_id = fields.Many2one(
        "sale.order.line",
        string="Línea de venta asignada",
        ondelete='set null',
        readonly=True,
        tracking=True,
        help="Línea de venta a la que está asignada esta credencial"
    )
    
    sale_order_id = fields.Many2one(
        "sale.order",
        string="Orden de venta",
        related="sale_line_id.order_id",
        store=True,
        readonly=True
    )
    
    partner_id = fields.Many2one(
        "res.partner",
        string="Cliente",
        related="sale_order_id.partner_id",
        store=True,
        readonly=True
    )

    ##### Campos de fechas y control #####
    
    assign_date = fields.Datetime(
        string="Fecha de asignación",
        readonly=True,
        tracking=True,
        help="Fecha en que se asignó la credencial"
    )
    
    expire_date = fields.Datetime(
        string="Fecha de expiración",
        tracking=True,
        help="Fecha en que expira el servicio"
    )

    notes = fields.Text(string="Notas")
    
    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        default=lambda self: self.env.company,
        required=True
    )
    
    active = fields.Boolean(default=True, tracking=True)

    ##### Restricciones SQL #####
    
    _sql_constraints = [
        ('unique_login_per_product',
         'unique(product_id, login)',
         'El login debe ser único por servicio.'),
    ]

    ##### Métodos de cifrado #####
    
    def _compute_password(self):
        """Desencripta la contraseña para mostrarla"""
        for rec in self:
            if rec.password_encrypted:
                try:
                    rec.password = base64.b64decode(rec.password_encrypted).decode('utf-8')
                except Exception as e:
                    _logger.error(f"Error al desencriptar contraseña: {e}")
                    rec.password = ''
            else:
                rec.password = ''

    def _inverse_password(self):
        """Encripta la contraseña antes de guardarla"""
        for rec in self:
            if rec.password:
                rec.password_encrypted = base64.b64encode(rec.password.encode('utf-8'))

    ##### Validaciones #####
    
    @api.constrains('password_encrypted')
    def _check_password_not_empty(self):
        """Valida que la contraseña no esté vacía"""
        for rec in self:
            if not rec.password_encrypted:
                raise ValidationError(_("La contraseña no puede estar vacía."))

    @api.constrains('login')
    def _check_login_not_empty(self):
        """Valida que el login no esté vacío"""
        for rec in self:
            if not rec.login or not rec.login.strip():
                raise ValidationError(_("El login/correo no puede estar vacío."))

    @api.constrains('sale_line_id', 'state')
    def _check_sale_line_consistency(self):
        """Valida consistencia entre línea de venta y estado"""
        for rec in self:
            if rec.sale_line_id and rec.state == 'available':
                raise ValidationError(
                    _("Una credencial asignada no puede estar en estado disponible.")
                )
            if not rec.sale_line_id and rec.state == 'assigned':
                raise ValidationError(
                    _("Una credencial en estado asignado debe tener una línea de venta.")
                )

    ##### Helpers visuales #####
    
    def name_get(self):
        """Mejora la visualización del registro"""
        return [(rec.id, f"{rec.product_id.name} - {rec.login}") for rec in self]

    ##### Acciones básicas de cambio de estado #####
    
    def action_mark_pending_reset(self):
        """Marca la credencial como pendiente de reinicio"""
        for rec in self:
            if rec.state != 'assigned':
                raise UserError(
                    _("Solo se pueden marcar como pendientes de reinicio las credenciales asignadas.")
                )
            rec.state = 'pending_reset'
            rec.message_post(
                body=_("Credencial marcada como pendiente de reinicio"),
                subject=_("Pendiente de Reinicio")
            )
            _logger.info(f"Credencial {rec.login} marcada como pendiente de reinicio")

    def action_reset_account(self):
        """Reinicia una cuenta para volverla disponible"""
        for rec in self:
            if rec.state != 'pending_reset':
                raise UserError(
                    _("Solo se pueden reiniciar credenciales pendientes de reinicio.")
                )
            
            rec.write({
                'state': 'available',
                'sale_line_id': False,
                'assign_date': False,
                'expire_date': False,
            })
            rec.message_post(
                body=_("Credencial reiniciada y disponible nuevamente"),
                subject=_("Cuenta Reiniciada")
            )
            _logger.info(f"Credencial {rec.login} reiniciada y disponible")

    def action_mark_expired(self):
        """Marca la credencial como expirada"""
        for rec in self:
            rec.state = 'expired'
            rec.message_post(
                body=_("Credencial marcada como expirada"),
                subject=_("Credencial Expirada")
            )
            _logger.info(f"Credencial {rec.login} marcada como expirada")

    def action_make_available(self):
        """Marca la credencial como disponible (solo si no está asignada)"""
        for rec in self:
            if rec.sale_line_id:
                raise UserError(
                    _("No se puede marcar como disponible una credencial asignada a una venta.")
                )
            rec.write({
                'state': 'available',
                'assign_date': False,
                'expire_date': False,
            })
            rec.message_post(
                body=_("Credencial marcada como disponible"),
                subject=_("Disponible")
            )
