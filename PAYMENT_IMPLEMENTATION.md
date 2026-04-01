# Implementación de Pagos con Mercado Pago - MVP

## Resumen de Implementación

Se ha implementado un flujo de pago **único** (sin suscripciones recurrentes por el momento) usando Mercado Pago Checkout Pro.

**Monto**: 149 MXN (120 + IVA)  
**Proveedor**: Mercado Pago  
**Modelo**: Pago único (fase 2 será suscripciones recurrentes)

---

## Archivos Creados

### Schemas

- `app/schemas/payment_schema.py` - Modelos de request/response para pagos

### Modelos ORM

- `app/models/Payment.py` - Tabla `payments` para guardar preferencias y pagos

### Repositorios

- `app/repositories/payment_repository.py` - CRUD para pagos

### Servicios

- `app/services/payment_service.py` - Lógica de negocio de pagos

### Rutas

- `app/routes/payment_routes.py` - Endpoints REST

### Configuración

- Actualizado: `app/core/dependencies.py` - Inyección de dependencias
- Actualizado: `main.py` - Registro de rutas

---

## Endpoints Disponibles

### 1. Crear Preferencia de Pago (Checkout)

```
POST /api/payments/checkout
Content-Type: application/json

Request:
{
  "user_id": 1
}

Response (201 Created):
{
  "preference_id": "123456789",
  "init_point": "https://www.mercadopago.com.mx/checkout/v1/redirect?pref_id=123456789",
  "sandbox_init_point": "https://sandbox.mercadopago.com.mx/checkout/v1/redirect?pref_id=123456789"
}
```

**Flujo**:

1. Frontend obtiene user_id del usuario autenticado
2. Llamada a POST /api/payments/checkout
3. Backend crea preferencia en Mercado Pago
4. Backend guarda información en tabla `payments`
5. Frontend redirige a `init_point` (URL de checkout)

### 2. Consultar Estado de Pago

```
GET /api/payments/status/{preference_id}

Response:
{
  "preference_id": "123456789",
  "status": "pending|approved|rejected",
  "user_id": 1,
  "amount": 149.0,
  "currency": "MXN",
  "created_at": "2026-03-31T10:30:00"
}
```

### 3. Webhook de Notificaciones (Mercado Pago → Backend)

```
POST /api/webhooks/payments?id=12345&type=payment

Response:
{
  "status": "received",
  "result": {
    "status": "processed",
    "payment_id": "123456789",
    "payment_status": "approved",
    "user_id": 1
  }
}
```

---

## Variables de Entorno Necesarias

Agregar a `.env`:

```env
# Mercado Pago - Credenciales
MERCADOPAGO_PUBLIC_KEY=your_public_key_here
MERCADOPAGO_ACCESS_TOKEN=your_access_token_here
USER_ID_MERCADOPAGO=your_user_id
USUARIO_MERCADOPAGO=your_username (opcional para auth básica)
CONTRASENA_MERCADOPAGO=your_password (opcional para auth básica)
CODIGO_VERIFICACION_MERCADOPAGO=your_code (opcional)

# URL del servidor (IMPORTANTE para app móvil)
# Reemplaza con tu IP o dominio
SERVER_URL=http://192.168.0.100:8000
# O en producción:
# SERVER_URL=https://api.tudominio.com
```

**Cómo obtenerlas**:

1. Ir a https://www.mercadopago.com.mx/developers/panel
2. Crear/seleccionar aplicación
3. Copiar credenciales desde el panel del desarrollador
4. Credenciales de TEST y PROD son diferentes

---

## Configuración en Mercado Pago

### Crear Plan (Opcional para MVP)

Para MVP **solo se usan pagos únicos**, pero si deseas agregar suscripciones después:

1. Dashboard Mercado Pago
2. Configuración → Planes
3. Crear plan:
   - Nombre: "FitnessPro Premium"
   - Frecuencia: Mensual
   - Precio: 149 MXN

### Configurar Webhooks

1. Dashboard → Configuración → Webhooks
2. Agregar URL pública de tu backend: `https://tuapi.com/api/webhooks/payments`
3. Seleccionar eventos: "payment.created", "payment.updated"

---

## Flujo Completo de Usuario (App Móvil - Opción 3)

```
1. Usuario autenticado en app
   ↓
2. Click en "Pagar Premium - 149 MXN"
   ↓
3. Frontend: POST /api/payments/checkout
   {user_id: 123}
   ↓
4. Backend:
   - Verifica user existe
   - Crea preferencia en Mercado Pago
   - Guarda en tabla payments
   - Retorna init_point + preference_id
   ↓
5. Frontend abre Mercado Pago checkout (init_point)
   ↓
6. Usuario completa pago en Mercado Pago
   ↓
7. MP redirige a callback URL (app puede ignorar)
   ↓
8. IMPORTANTE: Frontend hace POLLING (cada 2 segundos):
   GET /api/payments/status/{preference_id}
   → status: pending → espera...
   → status: approved → ¡PREMIUM ACTIVADO!
   ↓
9. PARALELO: MP envía webhook a /api/webhooks/payments
   ↓
10. Backend:
    - Recibe notificación
    - Consulta estado en MP
    - Actualiza tabla payments
    - (TODO) Activa premium para user_id
```

**Ventajas de esta opción**:

- ✅ No necesita URLs públicas complicadas (IP + puerto funciona)
- ✅ Funciona igual en desarrollo, staging y producción
- ✅ Webhook es la fuente de verdad (no depende del redirect)
- ✅ APP es más predecible (sin sorpresas de navegación)

---

## Pasos Próximos (TODO)

### Fase 1: Activación de Premium

- [ ] Agregar campo `is_premium` a tabla `User`
- [ ] Actualizar `user_service.update_user` para activar premium cuando pago sea "approved"
- [ ] Endpoint GET /api/users/me/is-premium para frontend

### Fase 2: Suscripciones Recurrentes

- [ ] Cambiar a Mercado Pago Subscription API
- [ ] Agregar campos a `Payment`: `subscription_id`, `next_billing_date`, `cancel_at_period_end`
- [ ] Implementar endpoint de cancelación: DELETE /api/subscriptions/{subscription_id}
- [ ] Manejar reintentos automáticos de cobro (dunning)

### Fase 3: Administración

- [ ] Panel para ver historial de pagos
- [ ] Refunds/reembolsos
- [ ] Reportes de ingresos netos

---

## Seguridad y Buenas Prácticas

✅ **Implementado**:

- Validación de usuario existe
- Guardado de datos de pago en BD para auditoría
- Webhook sin confiar solo en redirect del frontend
- Logging de operaciones

⚠️ **Recomendaciones para Producción**:

- [ ] Validar firma de webhook (usar `X-Signature` header de MP)
- [ ] Rate limiting en endpoint de webhooks
- [ ] Encriptar datos sensibles en BD
- [ ] Usar URLs de retorno reales en producción (actualizar en payment_routes.py)
- [ ] Webhook debe estar en HTTPS

---

## Pruebas

### Test Manual en Sandbox (Con IP Local)

**Paso 1: Obtener tu IP local**

```bash
# Windows
ipconfig  # Buscar IPv4 Address (ej: 192.168.x.x)

# Mac/Linux
ifconfig  # Buscar inet (ej: 192.168.x.x)
```

**Paso 2: Configurar SERVER_URL en .env**

```env
SERVER_URL=http://192.168.x.x:8000
# Reemplaza 192.168.x.x con tu IP real
```

**Paso 3: Iniciar servidor**

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Paso 4: Test en Postman/Insomnia**

```
POST http://192.168.x.x:8000/api/payments/checkout
Content-Type: application/json

{
  "user_id": 1
}
```

**Paso 5: Abre el init_point en navegador**

- Usa la URL sandbox o production según tus credenciales
- Mercado Pago te dará tarjetas de prueba

**Paso 6: Consulta estado después de pagar**

```
GET http://192.168.x.x:8000/api/payments/status/{preference_id}
```

**Paso 7: Simula webhook (entorno local)**

```bash
curl -X POST "http://192.168.x.x:8000/api/webhooks/payments?id=12345&type=payment"
```

### En Producción

- Reemplaza `SERVER_URL` con tu dominio: `https://api.tudominio.com`
- Asegúrate de que:
  1. Tu API está en HTTPS
  2. El puerto está abierto en firewall
  3. Configuraste el webhook en dashboard de MP

### Test Webhook

```bash
curl -X POST "http://localhost:8000/api/webhooks/payments?id=123456&type=payment"
```

---

## Notas de Implementación

- **Monto hardcodeado**: `149 MXN` en `PaymentService.AMOUNT`
- **URLs de retorno**: Simples para MVP, actualizar en producción
- **Base de datos**: Nueva tabla `payments` se crea automáticamente al iniciar
- **Inyección de dependencias**: Sigue patrón existente del proyecto

---

## Referencias

- [Mercado Pago Docs - Checkout Pro](https://www.mercadopago.com.mx/developers/es/docs/checkout-pro/landing)
- [Mercado Pago Docs - Webhooks](https://www.mercadopago.com.mx/developers/es/docs/subscriptions/additional-content/your-integrations/notifications/webhooks)
- Credenciales test disponibles en dashboard de Mercado Pago
