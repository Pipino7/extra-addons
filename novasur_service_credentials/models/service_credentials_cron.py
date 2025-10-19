# -*- coding: utf-8 -*-
##### Este archivo define la tarea automática (cron job)
##### que revisa credenciales expiradas y las marca como "Expiradas".

from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class ServiceCredentialsCron(models.Model):
    _inherit = "service.credentials"

    @api.model
    def cron_check_expired_credentials(self):
        """
        Revisa diariamente credenciales asignadas cuya fecha de expiración ya pasó.
        Marca automáticamente como 'expired' las credenciales vencidas.
        
        :return: Número de credenciales marcadas como expiradas
        """
        now = fields.Datetime.now()
        
        # Buscar credenciales asignadas con fecha de expiración pasada
        expired_credentials = self.search([
            ('state', '=', 'assigned'),
            ('expire_date', '!=', False),
            ('expire_date', '<', now),
        ])
        
        if not expired_credentials:
            _logger.info("[CRON] No se encontraron credenciales expiradas en esta ejecución.")
            return 0
        
        # Marcar como expiradas
        expired_credentials.action_mark_expired()
        
        # Log consolidado
        _logger.info(
            f"[CRON] Se marcaron {len(expired_credentials)} credenciales como expiradas:\n"
            + "\n".join([
                f"  - {cred.product_id.name} ({cred.login}) - Cliente: {cred.partner_id.name}"
                for cred in expired_credentials
            ])
        )
        
        # Enviar notificación al administrador (opcional)
        self._notify_admin_expired_credentials(expired_credentials)
        
        return len(expired_credentials)

    def _notify_admin_expired_credentials(self, expired_credentials):
        """
        Notifica a los administradores sobre credenciales que expiraron.
        Crea una actividad o envía un email según configuración.
        
        :param expired_credentials: Recordset de credenciales expiradas
        """
        if not expired_credentials:
            return
        
        try:
            # Buscar usuarios administradores para notificar
            admin_users = self.env.ref('base.group_system').users
            
            if not admin_users:
                _logger.warning("No se encontraron usuarios administradores para notificar")
                return
            
            # Crear mensaje para el chatter del primer registro (como referencia)
            body = _(
                "<h3>⚠️ Credenciales Expiradas Automáticamente</h3>"
                "<p>Las siguientes <strong>%s credenciales</strong> han sido marcadas como expiradas:</p>"
                "<ul>%s</ul>"
                "<p><em>Revise si necesitan reinicio o reemplazo.</em></p>"
            ) % (
                len(expired_credentials),
                "".join([
                    f"<li><strong>{cred.product_id.name}</strong> - {cred.login} "
                    f"(Cliente: {cred.partner_id.name})</li>"
                    for cred in expired_credentials
                ])
            )
            
            # Publicar en el primer registro
            expired_credentials[0].message_post(
                body=body,
                subject=_("Notificación Automática: Credenciales Expiradas"),
                partner_ids=admin_users.partner_id.ids,
                subtype_xmlid='mail.mt_note'
            )
            
            _logger.info(f"Notificación enviada a {len(admin_users)} administradores")
            
        except Exception as e:
            _logger.error(f"Error al enviar notificación de credenciales expiradas: {e}")

    @api.model
    def cron_warn_expiring_soon(self, days_before=7):
        """
        CRON OPCIONAL: Advierte sobre credenciales que expirarán pronto.
        Útil para preparar reemplazos antes de que expiren.
        
        :param days_before: Días de anticipación para la advertencia (default: 7)
        :return: Número de credenciales que expirarán pronto
        """
        now = fields.Datetime.now()
        warning_date = fields.Datetime.add(now, days=days_before)
        
        expiring_soon = self.search([
            ('state', '=', 'assigned'),
            ('expire_date', '!=', False),
            ('expire_date', '>', now),
            ('expire_date', '<=', warning_date),
        ])
        
        if not expiring_soon:
            _logger.info(
                f"[CRON] No hay credenciales que expiren en los próximos {days_before} días."
            )
            return 0
        
        _logger.warning(
            f"[CRON] ⚠️ {len(expiring_soon)} credenciales expirarán en los próximos {days_before} días:\n"
            + "\n".join([
                f"  - {cred.product_id.name} ({cred.login}) - "
                f"Expira: {cred.expire_date.strftime('%Y-%m-%d %H:%M')}"
                for cred in expiring_soon
            ])
        )
        
        # Crear actividades para seguimiento
        for cred in expiring_soon:
            cred.activity_schedule(
                'mail.mail_activity_data_todo',
                summary=_('Credencial próxima a expirar'),
                note=_(
                    'La credencial <strong>%s</strong> del servicio <strong>%s</strong> '
                    'expirará el <strong>%s</strong>.<br/>'
                    'Cliente: <strong>%s</strong><br/>'
                    'Considere preparar un reemplazo o renovación.'
                ) % (
                    cred.login,
                    cred.product_id.name,
                    cred.expire_date.strftime('%d/%m/%Y %H:%M'),
                    cred.partner_id.name
                ),
                date_deadline=cred.expire_date.date(),
                user_id=self.env.ref('base.user_admin').id
            )
        
        return len(expiring_soon)
