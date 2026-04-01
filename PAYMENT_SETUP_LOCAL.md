# Configura Pagos con Mercado Pago (App Móvil + IP Local)

## TL;DR - Rápido

1. **Obtén tu IP local**:

   ```powershell
   ipconfig  # Busca IPv4 Address (ej: 192.168.0.100)
   ```

2. **Agrega a `.env`**:

   ```env
   SERVER_URL=http://192.168.0.100:8000
   MERCADOPAGO_PUBLIC_KEY=PKtest_xxxxx
   MERCADOPAGO_ACCESS_TOKEN=TEST-xxxxx
   USER_ID_MERCADOPAGO=123456
   ```

3. **Inicia servidor en modo público**:

   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

4. **Crea pago desde otra máquina/app**:

   ```bash
   curl -X POST "http://192.168.0.100:8000/api/payments/checkout" \
     -H "Content-Type: application/json" \
     -d '{"user_id": 1}'
   ```

5. **Abre el checkout URL retornado en navegador** y paga

6. **Consulta estado**:
   ```bash
   curl "http://192.168.0.100:8000/api/payments/status/{preference_id}"
   ```

---

## Explicación del Flujo (Opción 3 para Apps Móviles)

Usamos **webhook + polling** porque:

- ✅ No necesitas URL pública compleja
- ✅ La app móvil controla el timeline
- ✅ El webhook es la fuente de verdad (no un redirect)

```
┌─────────────────┐
│  App Móvil      │
└────────┬────────┘
         │ 1. POST /api/payments/checkout
         ↓
┌─────────────────────────────────────┐
│  Backend FastAPI (tu_ip:8000)       │
├─────────────────────────────────────┤
│ - Crea preferencia en Mercado Pago  │
│ - Retorna init_point (URL checkout) │
│ - Guarda pago en BD                 │
└────────┬─────────────────────────────┘
         │
         │ 2. Abre checkout URL
         ↓
    ┌─────────────────┐
    │ Mercado Pago    │ (usuario paga aquí)
    │ Checkout        │
    └────────┬────────┘
             │
    ┌────────┴──────────┬─────────────────────┐
    │                   │                     │
    │ 3. Redirige a     │ 4. Webhook          │
    │    callback       │    (backend)        │
    ↓                   ↓                     ↓
┌────────┐     ┌──────────────────────────┐
│ App    │     │ Backend: actualiza BD    │
│ ignora │     │ - status = "approved"    │
└────────┘     └──────────────────────────┘

   5. App hace polling cada 2 seg
      GET /api/payments/status/{id}
      → status: approved → ¡Premium activado!
```

---

## Configuración Paso a Paso

### 1. Obtener IP Local (Windows)

```powershell
PS C:\> ipconfig

Configuración IP de Windows
...
Ethernet adapter Ethernet:
   Dirección IPv4 . . . . . . . . . . : 192.168.0.100
   Máscara de subred  . . . . . . . . : 255.255.255.0
```

**Usa 192.168.0.100** (tu IP será diferente)

### 2. Agregar a .env

```bash
# .env
SERVER_URL=http://192.168.0.100:8000

# Mercado Pago (obtén de https://www.mercadopago.com.mx/developers/panel)
MERCADOPAGO_PUBLIC_KEY=PKtest_xxxxxxxxxxxxxxxxxxxxxxxx
MERCADOPAGO_ACCESS_TOKEN=TEST-xxxxxxxxxxxxxxxxxxxxxxxxxxxx
USER_ID_MERCADOPAGO=123456789
```

### 3. Iniciar Servidor en 0.0.0.0 (escucha en todas las interfaces)

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Salida esperada**:

```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

### 4. Accede desde Otra Máquina/Dispositivo

Desde otra computadora o la app móvil:

```
http://192.168.0.100:8000/docs
→ Ves Swagger UI con los endpoints documentados
```

---

## Endpoints Principales

### Crear Preferencia de Pago

```bash
POST http://192.168.0.100:8000/api/payments/checkout
Content-Type: application/json

{
  "user_id": 1
}
```

**Response**:

```json
{
  "preference_id": "123456789",
  "init_point": "https://www.mercadopago.com.mx/checkout/v1/redirect?pref_id=123456789",
  "sandbox_init_point": "https://sandbox.mercadopago.com.mx/checkout/v1/redirect?pref_id=123456789"
}
```

### Consultar Estado

```bash
GET http://192.168.0.100:8000/api/payments/status/123456789
```

**Response**:

```json
{
  "preference_id": "123456789",
  "status": "pending|approved|rejected",
  "user_id": 1,
  "amount": 149.0,
  "currency": "MXN",
  "created_at": "2026-03-31T10:30:00"
}
```

### Webhook (Mercado Pago → Backend)

```bash
POST http://192.168.0.100:8000/api/webhooks/payments?id=12345&type=payment
```

---

## Prueba Completa

### 1. Crear Pago

```bash
curl -X POST http://192.168.0.100:8000/api/payments/checkout \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1}'
```

Guarda el `preference_id` (ej: `123456789`)

### 2. Verifica Estado (antes de pagar)

```bash
curl http://192.168.0.100:8000/api/payments/status/123456789
# → status: pending
```

### 3. Abre el Checkout

- Copia `sandbox_init_point` en navegador
- Usa tarjeta de prueba (MP te da opciones)
- Completa el pago

### 4. Verifica Estado (después de pagar)

```bash
curl http://192.168.0.100:8000/api/payments/status/123456789
# → status: approved
```

### 5. Simula Webhook

```bash
curl -X POST http://192.168.0.100:8000/api/webhooks/payments?id=123456789&type=payment
# Verifica logs del backend para confirmar que se procesó
```

---

## Para App Móvil (Pseudocódigo)

```dart
// Flutter / React Native / etc

Map<String, dynamic> response = await http.post(
  Uri.parse('http://192.168.0.100:8000/api/payments/checkout'),
  headers: {'Content-Type': 'application/json'},
  body: jsonEncode({'user_id': userId}),
);

String initPoint = response['init_point'];
String preferenceId = response['preference_id'];

// Abre URL de checkout
launchUrl(Uri.parse(initPoint));

// Mientras usuario paga, hace polling cada 2 segundos
Timer.periodic(Duration(seconds: 2), (timer) async {
  final statusResponse = await http.get(
    Uri.parse('http://192.168.0.100:8000/api/payments/status/$preferenceId'),
  );

  if (statusResponse.body['status'] == 'approved') {
    timer.cancel();
    // ¡Activa Premium!
    showSnackBar('¡Pago confirmado! Ahora tienes acceso premium');
  }
});
```

---

## Troubleshooting

### Error: "Connection refused"

- ✅ Verifica que el servidor está corriendo: `uvicorn main:app --host 0.0.0.0 --port 8000`
- ✅ Verifica que usaste la IP correcta (no localhost)
- ✅ Verifica firewall no bloquea puerto 8000

### Error: "Cannot connect from app"

- ✅ Usa IP local real, no 127.0.0.1 ni localhost
- ✅ Ambas máquinas en la **misma red WiFi**
- ✅ Prueba ping: `ping 192.168.0.100`

### Error: "Mercado Pago invalid credentials"

- ✅ Copia credenciales exactas del dashboard MP
- ✅ Usa tokens TEST, no PROD (para sandbox)
- ✅ Reload servidor y limpia env después de cambiar

### Webhook no se procesa

- ✅ Verifica que SERVER_URL en .env es correcto
- ✅ Revisa logs del backend
- ✅ Asegúrate que Mercado Pago puede alcanzar tu IP (configura webhook en dashboard MP)

---

## Siguiente Paso: Producción

Cuando lleves a producción:

1. Cambia `SERVER_URL` en .env a tu dominio/IP pública:

   ```env
   SERVER_URL=https://api.tudominio.com
   ```

2. Usa certificado SSL/TLS (HTTPS)

3. Configura webhook en dashboard de Mercado Pago:
   - Dirección: `https://api.tudominio.com/api/webhooks/payments`
   - Eventos: `payment.created`, `payment.updated`

4. Usa tokens PROD de Mercado Pago (no TEST)

---

## Ver También

- `PAYMENT_IMPLEMENTATION.md` - Documentación técnica completa
- `.env.payments.example` - Plantilla de variables de entorno
