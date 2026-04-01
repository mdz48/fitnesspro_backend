"""
Esquemas para pagos y preferencias de Mercado Pago
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class PaymentPreferenceRequest(BaseModel):
    """Request para crear una preferencia de pago"""
    user_id: int = Field(..., description="ID del usuario que realiza el pago")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 1
            }
        }


class PaymentPreferenceResponse(BaseModel):
    """Response con datos de preferencia de pago"""
    preference_id: str = Field(..., description="ID de preferencia de Mercado Pago")
    init_point: str = Field(..., description="URL de checkout de Mercado Pago")
    sandbox_init_point: str = Field(..., description="URL sandbox de Mercado Pago")
    
    class Config:
        json_schema_extra = {
            "example": {
                "preference_id": "123456789",
                "init_point": "https://www.mercadopago.com.mx/checkout/v1/redirect?pref_id=123456789",
                "sandbox_init_point": "https://sandbox.mercadopago.com.mx/checkout/v1/redirect?pref_id=123456789"
            }
        }


class PaymentStatusResponse(BaseModel):
    """Response con estado de preferencia de pago"""
    preference_id: str
    status: str
    user_id: int
    amount: float
    currency: str
    created_at: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "preference_id": "123456789",
                "status": "pending",
                "user_id": 1,
                "amount": 149.0,
                "currency": "MXN",
                "created_at": "2026-03-31T10:30:00"
            }
        }


class WebhookNotification(BaseModel):
    """Notificación de webhook de Mercado Pago"""
    id: str = Field(..., description="ID de la notificación")
    type: str = Field(..., description="Tipo de notificación (payment, plan, subscription, etc.)")
    data: dict = Field(..., description="Datos del evento")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "1234567890",
                "type": "payment",
                "data": {
                    "id": "payment_id_123"
                }
            }
        }
