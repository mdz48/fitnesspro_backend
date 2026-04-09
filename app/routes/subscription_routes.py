"""
Rutas para suscripciones con Mercado Pago
"""
import os
import logging
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, status, Request, Query
from fastapi.responses import JSONResponse
from app.schemas.subscription_schema import (
    SubscriptionPlanCreateRequest,
    SubscriptionPlanUpdateRequest,
    SubscriptionPlanResponse,
    SubscriptionPlanListResponse,
    SubscriptionCreateRequest,
    SubscriptionCreateWithoutPlanRequest,
    SubscriptionResponse,
    SubscriptionCheckoutResponse,
    SubscriptionStatusResponse,
    SubscriptionPauseRequest,
    SubscriptionCancelRequest,
    SubscriptionUpdateAmountRequest,
    SubscriptionUpdateCardRequest,
    UserSubscriptionListResponse,
    SubscriptionPaymentListResponse,
    SubscriptionPaymentResponse
)
from app.core.dependencies import (
    SubscriptionPlanServiceDep,
    SubscriptionServiceDep
)

load_dotenv()

logger = logging.getLogger(__name__)

subscription_router = APIRouter()


def _resolve_mp_mode(value: str | None) -> str:
    """Determina si una credencial de MP es test o production sin exponer su valor."""
    if not value:
        return "missing"
    if value.startswith("TEST-"):
        return "test"
    if value.startswith("APP_USR-"):
        return "production"
    return "unknown"


@subscription_router.get(
    "/subscriptions/debug/mp-mode",
    status_code=status.HTTP_200_OK
)
def get_mp_runtime_mode(
    service: SubscriptionServiceDep
):
    """
    Devuelve el modo de credenciales de Mercado Pago en runtime.

    No expone tokens; solo reporta si backend corre en test/production.
    """
    access_token_mode = _resolve_mp_mode(service.mp_config.access_token)
    public_key_mode = _resolve_mp_mode(service.mp_config.public_key)

    return {
        "access_token_mode": access_token_mode,
        "public_key_mode": public_key_mode,
        "modes_match": access_token_mode == public_key_mode,
        "runtime_env": "backend_process"
    }


# ===== Rutas de Planes de Suscripción =====

@subscription_router.post(
    "/subscriptions/plans",
    response_model=SubscriptionPlanResponse,
    status_code=status.HTTP_201_CREATED
)
def create_subscription_plan(
    request: SubscriptionPlanCreateRequest,
    service: SubscriptionPlanServiceDep
):
    """
    Crea un nuevo plan de suscripción en Mercado Pago.
    
    Args:
        request: Datos del plan
        service: Servicio de planes (inyectado)
        
    Returns:
        Datos del plan creado
        
    Raises:
        HTTPException: Si hay error en la creación
    """
    free_trial_freq = None
    free_trial_type = None
    if request.free_trial:
        free_trial_freq = request.free_trial.frequency
        free_trial_type = request.free_trial.frequency_type.value

    SERVER_URL = os.getenv("SERVER_URL")
    back_url = request.back_url or (f"{SERVER_URL}/api/subscriptions/callback" if SERVER_URL else None)
    notification_url = f"{SERVER_URL}/api/webhooks/subscriptions" if SERVER_URL else None
    
    result = service.create_plan(
        name=request.name,
        reason=request.reason,
        transaction_amount=request.transaction_amount,
        currency_id=request.currency_id,
        frequency=request.frequency,
        frequency_type=request.frequency_type.value,
        description=request.description,
        repetitions=request.repetitions,
        billing_day=request.billing_day,
        billing_day_proportional=request.billing_day_proportional,
        free_trial_frequency=free_trial_freq,
        free_trial_frequency_type=free_trial_type,
        back_url=back_url,
        notification_url=notification_url
    )
    
    return service.get_plan(result["id"])


@subscription_router.get(
    "/subscriptions/plans",
    response_model=SubscriptionPlanListResponse
)
def list_subscription_plans(
    service: SubscriptionPlanServiceDep,
    active_only: bool = True
):
    """
    Lista los planes de suscripción disponibles.
    
    Args:
        active_only: Si True, solo devuelve planes activos
        service: Servicio de planes (inyectado)
        
    Returns:
        Lista de planes
    """
    if active_only:
        plans = service.list_active_plans()
    else:
        plans = service.list_all_plans()
    
    return SubscriptionPlanListResponse(
        plans=plans,
        total=len(plans)
    )


@subscription_router.get(
    "/subscriptions/plans/{plan_id}",
    response_model=SubscriptionPlanResponse
)
def get_subscription_plan(
    plan_id: int,
    service: SubscriptionPlanServiceDep
):
    """
    Obtiene un plan de suscripción por ID.
    
    Args:
        plan_id: ID del plan
        service: Servicio de planes (inyectado)
        
    Returns:
        Datos del plan
        
    Raises:
        HTTPException: Si el plan no existe
    """
    return service.get_plan(plan_id)


@subscription_router.put(
    "/subscriptions/plans/{plan_id}",
    response_model=SubscriptionPlanResponse
)
def update_subscription_plan(
    plan_id: int,
    request: SubscriptionPlanUpdateRequest,
    service: SubscriptionPlanServiceDep
):
    """
    Actualiza un plan de suscripción.
    
    Args:
        plan_id: ID del plan
        request: Datos a actualizar
        service: Servicio de planes (inyectado)
        
    Returns:
        Plan actualizado
    """
    return service.update_plan(
        plan_id=plan_id,
        name=request.name,
        description=request.description,
        reason=request.reason,
        transaction_amount=request.transaction_amount,
        status=request.status.value if request.status else None,
        back_url=request.back_url
    )


@subscription_router.delete(
    "/subscriptions/plans/{plan_id}",
    response_model=SubscriptionPlanResponse
)
def cancel_subscription_plan(
    plan_id: int,
    service: SubscriptionPlanServiceDep
):
    """
    Cancela un plan de suscripción.
    
    IMPORTANTE: Los suscriptores existentes seguirán activos.
    
    Args:
        plan_id: ID del plan
        service: Servicio de planes (inyectado)
        
    Returns:
        Plan cancelado
    """
    return service.cancel_plan(plan_id)


# ===== Rutas de Suscripciones de Usuarios =====

@subscription_router.post(
    "/subscriptions",
    response_model=SubscriptionCheckoutResponse,
    status_code=status.HTTP_201_CREATED
)
def create_subscription(
    request: SubscriptionCreateRequest,
    service: SubscriptionServiceDep
):
    """
    Crea una suscripción para un usuario basada en un plan.
    
    Args:
        request: Datos de la suscripción (user_id, plan_id, card_token_id)
        service: Servicio de suscripciones (inyectado)
        
    Returns:
        Datos de la suscripción e init_point para checkout
        
    Raises:
        HTTPException: Si hay error en la creación
    """
    SERVER_URL = os.getenv("SERVER_URL")
    back_url = f"{SERVER_URL}/api/subscriptions/callback" if SERVER_URL else None
    notification_url = f"{SERVER_URL}/api/webhooks/subscriptions" if SERVER_URL else None

    logger.info(
        "POST /subscriptions received: user_id=%s plan_id=%s has_card_token=%s has_back_url=%s has_notification_url=%s",
        request.user_id,
        request.plan_id,
        bool(request.card_token_id),
        bool(back_url),
        bool(notification_url),
    )
    
    try:
        result = service.create_subscription(
            user_id=request.user_id,
            plan_id=request.plan_id,
            card_token_id=request.card_token_id,
            back_url=back_url,
            notification_url=notification_url
        )
        logger.info(
            "POST /subscriptions succeeded: user_id=%s plan_id=%s subscription_id=%s mp_preapproval_id=%s status=%s",
            request.user_id,
            request.plan_id,
            result.get("subscription_id"),
            result.get("mp_preapproval_id"),
            result.get("status"),
        )
    except HTTPException as exc:
        logger.warning(
            "POST /subscriptions failed: user_id=%s plan_id=%s status=%s detail=%s",
            request.user_id,
            request.plan_id,
            exc.status_code,
            exc.detail,
        )
        raise
    except Exception:
        logger.exception(
            "Unexpected error in POST /subscriptions: user_id=%s plan_id=%s",
            request.user_id,
            request.plan_id,
        )
        raise
    
    return SubscriptionCheckoutResponse(
        subscription_id=result["subscription_id"],
        mp_preapproval_id=result.get("mp_preapproval_id"),
        init_point=result.get("init_point") or "",
        sandbox_init_point=result.get("sandbox_init_point"),
        status=result["status"]
    )


@subscription_router.post(
    "/subscriptions/no-plan",
    response_model=SubscriptionCheckoutResponse,
    status_code=status.HTTP_201_CREATED
)
def create_subscription_without_plan(
    request: SubscriptionCreateWithoutPlanRequest,
    service: SubscriptionServiceDep
):
    """
    Crea una suscripción sin plan preconfigurado en Mercado Pago.

    Útil para escenarios flexibles o planes experimentales.
    """
    SERVER_URL = os.getenv("SERVER_URL")
    back_url = request.back_url or (f"{SERVER_URL}/api/subscriptions/callback" if SERVER_URL else None)
    notification_url = f"{SERVER_URL}/api/webhooks/subscriptions" if SERVER_URL else None

    logger.info(
        "POST /subscriptions/no-plan received: user_id=%s reason=%s amount=%s currency=%s frequency=%s frequency_type=%s has_card_token=%s has_back_url=%s has_notification_url=%s",
        request.user_id,
        request.reason,
        request.transaction_amount,
        request.currency_id,
        request.frequency,
        request.frequency_type.value,
        bool(request.card_token_id),
        bool(back_url),
        bool(notification_url),
    )

    try:
        result = service.create_subscription_without_plan(
            user_id=request.user_id,
            reason=request.reason,
            transaction_amount=request.transaction_amount,
            currency_id=request.currency_id,
            frequency=request.frequency,
            frequency_type=request.frequency_type.value,
            start_date=request.start_date,
            end_date=request.end_date,
            card_token_id=request.card_token_id,
            back_url=back_url,
            notification_url=notification_url
        )
        logger.info(
            "POST /subscriptions/no-plan succeeded: user_id=%s subscription_id=%s mp_preapproval_id=%s status=%s",
            request.user_id,
            result.get("subscription_id"),
            result.get("mp_preapproval_id"),
            result.get("status"),
        )
    except HTTPException as exc:
        logger.warning(
            "POST /subscriptions/no-plan failed: user_id=%s status=%s detail=%s",
            request.user_id,
            exc.status_code,
            exc.detail,
        )
        raise
    except Exception:
        logger.exception(
            "Unexpected error in POST /subscriptions/no-plan: user_id=%s",
            request.user_id,
        )
        raise

    return SubscriptionCheckoutResponse(
        subscription_id=result["subscription_id"],
        mp_preapproval_id=result.get("mp_preapproval_id"),
        init_point=result.get("init_point") or "",
        sandbox_init_point=result.get("sandbox_init_point"),
        status=result["status"]
    )


@subscription_router.get(
    "/subscriptions/user/{user_id}",
    response_model=UserSubscriptionListResponse
)
def get_user_subscriptions(
    user_id: int,
    service: SubscriptionServiceDep
):
    """
    Obtiene todas las suscripciones de un usuario.
    
    Args:
        user_id: ID del usuario
        service: Servicio de suscripciones (inyectado)
        
    Returns:
        Lista de suscripciones del usuario
    """
    subscriptions = service.get_user_subscriptions(user_id)
    return UserSubscriptionListResponse(
        subscriptions=subscriptions,
        total=len(subscriptions)
    )


@subscription_router.get(
    "/subscriptions/user/{user_id}/active",
    response_model=SubscriptionResponse
)
def get_active_subscription(
    user_id: int,
    service: SubscriptionServiceDep
):
    """
    Obtiene la suscripción activa de un usuario.
    
    Args:
        user_id: ID del usuario
        service: Servicio de suscripciones (inyectado)
        
    Returns:
        Suscripción activa o 404
        
    Raises:
        HTTPException: Si el usuario no tiene suscripción activa
    """
    subscription = service.get_active_subscription(user_id)
    if not subscription:
        raise HTTPException(
            status_code=404,
            detail={"code": "NO_ACTIVE_SUBSCRIPTION", "message": "El usuario no tiene suscripción activa"}
        )
    return subscription


# ===== Endpoint de Callback (Fallback) =====

@subscription_router.get(
    "/subscriptions/callback",
    status_code=status.HTTP_200_OK
)
def subscription_callback(
    request: Request,
    preapproval_id: str | None = None,
    status_param: str | None = Query(default=None, alias="status")
):
    """
    Endpoint de callback para redirecciones de Mercado Pago (fallback).

    La app móvil debe usar polling a GET /api/subscriptions/{id}/status
    y procesar webhooks en backend.

    Args:
        request: Request de FastAPI
        preapproval_id: ID de la suscripción
        status_param: Estado (authorized, paused, etc.) recibido como query param `status`

    Returns:
        Respuesta confirmando la redirección
    """
    logger.info(
        "Subscription callback received: preapproval_id=%s status=%s query=%s",
        preapproval_id,
        status_param,
        str(request.query_params),
    )

    return {
        "message": "Subscription callback received",
        "preapproval_id": preapproval_id,
        "status": status_param,
        "note": "Para app móvil, consulta el estado con GET /api/subscriptions/{id}/status"
    }


@subscription_router.get(
    "/subscriptions/{subscription_id}",
    response_model=SubscriptionResponse
)
def get_subscription(
    subscription_id: int,
    service: SubscriptionServiceDep
):
    """
    Obtiene una suscripción por ID.
    
    Args:
        subscription_id: ID de la suscripción
        service: Servicio de suscripciones (inyectado)
        
    Returns:
        Datos de la suscripción
        
    Raises:
        HTTPException: Si la suscripción no existe
    """
    return service.get_subscription(subscription_id)


@subscription_router.get(
    "/subscriptions/{subscription_id}/status",
    response_model=SubscriptionStatusResponse
)
def get_subscription_status(
    subscription_id: int,
    service: SubscriptionServiceDep
):
    """
    Obtiene el estado detallado de una suscripción.
    
    Sincroniza con Mercado Pago antes de devolver el estado.
    
    Args:
        subscription_id: ID de la suscripción
        service: Servicio de suscripciones (inyectado)
        
    Returns:
        Estado detallado de la suscripción
    """
    return service.get_subscription_status(subscription_id)


@subscription_router.put(
    "/subscriptions/{subscription_id}/pause",
    response_model=SubscriptionResponse
)
def pause_subscription(
    subscription_id: int,
    request: SubscriptionPauseRequest,
    service: SubscriptionServiceDep
):
    """
    Pausa una suscripción temporalmente.
    
    Args:
        subscription_id: ID de la suscripción
        request: Motivo de la pausa (opcional)
        service: Servicio de suscripciones (inyectado)
        
    Returns:
        Suscripción pausada
    """
    return service.pause_subscription(subscription_id, request.reason)


@subscription_router.put(
    "/subscriptions/{subscription_id}/reactivate",
    response_model=SubscriptionResponse
)
def reactivate_subscription(
    subscription_id: int,
    service: SubscriptionServiceDep
):
    """
    Reactiva una suscripción pausada.
    
    Args:
        subscription_id: ID de la suscripción
        service: Servicio de suscripciones (inyectado)
        
    Returns:
        Suscripción reactivada
    """
    return service.reactivate_subscription(subscription_id)


@subscription_router.put(
    "/subscriptions/{subscription_id}/cancel",
    response_model=SubscriptionResponse
)
def cancel_subscription(
    subscription_id: int,
    request: SubscriptionCancelRequest,
    service: SubscriptionServiceDep
):
    """
    Cancela una suscripción definitivamente.
    
    Args:
        subscription_id: ID de la suscripción
        request: Motivo de la cancelación (opcional)
        service: Servicio de suscripciones (inyectado)
        
    Returns:
        Suscripción cancelada
    """
    return service.cancel_subscription(subscription_id, request.reason)


@subscription_router.put(
    "/subscriptions/{subscription_id}/amount",
    response_model=SubscriptionResponse
)
def update_subscription_amount(
    subscription_id: int,
    request: SubscriptionUpdateAmountRequest,
    service: SubscriptionServiceDep
):
    """
    Modifica el monto de una suscripción.
    
    Args:
        subscription_id: ID de la suscripción
        request: Nuevo monto y moneda
        service: Servicio de suscripciones (inyectado)
        
    Returns:
        Suscripción actualizada
    """
    return service.update_subscription_amount(
        subscription_id,
        request.transaction_amount,
        request.currency_id
    )


@subscription_router.put(
    "/subscriptions/{subscription_id}/card",
    response_model=SubscriptionResponse
)
def update_subscription_card(
    subscription_id: int,
    request: SubscriptionUpdateCardRequest,
    service: SubscriptionServiceDep
):
    """
    Actualiza la tarjeta de una suscripción.
    
    Args:
        subscription_id: ID de la suscripción
        request: Nuevo token de tarjeta
        service: Servicio de suscripciones (inyectado)
        
    Returns:
        Suscripción actualizada
    """
    return service.update_subscription_card(subscription_id, request.card_token_id)


@subscription_router.get(
    "/subscriptions/{subscription_id}/payments",
    response_model=SubscriptionPaymentListResponse
)
def get_subscription_payments(
    subscription_id: int,
    service: SubscriptionServiceDep
):
    """
    Obtiene el historial de pagos de una suscripción.
    
    Args:
        subscription_id: ID de la suscripción
        service: Servicio de suscripciones (inyectado)
        
    Returns:
        Lista de pagos de la suscripción
    """
    payments = service.get_subscription_payments(subscription_id)
    return SubscriptionPaymentListResponse(
        payments=payments,
        total=len(payments)
    )


# ===== Webhook para Notificaciones de Suscripciones =====

@subscription_router.post(
    "/webhooks/subscriptions",
    status_code=status.HTTP_200_OK
)
def receive_subscription_webhook(
    request: Request,
    body: dict
):
    """
    Recibe notificaciones de webhook de suscripciones de Mercado Pago.
    
    Tipos soportados:
    - subscription_preapproval: Cambios en la suscripción
    - subscription_authorized_payment: Pagos recurrentes
    
    Args:
        request: Request de FastAPI
        body: Payload JSON del webhook
        
    Returns:
        Confirmación de recepción con status 200
    """
    from app.core.dependencies import get_subscription_service_sync
    
    notification_id = body.get("id")
    notification_type = body.get("type")
    
    # MP puede enviar datos por query params también
    query_notification_type = request.query_params.get("type")
    query_data_id = request.query_params.get("data.id")
    
    if not notification_type and query_notification_type:
        notification_type = query_notification_type
    
    if body.get("data") is None and query_data_id:
        body["data"] = {"id": query_data_id}
    elif isinstance(body.get("data"), dict) and not body["data"].get("id") and query_data_id:
        body["data"]["id"] = query_data_id

    resource_id = body.get("data", {}).get("id") if isinstance(body.get("data"), dict) else None
    
    logger.info(f"Subscription webhook received: type={notification_type}, id={notification_id}, body={body}")
    
    if not notification_id or not notification_type:
        logger.warning(f"Webhook missing required fields: id={notification_id}, type={notification_type}")
        return {"status": "ignored", "reason": "missing_fields"}
    
    # Usar versión sincrónica del servicio
    service = get_subscription_service_sync()

    signature_header = request.headers.get("x-signature")
    request_id_header = request.headers.get("x-request-id")
    if not service.verify_webhook_signature(signature_header, resource_id, request_id_header):
        logger.warning("Invalid subscription webhook signature")
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "status": "ignored",
                "reason": "invalid_signature"
            }
        )
    
    try:
        result = service.process_webhook_notification(body)
        logger.info(f"Subscription webhook processed: {result}")
        return {
            "status": "received",
            "result": result
        }
    except HTTPException as exc:
        logger.error(f"Error processing subscription webhook: {exc.detail}")
        return {
            "status": "received",
            "result": {
                "status": "ignored",
                "reason": "processing_error",
                "detail": str(exc.detail)
            }
        }
    except Exception as exc:
        logger.exception(f"Unexpected error processing subscription webhook: {str(exc)}")
        return {
            "status": "received",
            "result": {
                "status": "ignored",
                "reason": "unexpected_error"
            }
        }


