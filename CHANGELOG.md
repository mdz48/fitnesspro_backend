# Changelog

## [Unreleased]

### Cambios

- Se agregaron logs detallados y sanitizados al flujo de creación de suscripciones para depurar respuestas `400 Bad Request` de Mercado Pago y validaciones locales.
- Las rutas `POST /api/subscriptions` y `POST /api/subscriptions/no-plan` ahora registran el request entrante, la respuesta del servicio y el detalle de cualquier `HTTPException`.
- Se agregó persistencia de tokens FCM por usuario y el endpoint `POST /api/users/{user_id}/fcm-token` para registrar dispositivos.
- El backend ahora envía notificaciones FCM de tipo `PAYMENT_SUCCESS` cuando Mercado Pago confirma un pago recurrente aprobado.
- La carga de credenciales Firebase ahora soporta autodetección local de `firebasecredencials.json` (además de variables de entorno) para facilitar desarrollo.

## [1.5.3] - 2026-04-08

### Cambios

- Se actualizó la integración de ExerciseDB para usar el host oficial `exercisedb.p.rapidapi.com` por defecto.
- El backend ahora normaliza y pagina localmente la respuesta remota de ejercicios para mantener intacto el contrato del frontend.
- Se conservaron los mismos esquemas de salida para lista, detalle, búsqueda y filtros de ejercicios.

### Notas

- La respuesta pública de ejercicios no cambia; solo se reemplazó la adaptación interna al proveedor externo.
- `EXERCISEDB_BASE_URL` y `RAPIDAPI_HOST` siguen siendo configurables por entorno.

## [1.5.2] - 2026-04-03

### Cambios

- Se reforzó la compatibilidad del consumo remoto de ejercicios para tolerar respuestas legacy y variaciones de formato.
- Se normalizó la respuesta remota para mantener el contrato público actual del backend en ejercicios.
- Se agregó búsqueda remota con fallback local para no romper el frontend cuando el proveedor no expone un path específico.

### Notas

- La configuración de ExerciseDB sigue usando `EXERCISEDB_BASE_URL`, `RAPIDAPI_HOST` y `RAPIDAPI_KEY`.
- Si el proveedor remoto cambia su contrato, el backend conserva el contrato público mientras mantiene el servicio funcionando.

## [1.5.1] - 2026-04-02

### Cambios

- Se agregó `notification_url` en la creación de planes y suscripciones para enrutar eventos recurrentes a `POST /api/webhooks/subscriptions`.
- Se implementó validación opcional de firma HMAC en webhook de suscripciones (`x-signature` + `x-request-id`) controlada por `MERCADOPAGO_VALIDATE_WEBHOOK_SIGNATURE`.
- Se añadió endpoint `POST /api/subscriptions/no-plan` para crear suscripciones flexibles sin `preapproval_plan`.
- Se corrigió el callback de suscripciones para responder con `200 OK` en lugar de declarar `302` sin redirección real.

### Notas

- Si `SERVER_URL` está configurado, el backend usa automáticamente esa base para `notification_url` y callback.
- Cuando la validación de firma está activa y la firma es inválida, el webhook responde `401`.

## [1.5.0] - 2026-04-02

### Cambios

- Se eliminó por completo el flujo legado de pago único con Mercado Pago.
- El arranque de la aplicación quedó concentrado en suscripciones y planes recurrentes.
- Se removieron los routers, servicio, repositorio, modelo y schemas del checkout único.

### Notas

- La monetización pasa a depender exclusivamente de suscripciones con Mercado Pago.
- La implementación en curso prioriza planes, suscripciones, pagos recurrentes y webhooks.

## [1.4.0] - 2026-03-31

### Añadido

- **Integración de Mercado Pago para pagos únicos (MVP para Premium)**:
  - Nuevo endpoint POST /api/payments/checkout para crear preferencias de pago
  - Nuevo endpoint GET /api/payments/status/{preference_id} para verificar estado de pago
  - Nuevo webhook en POST /api/webhooks/payments para procesar notificaciones de Mercado Pago
  - Nuevo modelo ORM `Payment` para registrar todas las transacciones y preferencias
  - Nuevo repositorio `PaymentRepository` con métodos CRUD para pagos
  - Nuevo servicio `PaymentService` con lógica de integración con Mercado Pago
- **Configuración de Mercado Pago**:
  - Clase `MercadoPagoConfig` para gestionar credenciales (public_key, access_token, user_id)
  - Inyección de dependencias integrada en `app/core/dependencies.py`

### Cambios

- Se actualizó `main.py` para registrar las rutas de pagos
- Se agregó nueva tabla `payments` a la base de datos para auditoría y seguimiento
- Se mejoró la estructura de dependencias añadiendo `PaymentServiceDep` y `PaymentRepositoryDep`

### Notas

- MVP implementa solo pagos únicos por MXN 149 (sin suscripciones recurrentes aún)
- Las suscripciones recurrentes se agregarán en fase 2

---

### Consideraciones de arquitectura

- **No hay autenticación en los endpoints de pago.** Cualquiera con un `user_id` válido puede
  crear un checkout. En fase 2 se agregarán tokens JWT para proteger estos endpoints.
- **El webhook llega al servidor EC2** (`fitnesspro.redirectme.net`). Si el servidor está caído
  cuando MP envía el webhook, MP reintentará automáticamente hasta 72 horas.
- **Un `preference_id` es de un solo uso.** Si el usuario abandona el pago, la app debe llamar
  de nuevo a `POST /payments/checkout` para generar uno nuevo.
- **La tabla `payments` en BD guarda el historial completo.** Si un usuario llama múltiples veces
  al checkout, habrá múltiples registros. El frontend debe guardar el `preference_id` más reciente.

---

## [1.3.6] - 2026-03-29

### Añadido

- Integración de nueva API externa de recetas (TheMealDB) con endpoints:
  - GET /api/recipes/remote/search?name=
  - GET /api/recipes/remote/{recipe_id}
  - GET /api/recipes/remote/random
  - GET /api/recipes/remote/random/list?count=

### Cambios

- Se agregó caché para búsquedas y detalle de recetas externas para reducir latencia y llamadas repetidas.
- Se traduce automáticamente al español la información principal de la receta externa (nombre, categoría, área, instrucciones, ingredientes, medidas y etiquetas).
- Se agregó endpoint para obtener múltiples recetas aleatorias en una sola llamada con caché de corta duración.

## [1.3.5] - 2026-03-28

### Añadido

- Se agrego un nuevo endpoint para obtener los ejercicios y recetas del usuario de ese dia

## [1.3.4] - 2026-03-27

### Añadido

- Se puso un endpoint para obtener los ejercicios de la comunidad

## [1.3.3] - 2026-03-23

### Cambios

- Se corrigió el filtrado para la API externa y los ENUMs estaban mal

## [1.3.2] - 2026-03-23

### Cambios

- Se corrigió el error con google auth, ahora se puede iniciar sesión con google sin registrarse por completo.

## [1.3.1] - 2026-03-22

### Cambios

- Se corrigieron cosas opciones
- La tabla de user ahora tiene un nuevo campo llamado membership que puede ser gratuito, premium o admin. por defecto es gratuito.
- Se corrigió el error de que no se podían actualizar los campos de los usuarios.

## [1.3.0] - 2026-03-11

### Añadido

- Nuevos endpoints para buscar ejercicios y recetas por nombre.

## [1.2.0] - 2026-03-10

### Añadido

- Nueva feature de los planes de recetas en la base de datos.

## [1.1.0] - 2026-03-09

### Añadido

- Nueva feature de los planes de workout en la base de datos.

## [1.0.4] - 2026-03-09

### Añadido

- Filtro para ejercicios locales por parte del cuerpo, musculo, equipo, dificultad y tipo.

## [1.0.3] - 2026-03-08

### Cambios

- No se estaba cacheando los ejercicios traducidos

## [1.0.2] - 2026-03-08

### Añadido

- Ahora se pueden subir archivos PNG, JPG y JPEG en las recetas. y mp4 en los ejercicios.
- Se le agrego dificultad a los ejercicios.

### Cambios

- Se corrigió el error de que no se pudieran actualizar los campos de las recetas.
- Se corrigió el error de que no se pudieran actualizar los campos de los ejercicios.

## [1.0.1] - 2026-03-08

### Añadido

- **Cálculo de edad automático**: Se eliminó el campo `age` del modelo y esquema de usuarios, y se implementó un cálculo automático basado en la fecha de nacimiento.

### Cambios

- Se eliminó el campo `age` del modelo `User`.
- Se eliminó el campo `age` del esquema `UserBase`.
- Se agregó un cálculo automático de edad en el método `create` del servicio de usuarios.

## [1.0.0] - 2026-03-08

### Añadido

- **Integración con AWS S3**: Implementación de subida de archivos para imágenes de recetas.
- **Soporte Multimedia en Recetas**: Se habilitó la recepción de archivos de imagen (jpg, jpeg, png) vía `multipart/form-data` en el endpoint de creación de recetas.
- **Configuración de S3**: Añadida lógica centralizada en `app/shared/config/s3_files.py` para gestionar la comunicación con AWS.
- **Esquema de Base de Datos**: Actualizado para incluir `image_url` en el modelo y esquema de Recetas.
- **Dependencias**: Se agregaron `boto3` y librerías relacionadas al archivo `requirements.txt`.

### Cambios

- Refactorización de la ruta `POST /recipes` para soportar `Form` y `File` de FastAPI en lugar de solo JSON Raw.
