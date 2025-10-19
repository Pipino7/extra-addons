# -*- coding: utf-8 -*-
##### Este archivo define un conector HTTP para enviar correos mediante la API REST de SendGrid.
##### Ideal para servidores que tienen bloqueo SMTP (como DigitalOcean, AWS, GCP).
##### Se puede usar desde cualquier módulo de Odoo con env['sendgrid.mailer'].send_email()

import requests
import logging
from odoo import models, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class SendGridMailer(models.AbstractModel):
    _name = "sendgrid.mailer"
    _description = "Envío de correos mediante API SendGrid"

    SENDGRID_URL = "https://api.sendgrid.com/v3/mail/send"
    SENDGRID_TIMEOUT = 10  # Segundos

    @api.model
    def _get_api_key(self):
        """
        Obtiene la API Key de SendGrid desde parámetros del sistema.
        
        :return: API Key o None
        """
        api_key = self.env['ir.config_parameter'].sudo().get_param('sendgrid.api_key')
        
        if not api_key:
            _logger.warning("⚠️ No se ha configurado la API Key de SendGrid")
            
        return api_key

    @api.model
    def _get_default_from_email(self):
        """Obtiene el email remitente por defecto"""
        return (
            self.env['ir.config_parameter'].sudo().get_param('sendgrid.default_from_email') or
            self.env.company.email or
            "no-reply@example.com"
        )

    @api.model
    def _get_default_from_name(self):
        """Obtiene el nombre remitente por defecto"""
        return (
            self.env['ir.config_parameter'].sudo().get_param('sendgrid.default_from_name') or
            self.env.company.name or
            "Mi Empresa"
        )

    @api.model
    def send_email(self, to_email, subject, html_content, from_email=None, from_name=None, 
                   cc_emails=None, bcc_emails=None, attachments=None):
        """
        Envía un correo electrónico usando la API REST de SendGrid.
        
        Ventajas sobre SMTP:
        - Usa HTTPS (puerto 443) - no depende del SMTP bloqueado
        - Más rápido y confiable
        - Mejor gestión de errores
        - Estadísticas y tracking disponibles en SendGrid
        
        :param to_email: Email del destinatario (requerido)
        :param subject: Asunto del correo (requerido)
        :param html_content: Contenido HTML del correo (requerido)
        :param from_email: Email del remitente (opcional)
        :param from_name: Nombre del remitente (opcional)
        :param cc_emails: Lista de emails en copia (opcional)
        :param bcc_emails: Lista de emails en copia oculta (opcional)
        :param attachments: Lista de diccionarios con attachments (opcional)
                           Formato: [{'filename': 'doc.pdf', 'content': base64_content, 'type': 'application/pdf'}]
        :return: True si se envió correctamente, lanza UserError si falla
        """
        # Validar API Key
        api_key = self._get_api_key()
        if not api_key:
            raise UserError(_(
                "No se ha configurado la clave API de SendGrid.\n\n"
                "🔧 Configura tu API Key en:\n"
                "Configuración > Técnico > Parámetros > Parámetros del Sistema\n\n"
                "Crea un parámetro con:\n"
                "• Clave: sendgrid.api_key\n"
                "• Valor: tu_api_key_de_sendgrid\n\n"
                "💡 Obtén tu API Key en: https://app.sendgrid.com/settings/api_keys"
            ))

        # Validar parámetros requeridos
        if not to_email:
            raise UserError(_("El email del destinatario es obligatorio"))
        
        if not subject:
            raise UserError(_("El asunto del correo es obligatorio"))
        
        if not html_content:
            raise UserError(_("El contenido del correo es obligatorio"))

        # Obtener valores por defecto
        from_email = from_email or self._get_default_from_email()
        from_name = from_name or self._get_default_from_name()

        # Construir payload base
        personalization = {
            "to": [{"email": to_email}],
            "subject": subject
        }

        # Agregar CC si existe
        if cc_emails:
            personalization["cc"] = [{"email": email} for email in cc_emails if email]

        # Agregar BCC si existe
        if bcc_emails:
            personalization["bcc"] = [{"email": email} for email in bcc_emails if email]

        payload = {
            "personalizations": [personalization],
            "from": {
                "email": from_email,
                "name": from_name
            },
            "content": [{
                "type": "text/html",
                "value": html_content
            }]
        }

        # Agregar attachments si existen
        if attachments:
            payload["attachments"] = []
            for att in attachments:
                if not all(k in att for k in ['filename', 'content']):
                    _logger.warning("Attachment incompleto, requiere 'filename' y 'content'")
                    continue
                
                payload["attachments"].append({
                    "content": att['content'],  # Base64
                    "filename": att['filename'],
                    "type": att.get('type', 'application/octet-stream'),
                    "disposition": "attachment"
                })

        # Headers de la petición
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        # Enviar petición a SendGrid
        try:
            _logger.info(f"📧 Enviando email a {to_email} - Asunto: {subject}")
            
            response = requests.post(
                self.SENDGRID_URL,
                headers=headers,
                json=payload,
                timeout=self.SENDGRID_TIMEOUT
            )

            # Verificar respuesta
            if response.status_code in (200, 202):
                _logger.info(
                    f"✅ Email enviado exitosamente a {to_email}\n"
                    f"   Asunto: {subject}\n"
                    f"   Status: {response.status_code}"
                )
                return True
            else:
                error_msg = response.text
                _logger.error(
                    f"❌ Error de SendGrid:\n"
                    f"   Status: {response.status_code}\n"
                    f"   Destinatario: {to_email}\n"
                    f"   Respuesta: {error_msg}"
                )
                raise UserError(
                    _("Error al enviar email a %s\n\nError de SendGrid (%s):\n%s") % 
                    (to_email, response.status_code, error_msg)
                )

        except requests.exceptions.Timeout:
            error_msg = _("Timeout al conectar con SendGrid (> %s segundos)") % self.SENDGRID_TIMEOUT
            _logger.error(f"⏱️ {error_msg}")
            raise UserError(error_msg)

        except requests.exceptions.ConnectionError as e:
            error_msg = _("Error de conexión con SendGrid API")
            _logger.error(f"🔌 {error_msg}: {e}")
            raise UserError(f"{error_msg}\n\n{str(e)}")

        except requests.exceptions.RequestException as e:
            error_msg = _("Error en la petición HTTP a SendGrid")
            _logger.error(f"💥 {error_msg}: {e}", exc_info=True)
            raise UserError(f"{error_msg}\n\n{str(e)}")

        except Exception as e:
            error_msg = _("Error inesperado al enviar email")
            _logger.error(f"💥 {error_msg}: {e}", exc_info=True)
            raise UserError(f"{error_msg}\n\n{str(e)}")

    @api.model
    def send_template_email(self, to_email, template_id, dynamic_data=None, from_email=None, from_name=None):
        """
        Envía un correo usando un template dinámico de SendGrid.
        
        :param to_email: Email del destinatario
        :param template_id: ID del template en SendGrid
        :param dynamic_data: Diccionario con datos para el template
        :param from_email: Email del remitente (opcional)
        :param from_name: Nombre del remitente (opcional)
        :return: True si se envió correctamente
        """
        api_key = self._get_api_key()
        if not api_key:
            raise UserError(_("No se ha configurado la API Key de SendGrid"))

        from_email = from_email or self._get_default_from_email()
        from_name = from_name or self._get_default_from_name()

        payload = {
            "personalizations": [{
                "to": [{"email": to_email}],
                "dynamic_template_data": dynamic_data or {}
            }],
            "from": {
                "email": from_email,
                "name": from_name
            },
            "template_id": template_id
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        try:
            _logger.info(f"📧 Enviando email con template {template_id} a {to_email}")
            
            response = requests.post(
                self.SENDGRID_URL,
                headers=headers,
                json=payload,
                timeout=self.SENDGRID_TIMEOUT
            )

            if response.status_code in (200, 202):
                _logger.info(f"✅ Email con template enviado exitosamente a {to_email}")
                return True
            else:
                _logger.error(f"❌ Error SendGrid {response.status_code}: {response.text}")
                raise UserError(_("Error de SendGrid: %s") % response.text)

        except Exception as e:
            _logger.error(f"💥 Error al enviar template: {e}", exc_info=True)
            raise UserError(_("No se pudo enviar el correo: %s") % str(e))

    @api.model
    def test_connection(self):
        """
        Prueba la conexión con SendGrid enviando un email de prueba.
        
        :return: Diccionario con resultado de la prueba
        """
        api_key = self._get_api_key()
        
        if not api_key:
            return {
                'success': False,
                'message': _("No se ha configurado la API Key de SendGrid")
            }

        test_email = self._get_default_from_email()
        
        try:
            self.send_email(
                to_email=test_email,
                subject="🧪 Test de Conexión - SendGrid API",
                html_content="""
                    <h2>✅ Conexión Exitosa</h2>
                    <p>Este es un correo de prueba desde Odoo usando SendGrid API.</p>
                    <p>La integración está funcionando correctamente.</p>
                    <hr>
                    <small>Enviado desde: {}</small>
                """.format(self.env.company.name or "Odoo")
            )
            
            return {
                'success': True,
                'message': _("✅ Conexión exitosa. Email de prueba enviado a %s") % test_email
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': _("❌ Error: %s") % str(e)
            }
