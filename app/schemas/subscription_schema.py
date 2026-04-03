"""
Esquemas Pydantic para suscripciones de Mercado Pago
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime
from enum import Enum


# === Enums ===

class FrequencyType(str, Enum):
    """Tipo de frecuencia de cobro"""
    DAYS = "days"
    MONTHS = "months"


class SubscriptionStatus(str, Enum):
    """Estados posibles de una suscripción"""
    PENDING = "pending"
    AUTHORIZED = "authorized"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class PaymentStatus(str, Enum):
    """Estados posibles de un pago de suscripción"""
    PROCESSED = "processed"
    RECYCLING = "recycling"
    WAITING_FOR_GATEWAY = "waiting_for_gateway"
    REJECTED = "rejected"
    REFUNDED = "refunded"


class PlanStatus(str, Enum):
    """Estados posibles de un plan"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    CANCELLED = "cancelled"


# === Schemas de Plan de Suscripción ===

class FreeTrial(BaseModel):
    """Configuración de período de prueba gratis"""
    frequency: int = Field(..., ge=1, description="Duración del trial")
    frequency_type: FrequencyType = Field(..., description="Tipo: days o months")


class SubscriptionPlanCreateRequest(BaseModel):
    """Request para crear un plan de suscripción"""
    name: str = Field(..., min_length=1, max_length=100, description="Nombre interno del plan")
    description: Optional[str] = Field(None, description="Descripción del plan")
    reason: str = Field(..., min_length=1, max_length=255, description="Título visible para el usuario")
    
    frequency: int = Field(1, ge=1, description="Cada cuánto se cobra")
    frequency_type: FrequencyType = Field(FrequencyType.MONTHS, description="Tipo de frecuencia")
    transaction_amount: float = Field(149.0, gt=0, description="Monto del cobro")
    currency_id: str = Field("MXN", max_length=10, description="Moneda")
    
    repetitions: Optional[int] = Field(None, ge=1, description="Número de cobros (None=ilimitado)")
    billing_day: Optional[int] = Field(None, ge=1, le=28, description="Día del mes para cobro")
    billing_day_proportional: bool = Field(True, description="Cobrar proporcional al suscribirse")
    
    free_trial: Optional[FreeTrial] = Field(None, description="Período de prueba gratis")
    back_url: Optional[str] = Field(None, description="URL de retorno")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Plan Premium Mensual",
                "description": "Acceso completo a FitnessPro por un mes",
                "reason": "FitnessPro Premium - Mensual",
                "frequency": 1,
                "frequency_type": "months",
                "transaction_amount": 149.0,
                "currency_id": "MXN",
                "billing_day": 1,
                "billing_day_proportional": True,
                "free_trial": {
                    "frequency": 7,
                    "frequency_type": "days"
                }
            }
        }


class SubscriptionPlanUpdateRequest(BaseModel):
    """Request para actualizar un plan de suscripción"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    reason: Optional[str] = Field(None, min_length=1, max_length=255)
    transaction_amount: Optional[float] = Field(None, gt=0)
    status: Optional[PlanStatus] = None
    back_url: Optional[str] = None


class SubscriptionPlanResponse(BaseModel):
    """Response con datos de un plan de suscripción"""
    id: int
    mp_plan_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    reason: str
    
    frequency: int
    frequency_type: FrequencyType
    transaction_amount: float
    currency_id: str
    
    repetitions: Optional[int] = None
    billing_day: Optional[int] = None
    billing_day_proportional: bool
    
    free_trial_frequency: Optional[int] = None
    free_trial_frequency_type: Optional[FrequencyType] = None
    
    status: PlanStatus
    created_at: datetime
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "mp_plan_id": "2c938084726fca480172750000000000",
                "name": "Plan Premium Mensual",
                "description": "Acceso completo a FitnessPro",
                "reason": "FitnessPro Premium - Mensual",
                "frequency": 1,
                "frequency_type": "months",
                "transaction_amount": 149.0,
                "currency_id": "MXN",
                "billing_day": 1,
                "billing_day_proportional": True,
                "free_trial_frequency": 7,
                "free_trial_frequency_type": "days",
                "status": "active",
                "created_at": "2026-04-03T10:30:00"
            }
        }


# === Schemas de Suscripción de Usuario ===

class SubscriptionCreateRequest(BaseModel):
    """Request para crear una suscripción de usuario"""
    user_id: int = Field(..., description="ID del usuario")
    plan_id: int = Field(..., description="ID del plan de suscripción")
    card_token_id: Optional[str] = Field(None, description="Token de tarjeta (para pago autorizado)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 1,
                "plan_id": 1,
                "card_token_id": "e3ed6f098462036dd2cbabe314b9de2a"
            }
        }


class SubscriptionCreateWithoutPlanRequest(BaseModel):
    """Request para crear una suscripción sin plan asociado"""
    user_id: int = Field(..., description="ID del usuario")
    reason: str = Field(..., description="Descripción de la suscripción")
    
    frequency: int = Field(1, ge=1, description="Cada cuánto se cobra")
    frequency_type: FrequencyType = Field(FrequencyType.MONTHS)
    transaction_amount: float = Field(..., gt=0, description="Monto del cobro")
    currency_id: str = Field("MXN", max_length=10)
    
    start_date: Optional[datetime] = Field(None, description="Fecha de inicio")
    end_date: Optional[datetime] = Field(None, description="Fecha de fin")
    
    card_token_id: Optional[str] = Field(None, description="Token de tarjeta")
    back_url: Optional[str] = Field(None, description="URL de retorno")


class SubscriptionResponse(BaseModel):
    """Response con datos de una suscripción"""
    id: int
    user_id: int
    plan_id: Optional[int] = None
    
    mp_preapproval_id: Optional[str] = None
    payer_email: str
    external_reference: Optional[str] = None
    reason: Optional[str] = None
    
    frequency: int
    frequency_type: FrequencyType
    transaction_amount: float
    currency_id: str
    
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    next_payment_date: Optional[datetime] = None
    
    status: SubscriptionStatus
    payments_count: int
    last_payment_date: Optional[datetime] = None
    
    init_point: Optional[str] = None
    
    created_at: datetime
    authorized_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "user_id": 1,
                "plan_id": 1,
                "mp_preapproval_id": "2c938084726fca480172750000000001",
                "payer_email": "usuario@example.com",
                "external_reference": "user_1_sub_1",
                "reason": "FitnessPro Premium - Mensual",
                "frequency": 1,
                "frequency_type": "months",
                "transaction_amount": 29.99,
                "currency_id": "MXN",
                "status": "authorized",
                "payments_count": 3,
                "created_at": "2026-04-03T10:30:00",
                "authorized_at": "2026-04-03T10:35:00"
            }
        }


class SubscriptionCheckoutResponse(BaseModel):
    """Response con URL de checkout para suscripción"""
    subscription_id: int = Field(..., description="ID de la suscripción local")
    mp_preapproval_id: Optional[str] = Field(None, description="ID en Mercado Pago")
    init_point: str = Field(..., description="URL de checkout de Mercado Pago")
    sandbox_init_point: Optional[str] = Field(None, description="URL sandbox")
    status: SubscriptionStatus
    
    class Config:
        json_schema_extra = {
            "example": {
                "subscription_id": 1,
                "mp_preapproval_id": "2c938084726fca480172750000000001",
                "init_point": "https://www.mercadopago.com.mx/subscriptions/checkout?preapproval_id=xxx",
                "sandbox_init_point": "https://sandbox.mercadopago.com.mx/subscriptions/checkout?preapproval_id=xxx",
                "status": "pending"
            }
        }


# === Schemas de Gestión de Suscripción ===

class SubscriptionPauseRequest(BaseModel):
    """Request para pausar una suscripción"""
    reason: Optional[str] = Field(None, description="Motivo de la pausa")


class SubscriptionCancelRequest(BaseModel):
    """Request para cancelar una suscripción"""
    reason: Optional[str] = Field(None, description="Motivo de la cancelación")


class SubscriptionUpdateAmountRequest(BaseModel):
    """Request para modificar el monto de una suscripción"""
    transaction_amount: float = Field(..., gt=0, description="Nuevo monto")
    currency_id: str = Field("MXN", description="Moneda")


class SubscriptionUpdateCardRequest(BaseModel):
    """Request para cambiar la tarjeta de una suscripción"""
    card_token_id: str = Field(..., description="Nuevo token de tarjeta")


class SubscriptionStatusResponse(BaseModel):
    """Response con estado detallado de una suscripción"""
    id: int
    user_id: int
    status: SubscriptionStatus
    
    transaction_amount: float
    currency_id: str
    
    next_payment_date: Optional[datetime] = None
    last_payment_date: Optional[datetime] = None
    payments_count: int
    failed_payments_count: int
    
    is_active: bool = Field(..., description="Si la suscripción está activa")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "user_id": 1,
                "status": "authorized",
                "transaction_amount": 29.99,
                "currency_id": "MXN",
                "next_payment_date": "2026-05-01T00:00:00",
                "last_payment_date": "2026-04-01T10:30:00",
                "payments_count": 3,
                "failed_payments_count": 0,
                "is_active": True
            }
        }


# === Schemas de Pagos de Suscripción ===

class SubscriptionPaymentResponse(BaseModel):
    """Response con datos de un pago de suscripción"""
    id: int
    subscription_id: int
    mp_payment_id: Optional[str] = None
    
    transaction_amount: float
    currency_id: str
    status: PaymentStatus
    
    rejection_reason: Optional[str] = None
    retry_attempt: int
    
    scheduled_date: Optional[datetime] = None
    payment_date: Optional[datetime] = None
    
    payment_method_id: Optional[str] = None
    payment_type: Optional[str] = None
    card_last_four: Optional[str] = None
    
    created_at: datetime
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "subscription_id": 1,
                "mp_payment_id": "123456789",
                "transaction_amount": 29.99,
                "currency_id": "MXN",
                "status": "processed",
                "retry_attempt": 1,
                "payment_date": "2026-04-01T10:30:00",
                "payment_method_id": "visa",
                "payment_type": "credit_card",
                "card_last_four": "1234",
                "created_at": "2026-04-01T10:30:00"
            }
        }


# === Schemas de Webhook ===

class SubscriptionWebhookData(BaseModel):
    """Datos del webhook de suscripción"""
    id: str = Field(..., description="ID del recurso")


class SubscriptionWebhookNotification(BaseModel):
    """Notificación de webhook de suscripción de Mercado Pago"""
    id: str = Field(..., description="ID de la notificación")
    type: str = Field(..., description="Tipo: subscription_preapproval o subscription_authorized_payment")
    action: Optional[str] = Field(None, description="Acción: created, updated, etc.")
    data: SubscriptionWebhookData = Field(..., description="Datos del evento")
    user_id: Optional[str] = None
    live_mode: bool = Field(False)
    date_created: Optional[datetime] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "1234567890",
                "type": "subscription_preapproval",
                "action": "updated",
                "data": {
                    "id": "2c938084726fca480172750000000001"
                },
                "user_id": "123456789",
                "live_mode": False,
                "date_created": "2026-04-03T10:30:00"
            }
        }


# === Schemas de Listado ===

class SubscriptionPlanListResponse(BaseModel):
    """Response con lista de planes"""
    plans: list[SubscriptionPlanResponse]
    total: int


class UserSubscriptionListResponse(BaseModel):
    """Response con lista de suscripciones de un usuario"""
    subscriptions: list[SubscriptionResponse]
    total: int


class SubscriptionPaymentListResponse(BaseModel):
    """Response con historial de pagos de una suscripción"""
    payments: list[SubscriptionPaymentResponse]
    total: int
