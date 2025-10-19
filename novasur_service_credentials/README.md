# Novasur - Servicios Digitales

Módulo para la gestión de credenciales de servicios digitales en Odoo 18.

## 📋 Características

- ✅ **Gestión centralizada** de credenciales digitales (Spotify, Netflix, YouTube, etc.)
- ✅ **Asignación automática** de credenciales al confirmar ventas
- ✅ **Control de estados**: Disponible, Asignado, Expirado, Pendiente de reinicio
- ✅ **Encriptación** de contraseñas en base de datos (Base64)
- ✅ **Notificaciones por email** al cliente con las credenciales
- ✅ **CRON automático** para marcar credenciales expiradas
- ✅ **CRON de advertencia** para credenciales próximas a expirar
- ✅ **Integración completa** con productos y órdenes de venta
- ✅ **Seguimiento de asignaciones** (Chatter)
- ✅ **Smart buttons** en productos para ver credenciales disponibles
- ✅ **Permisos granulares** por grupo de usuario
- ✅ **Reenvío manual** de credenciales por email

## 🏗️ Arquitectura Modular

```
models/
├── service_credentials.py         # Modelo principal (campos, validaciones, acciones básicas)
├── service_credentials_assign.py  # Lógica de asignación y envío de emails
└── service_credentials_cron.py    # Tareas automatizadas (expiración, advertencias)
```

Esta arquitectura modular permite:
- 📦 **Separación de responsabilidades**: Cada archivo tiene un propósito específico
- 🔧 **Mantenimiento sencillo**: Modificar una funcionalidad sin afectar otras
- 🧪 **Testing independiente**: Probar cada componente por separado
- 📖 **Código más legible**: Archivos más cortos y enfocados

## 🚀 Instalación

1. Copiar el módulo en la carpeta de addons
2. Actualizar lista de aplicaciones en Odoo
3. Buscar "Novasur - Servicios Digitales"
4. Hacer clic en "Instalar"

## 📖 Uso

### 1. Configurar Productos como Servicios Digitales

1. Ir a **Inventario > Productos > Productos**
2. Abrir el producto deseado (ej: Spotify Premium)
3. En la pestaña **Ventas**, marcar:
   - ☑️ **Es Servicio Digital**
   - ☑️ **Asignar Credenciales Automáticamente**

### 2. Crear Credenciales

1. Ir a **Servicios Digitales > Credenciales**
2. Hacer clic en **Crear**
3. Completar:
   - **Servicio**: Seleccionar el producto
   - **Correo / Usuario**: usuario@servicio.com
   - **Contraseña**: ********
4. Guardar

### 3. Venta con Asignación Automática

1. Crear una orden de venta normalmente
2. Agregar productos marcados como "Servicio Digital"
3. Al **Confirmar la venta**:
   - Se asigna automáticamente una credencial disponible
   - Se envía un email al cliente con las credenciales
   - La credencial cambia a estado "Asignado"

### 4. Gestión de Credenciales

**Estados disponibles:**
- **Disponible**: Credencial lista para ser asignada
- **Asignado**: Credencial en uso por un cliente
- **Expirado**: Credencial caducada
- **Pendiente de reinicio**: Marcada para reiniciar y reusar

**Acciones disponibles:**
- **Marcar para reinicio**: Cuando un cliente deja de usar el servicio
- **Reiniciar cuenta**: Libera la credencial para nuevo uso
- **Marcar como expirado**: Cuando la credencial ya no es válida

## 🔐 Seguridad

- Las contraseñas se almacenan encriptadas en base64
- Solo los Sales Managers pueden ver las contraseñas
- Auditoría completa de cambios (Chatter)
- Permisos por grupo de usuario

## ⚙️ Configuración Avanzada

### CRON Job
El sistema incluye un CRON que se ejecuta diariamente para:
- Marcar automáticamente como expiradas las credenciales con fecha de expiración vencida

Para configurarlo:
1. Ir a **Configuración > Técnico > Automatización > Acciones Programadas**
2. Buscar "Marcar Credenciales Expiradas"
3. Ajustar frecuencia según necesidad

### Template de Email
Personalizar el email enviado a los clientes:
1. Ir a **Configuración > Técnico > Email > Plantillas**
2. Buscar "Credenciales de Servicio Digital - Asignación"
3. Editar HTML según diseño corporativo

## 📊 Reportes y Estadísticas

Desde el formulario de producto, puedes ver:
- Total de credenciales creadas
- Credenciales disponibles
- Credenciales asignadas

Vista Kanban agrupada por estado para gestión visual.

## 🐛 Solución de Problemas

### No se asignan credenciales automáticamente
- Verificar que el producto tenga marcado "Es Servicio Digital" y "Asignar Credenciales Automáticamente"
- Confirmar que existan credenciales en estado "Disponible"

### Email no se envía
- Verificar configuración de servidor de correo en Odoo
- Revisar que el cliente tenga un email válido
- Verificar logs en modo debug

### Contraseña no visible
- Solo usuarios con rol "Sales Manager" pueden ver contraseñas
- Verificar permisos del usuario

## 👥 Permisos

| Grupo | Lectura | Escritura | Creación | Eliminación |
|-------|---------|-----------|----------|-------------|
| Sales Manager | ✅ | ✅ | ✅ | ✅ |
| Salesperson | ✅ | ❌ | ❌ | ❌ |
| User | ✅ | ❌ | ❌ | ❌ |
| Portal | ✅ | ❌ | ❌ | ❌ |

## 📝 Changelog

### Version 18.0.1.0.0
- Versión inicial
- Gestión completa de credenciales
- Asignación automática
- Encriptación de contraseñas
- Notificaciones por email
- CRON de expiración
- Integración con productos y ventas

## 🤝 Soporte

Para soporte, contactar a: **soporte@novasur.cl**

## 📄 Licencia

LGPL-3

## 👨‍💻 Autor

**Novasur**
- Website: https://www.novasur.cl
