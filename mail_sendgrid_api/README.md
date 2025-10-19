# Mail SendGrid API

Integración de Odoo con SendGrid API para envío de emails mediante HTTPS.

## 🎯 Características

- ✅ **Envío mediante API REST** (HTTPS, puerto 443)
- ✅ **No depende de SMTP** (ideal para servidores con SMTP bloqueado)
- ✅ **Compatible** con DigitalOcean, AWS, Google Cloud, etc.
- ✅ **Configuración simple** mediante UI de Odoo
- ✅ **Logs detallados** de todos los envíos
- ✅ **Gestión de errores robusta**
- ✅ **Soporte para adjuntos** (attachments)
- ✅ **Soporte para CC y BCC**
- ✅ **Templates dinámicos** de SendGrid
- ✅ **Botón de prueba** de conexión

## 📦 Instalación

### 1. Dependencias Python

```bash
pip install requests
```

### 2. Instalar el módulo

1. Copiar el módulo en la carpeta de addons
2. Actualizar lista de aplicaciones en Odoo
3. Buscar "Mail SendGrid API"
4. Hacer clic en "Instalar"

### 3. Obtener API Key de SendGrid

1. Crear cuenta en [SendGrid](https://sendgrid.com/)
2. Ir a [Settings > API Keys](https://app.sendgrid.com/settings/api_keys)
3. Crear nueva API Key con permisos de "Mail Send"
4. Copiar la API Key (solo se muestra una vez)

### 4. Configurar en Odoo

1. Ir a **Configuración > Configuración General**
2. Buscar sección **"SendGrid API"**
3. Completar:
   - ✅ **API Key**: Tu clave de SendGrid
   - ✅ **Email Remitente**: email@tudominio.com
   - ✅ **Nombre Remitente**: Tu Empresa
   - ✅ **Activar**: Marcar checkbox
4. Hacer clic en **"🧪 Probar Conexión"**
5. Guardar

## 🚀 Uso

### Desde Python

#### Envío simple:

```python
self.env['sendgrid.mailer'].send_email(
    to_email='cliente@ejemplo.com',
    subject='Asunto del correo',
    html_content='<h1>Hola</h1><p>Este es un correo de prueba</p>'
)
```

#### Envío completo con todas las opciones:

```python
self.env['sendgrid.mailer'].send_email(
    to_email='cliente@ejemplo.com',
    subject='Orden de Compra #12345',
    html_content='<h1>Tu orden ha sido confirmada</h1>',
    from_email='ventas@miempresa.com',
    from_name='Equipo de Ventas',
    cc_emails=['supervisor@miempresa.com'],
    bcc_emails=['contabilidad@miempresa.com'],
    attachments=[{
        'filename': 'orden_12345.pdf',
        'content': base64_content,  # Contenido en base64
        'type': 'application/pdf'
    }]
)
```

#### Con template dinámico de SendGrid:

```python
self.env['sendgrid.mailer'].send_template_email(
    to_email='cliente@ejemplo.com',
    template_id='d-1234567890abcdef',  # ID del template en SendGrid
    dynamic_data={
        'customer_name': 'Juan Pérez',
        'order_number': '12345',
        'total': '$1,500.00'
    }
)
```

#### Probar conexión:

```python
result = self.env['sendgrid.mailer'].test_connection()
if result['success']:
    print("✅ Conexión exitosa")
else:
    print(f"❌ Error: {result['message']}")
```

### Ejemplo real en un módulo:

```python
class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    def action_confirm(self):
        res = super().action_confirm()
        
        # Enviar email al cliente
        html_content = f"""
            <h2>Orden Confirmada</h2>
            <p>Hola {self.partner_id.name},</p>
            <p>Tu orden <strong>{self.name}</strong> ha sido confirmada.</p>
            <p>Total: <strong>{self.amount_total}</strong></p>
        """
        
        self.env['sendgrid.mailer'].send_email(
            to_email=self.partner_id.email,
            subject=f'Orden Confirmada - {self.name}',
            html_content=html_content
        )
        
        return res
```

## 🔧 Configuración Avanzada

### Parámetros del Sistema

Todos los parámetros se pueden configurar en:
**Configuración > Técnico > Parámetros > Parámetros del Sistema**

| Parámetro | Descripción | Valor por defecto |
|-----------|-------------|-------------------|
| `sendgrid.api_key` | API Key de SendGrid | (vacío) |
| `sendgrid.enabled` | Activar SendGrid | False |
| `sendgrid.default_from_email` | Email remitente | company.email |
| `sendgrid.default_from_name` | Nombre remitente | company.name |

### Templates de SendGrid

Para usar templates dinámicos:

1. Crear template en [SendGrid Templates](https://mc.sendgrid.com/dynamic-templates)
2. Copiar el Template ID (formato: `d-xxxxxxxxxx`)
3. Usar en código:

```python
self.env['sendgrid.mailer'].send_template_email(
    to_email='cliente@ejemplo.com',
    template_id='d-1234567890abcdef',
    dynamic_data={
        'variable1': 'valor1',
        'variable2': 'valor2'
    }
)
```

## 🐛 Solución de Problemas

### Error: "No se ha configurado la API Key"
✅ Verificar que la API Key esté configurada en Configuración > SendGrid API

### Error: "Unauthorized" (401)
✅ La API Key es inválida o ha sido revocada
✅ Generar una nueva en SendGrid

### Error: "Forbidden" (403)
✅ La API Key no tiene permisos de "Mail Send"
✅ Crear nueva API Key con permisos correctos

### Error: "Bad Request" (400)
✅ Email remitente no verificado en SendGrid
✅ Verificar dominio en [Sender Authentication](https://app.sendgrid.com/settings/sender_auth)

### Error: "Connection timeout"
✅ Verificar conexión a internet
✅ Verificar que el puerto 443 (HTTPS) no esté bloqueado

### Emails no llegan
✅ Verificar carpeta de spam
✅ Revisar [Activity Feed](https://app.sendgrid.com/email_activity) en SendGrid
✅ Verificar que el dominio esté verificado

## 📊 Logs

Todos los envíos se registran en el log de Odoo:

- ✅ `INFO`: Email enviado correctamente
- ⚠️ `WARNING`: Advertencias (API Key no configurada, etc.)
- ❌ `ERROR`: Errores en el envío

Ver logs en:
```bash
tail -f /var/log/odoo/odoo-server.log | grep sendgrid
```

## 🔐 Seguridad

- ✅ La API Key se almacena encriptada en la base de datos
- ✅ Solo usuarios con permisos de "Settings" pueden configurarla
- ✅ Se muestra ofuscada en la UI (como password)
- ✅ Los logs NO registran la API Key completa

## 📈 Estadísticas

Ver estadísticas de envíos en SendGrid:
- [Activity Feed](https://app.sendgrid.com/email_activity)
- [Statistics](https://app.sendgrid.com/statistics)

## 🆚 Comparación: SMTP vs SendGrid API

| Característica | SMTP | SendGrid API |
|----------------|------|--------------|
| **Puerto** | 25/587/465 | 443 (HTTPS) |
| **Bloqueado en hosting** | ❌ Frecuentemente | ✅ Nunca |
| **Velocidad** | Lento | Rápido |
| **Estadísticas** | No | ✅ Completas |
| **Gestión de errores** | Básica | ✅ Detallada |
| **Bounce handling** | Manual | ✅ Automático |
| **Tracking** | No | ✅ Si |
| **Templates** | No | ✅ Si |

## 📝 Changelog

### Version 18.0.1.0.0
- ✅ Versión inicial
- ✅ Envío de emails mediante API REST
- ✅ Configuración en UI
- ✅ Soporte para adjuntos
- ✅ Soporte para CC y BCC
- ✅ Templates dinámicos
- ✅ Botón de prueba
- ✅ Logs detallados
- ✅ Gestión de errores completa

## 🤝 Soporte

Para soporte, contactar a: **soporte@novasur.cl**

## 📄 Licencia

LGPL-3

## 👨‍💻 Autor

**Felipe Dev / Novasur**
- Website: https://www.novasur.cl

## 🔗 Enlaces Útiles

- [SendGrid API Documentation](https://docs.sendgrid.com/api-reference/mail-send/mail-send)
- [SendGrid Dashboard](https://app.sendgrid.com/)
- [Pricing](https://sendgrid.com/pricing/)
- [Status Page](https://status.sendgrid.com/)
