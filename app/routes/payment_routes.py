"""
Rutas para pagos con Mercado Pago
"""
import os
import logging
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, status, Query, Request
from app.schemas.payment_schema import PaymentPreferenceRequest, PaymentPreferenceResponse, PaymentStatusResponse
from app.core.dependencies import PaymentServiceDep

load_dotenv()

# Obtener URL base del servidor desde variable de entorno
# En desarrollo: http://tu_ip:8000
# En produccion: https://tu_dominio.com
SERVER_URL = os.getenv("SERVER_URL", "http://localhost:8000")

logger = logging.getLogger(__name__)

payment_router = APIRouter()


@payment_router.post("/payments/checkout", response_model=PaymentPreferenceResponse, status_code=status.HTTP_201_CREATED)
def create_checkout_preference(
    request: PaymentPreferenceRequest,
    service: PaymentServiceDep
):
    """
    Crea una preferencia de pago en Mercado Pago para checkout
    
    Args:
        request: Datos del usuario que realiza el pago
        service: Servicio de pagos (inyectado)
        
    Returns:
        PaymentPreferenceResponse con datos de la preferencia
        
    Raises:
        HTTPException: Si hay error en la creación
    """
    # URLs de retorno (se configuran desde variable de entorno SERVER_URL)
    # Opción 3: La app usa webhook + polling, estas URLs son fallback
    success_url = f"{SERVER_URL}/api/payments/callback?preference_id={{preference_id}}&status=approved"
    pending_url = f"{SERVER_URL}/api/payments/callback?preference_id={{preference_id}}&status=pending"
    failure_url = f"{SERVER_URL}/api/payments/callback?preference_id={{preference_id}}&status=rejected"
    
    result = service.create_checkout_preference(
        user_id=request.user_id,
        success_url=success_url,
        pending_url=pending_url,
        failure_url=failure_url
    )
    
    return PaymentPreferenceResponse(
        preference_id=result["preference_id"],
        init_point=result["init_point"],
        sandbox_init_point=result["sandbox_init_point"]
    )


@payment_router.get("/payments/status/{preference_id}", response_model=PaymentStatusResponse)
def get_payment_status(
    preference_id: str,
    service: PaymentServiceDep
):
    """
    Obtiene el estado de un pago
    
    Args:
        preference_id: ID de preferencia de Mercado Pago
        service: Servicio de pagos (inyectado)
        
    Returns:
        PaymentStatusResponse con estado actual
        
    Raises:
        HTTPException: Si el pago no existe
    """
    result = service.get_payment_status(preference_id)
    
    return PaymentStatusResponse(
        preference_id=result["preference_id"],
        status=result["status"],
        user_id=result["user_id"],
        amount=result["amount"],
        currency=result["currency"],
        created_at=result["created_at"]
    )


@payment_router.post("/webhooks/payments", status_code=status.HTTP_200_OK)
def receive_payment_webhook(
    request: Request,
    body: dict
):
    """
    Recibe notificaciones de webhook de Mercado Pago
    
    Mercado Pago envía un POST con body JSON:
    {
      "id": "123456",
      "type": "payment",
      "action": "payment.updated",
      "data": {"id": "payment_id"},
      "user_id": 279172247,
      "live_mode": false
    }
    
    Args:
        body: Payload JSON del webhook de Mercado Pago
        
    Returns:
        Confirmación de recepción con status 200
        
    Raises:
        HTTPException: Si hay error al procesar la notificación
    """
    from app.core.dependencies import get_payment_service_sync
    
    notification_id = body.get("id")
    notification_type = body.get("type")

    # Mercado Pago puede enviar parte de los datos también por query params.
    query_notification_type = request.query_params.get("type")
    query_data_id = request.query_params.get("data.id")

    if not notification_type and query_notification_type:
        notification_type = query_notification_type

    if body.get("data") is None and query_data_id:
        body["data"] = {"id": query_data_id}
    elif isinstance(body.get("data"), dict) and not body["data"].get("id") and query_data_id:
        body["data"]["id"] = query_data_id
    
    logger.info(f"Webhook received: type={notification_type}, id={notification_id}, body={body}")
    
    # Validar campos requeridos
    if not notification_id or not notification_type:
        logger.warning(f"Webhook missing required fields: id={notification_id}, type={notification_type}")
        return {"status": "ignored", "reason": "missing_fields"}
    
    # Usar versión sincrónica de servicio
    service = get_payment_service_sync()
    
    try:
        result = service.process_webhook_notification(body)
        logger.info(f"Webhook processed successfully: {result}")
        return {
            "status": "received",
            "result": result
        }
    except HTTPException as exc:
        logger.error(f"Error processing webhook: {exc.detail}")
        # Confirmamos recepción para evitar reintentos por errores transitorios.
        return {
            "status": "received",
            "result": {
                "status": "ignored",
                "reason": "processing_error",
                "detail": str(exc.detail)
            }
        }
    except Exception as exc:
        logger.exception(f"Unexpected error processing webhook: {str(exc)}")
        return {
            "status": "received",
            "result": {
                "status": "ignored",
                "reason": "unexpected_error"
            }
        }


@payment_router.get("/payments/callback", status_code=status.HTTP_302_FOUND)
def payment_callback(
    preference_id: str = Query(...),
    status_param: str = Query("", alias="status")
):
    """
    Endpoint de callback para redirecciones de Mercado Pago (fallback para app móvil)
    
    La app móvil NO debería usar esta URL directamente.
    En su lugar, la app debe:
    1. Hacer polling a GET /api/payments/status/{preference_id}
    2. Procesar el webhook en backend (POST /api/webhooks/payments)
    
    Este endpoint es solo para navegadores de fallback.
    
    Args:
        preference_id: ID de la preferencia
        status_param: Estado del pago (approved, pending, rejected)
        
    Returns:
        Respuesta simple confirmando que se recibió la redirección
    """
    logger.info(f"Payment callback received: preference_id={preference_id}, status={status_param}")
    
    return {
        "message": "Payment callback received",
        "preference_id": preference_id,
        "status": status_param,
        "note": "Para app móvil, consulta el estado con GET /api/payments/status/{preference_id}"
    }
