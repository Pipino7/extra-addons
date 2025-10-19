# 📐 ARQUITECTURA DEL MÓDULO - Novasur Service Credentials

## 🎯 Objetivo de la Refactorización

Separar el código en módulos especializados para mejorar:
- **Mantenibilidad**: Cada archivo tiene una responsabilidad única
- **Escalabilidad**: Fácil agregar nuevas funcionalidades
- **Legibilidad**: Archivos más cortos y enfocados
- **Testing**: Probar componentes de forma independiente

---

## 📁 Estructura de Archivos

```
novasur_service_credentials/
│
├── 📄 __init__.py                          # Inicialización del módulo
├── 📄 __manifest__.py                      # Manifiesto con dependencias
├── 📄 README.md                            # Documentación del usuario
├── 📄 ARCHITECTURE.md                      # Este archivo (documentación técnica)
│
├── 📂 models/                              # Lógica de negocio
│   ├── __init__.py                         # Importa todos los modelos
│   ├── service_credentials.py              # 🔵 MODELO BASE
│   ├── service_credentials_assign.py       # 🟢 ASIGNACIÓN Y EMAIL
│   ├── service_credentials_cron.py         # 🟡 TAREAS AUTOMATIZADAS
│   ├── product_product.py                  # 🔶 Extensión de productos
│   └── sale_order.py                       # 🔷 Integración con ventas (HOOK)
│
├── 📂 views/                               # Interfaces de usuario
│   ├── service_credentials_views.xml       # Vistas principales (Kanban, Tree, Form)
│   ├── product_product_views.xml           # Smart buttons en productos
│   └── sale_order_views.xml                # Integración en ventas
│
├── 📂 data/                                # Datos y configuración
│   ├── ir_cron.xml                         # Tareas programadas (CRON)
│   └── mail_template.xml                   # Plantillas de email
│
└── 📂 security/                            # Control de acceso
    └── ir.model.access.csv                 # Permisos por grupo
```

---

## 🔵 MODELO BASE: `service_credentials.py`

### Responsabilidad
Define la **estructura de datos** y la **lógica básica** del modelo.

### Contiene:
✅ **Campos del modelo**
- `product_id` - Servicio digital
- `login` - Usuario/Email
- `password` / `password_encrypted` - Credenciales encriptadas
- `state` - Estado (disponible, asignado, expirado, pendiente_reset)
- `sale_line_id`, `partner_id` - Relaciones
- `assign_date`, `expire_date` - Fechas
- `notes`, `company_id`, `active` - Metadatos

✅ **Validaciones**
- `_check_password_not_empty()` - Contraseña requerida
- `_check_login_not_empty()` - Login requerido
- `_check_sale_line_consistency()` - Consistencia estado/venta

✅ **Métodos de encriptación**
- `_compute_password()` - Desencripta para mostrar
- `_inverse_password()` - Encripta antes de guardar

✅ **Acciones básicas de estado**
- `action_mark_pending_reset()` - Marcar para reinicio
- `action_reset_account()` - Reiniciar cuenta
- `action_mark_expired()` - Marcar expirada
- `action_make_available()` - Marcar disponible

✅ **Helpers**
- `name_get()` - Visualización mejorada

### NO contiene:
❌ Lógica de asignación a ventas
❌ Envío de emails
❌ Tareas automáticas (CRON)

---

## 🟢 ASIGNACIÓN Y EMAIL: `service_credentials_assign.py`

### Responsabilidad
Maneja la **asignación de credenciales a ventas** y el **envío de notificaciones**.

### Hereda de:
```python
_inherit = "service.credentials"
```

### Contiene:
✅ **Búsqueda de credenciales**
- `get_available_credential(product_id)` - Encuentra credencial disponible

✅ **Asignación a ventas**
- `assign_to_sale_line(sale_line, expire_date)` - Asigna credencial a línea de venta

✅ **Envío de emails**
- `_send_credential_email()` - Envía email al cliente (método privado)
- `action_resend_credential_email()` - Reenvío manual desde UI

### Flujo de asignación:
```
1. Venta confirmada
   ↓
2. get_available_credential(product_id)
   ↓
3. assign_to_sale_line(sale_line)
   ↓
4. Actualiza estado → 'assigned'
   ↓
5. _send_credential_email()
   ↓
6. Registra en chatter
```

### Gestión de errores:
- ✅ Log si no hay credenciales disponibles
- ✅ Log si el email falla
- ✅ Registra todo en el chatter
- ✅ No bloquea la venta si falla el email

---

## 🟡 TAREAS AUTOMATIZADAS: `service_credentials_cron.py`

### Responsabilidad
Define **tareas programadas** para mantenimiento automático.

### Hereda de:
```python
_inherit = "service.credentials"
```

### Contiene:

#### 1️⃣ CRON: Marcar Expiradas
```python
cron_check_expired_credentials()
```
- **Ejecuta**: Diariamente
- **Activo**: Por defecto ✅
- **Función**: Marca como 'expired' las credenciales con `expire_date` < ahora
- **Notifica**: A administradores via chatter
- **Log**: Detallado de cada credencial expirada

#### 2️⃣ CRON: Advertir Próximas a Expirar
```python
cron_warn_expiring_soon(days_before=7)
```
- **Ejecuta**: Diariamente
- **Activo**: Desactivado por defecto ⚠️
- **Función**: Crea actividades para credenciales que expirarán pronto
- **Parámetro**: `days_before` - Días de anticipación (default: 7)
- **Notifica**: Crea actividades asignadas al admin

### Métodos auxiliares:
- `_notify_admin_expired_credentials()` - Notifica via chatter a admins

---

## 🔄 Flujo de Datos Completo

### Caso de Uso: Cliente compra servicio digital

```mermaid
1. VENTA
   Cliente compra "Spotify Premium"
   └─→ sale_order.action_confirm()
       └─→ sale_order_line._auto_assign_credential()

2. BÚSQUEDA (service_credentials_assign.py)
   └─→ get_available_credential(product_id)
       └─→ Busca: state='available', product_id=X
       └─→ Retorna: credential o False

3. ASIGNACIÓN (service_credentials_assign.py)
   └─→ assign_to_sale_line(sale_line, expire_date)
       ├─→ Actualiza: state='assigned', sale_line_id, assign_date
       ├─→ _send_credential_email()
       │   ├─→ Busca template
       │   ├─→ Envía email con login/password
       │   └─→ Registra en chatter
       └─→ message_post() - "Credencial asignada"

4. CLIENTE
   └─→ Recibe email con:
       ├─→ Servicio: Spotify Premium
       ├─→ Usuario: user@spotify.com
       ├─→ Contraseña: Pass123!
       └─→ Fecha expiración: 2025-11-17

5. MONITOREO AUTOMÁTICO (service_credentials_cron.py)
   └─→ CRON diario: cron_check_expired_credentials()
       ├─→ Busca: state='assigned', expire_date < ahora
       ├─→ Marca como: state='expired'
       └─→ Notifica administradores
```

---

## � INTEGRACIÓN CON VENTAS: `sale_order.py`

### Responsabilidad
Conecta el flujo de ventas con la **asignación automática de credenciales**.

### Hereda de:
```python
_inherit = 'sale.order'
_inherit = 'sale.order.line'
```

### Contiene:

#### Modelo: `SaleOrder`

**Campo computado:**
- `has_digital_services` - Detecta si la orden tiene servicios digitales

**Método principal:**
```python
action_confirm()
```
1. **Valida disponibilidad** de credenciales (ANTES de confirmar)
2. Llama a `super().action_confirm()` (confirma la venta)
3. **Asigna credenciales** automáticamente (DESPUÉS de confirmar)

**Método de validación:**
```python
_validate_credentials_availability()
```
- Cuenta credenciales disponibles
- Compara con cantidad solicitada
- Lanza `UserError` si no hay suficientes
- Mensaje detallado con productos faltantes

#### Modelo: `SaleOrderLine`

**Campos:**
- `service_credential_id` - Credencial asignada a esta línea
- `credential_login` - Related (usuario)
- `credential_password` - Related (contraseña, solo admins)
- `credential_state` - Related (estado)

**Métodos:**

```python
_auto_assign_credential()
```
- Busca credencial disponible
- Asigna usando `credential.assign_to_sale_line()`
- Registra en chatter
- Gestión de errores completa

```python
action_assign_credential_manually()
```
- Asignación manual desde UI
- Notificación de éxito
- Validaciones previas

```python
action_view_credential()
```
- Abre formulario de credencial
- Vista rápida desde la línea de venta

### Flujo completo en ventas:

```
1. Usuario agrega servicio digital a orden
   └─→ Campo is_digital_service = True

2. Usuario hace clic en "Confirmar"
   └─→ action_confirm() se ejecuta

3. VALIDACIÓN (ANTES de confirmar)
   └─→ _validate_credentials_availability()
       ├─→ Cuenta credenciales disponibles
       ├─→ Compara con cantidad solicitada
       └─→ Si faltan → UserError (bloquea venta)

4. CONFIRMACIÓN
   └─→ super().action_confirm()
       └─→ Orden confirmada en Odoo

5. ASIGNACIÓN (DESPUÉS de confirmar)
   └─→ Para cada línea con is_digital_service:
       └─→ _auto_assign_credential()
           ├─→ get_available_credential()
           ├─→ assign_to_sale_line()
           │   ├─→ Actualiza estado
           │   └─→ _send_credential_email()
           └─→ Registra en chatter

6. RESULTADO
   ├─→ Cliente recibe email con credenciales
   ├─→ Credencial marcada como 'assigned'
   └─→ Trazabilidad completa en la orden
```

### Características especiales:

✅ **Validación preventiva**
- Evita confirmar ventas sin stock digital
- Mensaje claro al usuario
- Lista productos faltantes

✅ **Alerta visual en UI**
- Banner azul informativo
- "Esta orden contiene servicios digitales"
- Solo visible en borrador

✅ **Gestión de errores robusta**
- Logs detallados
- Mensajes en chatter
- No bloquea la venta si falla el email
- Solo bloquea si no hay credenciales

✅ **Trazabilidad completa**
- Credencial visible en línea de venta
- Estado de credencial en tiempo real
- Botón para ver credencial completa

---

## �🔌 Extensibilidad

### Agregar nueva funcionalidad: Historial de uso

**Opción 1: Nuevo archivo** (Recomendado)
```python
# models/service_credentials_history.py
class ServiceCredentialsHistory(models.Model):
    _inherit = "service.credentials"
    
    history_ids = fields.One2many('service.credentials.history', 'credential_id')
    
    def log_usage(self, action):
        # Lógica de historial
        pass
```

**Opción 2: Extender archivo existente**
```python
# Agregar en service_credentials.py si es lógica muy básica
```

### Agregar nueva acción: Renovar automáticamente

```python
# models/service_credentials_renewal.py
class ServiceCredentialsRenewal(models.Model):
    _inherit = "service.credentials"
    
    auto_renewal = fields.Boolean("Renovación Automática")
    
    def action_auto_renew(self):
        # Lógica de renovación
        pass
```

---

## 🧪 Testing

### Separación permite testing modular:

```python
# tests/test_service_credentials_base.py
class TestServiceCredentialsBase(TransactionCase):
    def test_password_encryption(self):
        # Prueba solo encriptación
        pass

# tests/test_service_credentials_assign.py
class TestServiceCredentialsAssign(TransactionCase):
    def test_assign_to_sale(self):
        # Prueba solo asignación
        pass

# tests/test_service_credentials_cron.py
class TestServiceCredentialsCron(TransactionCase):
    def test_expire_credentials(self):
        # Prueba solo CRON
        pass
```

---

## 📊 Comparación: Antes vs Después

### ❌ ANTES (Monolítico)
```
service_credentials.py  (300 líneas)
├─ Campos
├─ Validaciones
├─ Encriptación
├─ Acciones de estado
├─ Asignación a ventas
├─ Envío de emails
└─ CRON jobs
```
**Problemas:**
- 🔴 Difícil de mantener
- 🔴 Difícil de testear
- 🔴 Difícil de extender
- 🔴 Mezcla de responsabilidades

### ✅ DESPUÉS (Modular)
```
models/
├─ service_credentials.py (180 líneas)
│  └─ Campos, validaciones, acciones básicas
│
├─ service_credentials_assign.py (140 líneas)
│  └─ Asignación + emails
│
└─ service_credentials_cron.py (150 líneas)
   └─ Tareas automatizadas
```
**Ventajas:**
- ✅ Fácil de mantener
- ✅ Fácil de testear
- ✅ Fácil de extender
- ✅ Separación clara de responsabilidades

---

## 📝 Convenciones de Código

### Comentarios
```python
##### Título de sección (5 #)
# Comentario normal (1 #)
"""Docstring para funciones/clases"""
```

### Logging
```python
_logger.info("Operación exitosa: %s", variable)
_logger.warning("Advertencia: %s", mensaje)
_logger.error("Error: %s", error, exc_info=True)
```

### Mensajes de chatter
```python
self.message_post(
    body=_("Mensaje al usuario"),
    subject=_("Asunto"),
    subtype_xmlid='mail.mt_note'  # O mail.mt_comment
)
```

---

## 🚀 Próximos Pasos

### Fase 2: Mejoras
- [ ] Tests unitarios completos
- [ ] Dashboard con gráficos
- [ ] Reportes PDF
- [ ] Widget de búsqueda avanzada

### Fase 3: Integraciones
- [ ] API REST para servicios externos
- [ ] Webhook de servicios (Spotify, Netflix)
- [ ] Sincronización de estados
- [ ] Portal del cliente

---

## 👨‍💻 Mantenimiento

### Para agregar funcionalidad:
1. ✅ Identificar responsabilidad (¿Qué hace?)
2. ✅ Elegir archivo apropiado o crear nuevo
3. ✅ Heredar modelo: `_inherit = "service.credentials"`
4. ✅ Agregar import en `models/__init__.py`
5. ✅ Documentar en este archivo

### Para modificar funcionalidad:
1. ✅ Identificar archivo responsable
2. ✅ Modificar solo ese archivo
3. ✅ Actualizar tests si existen
4. ✅ Actualizar documentación

---

**Autor**: Novasur  
**Versión**: 18.0.1.0.0  
**Fecha**: Octubre 2025
