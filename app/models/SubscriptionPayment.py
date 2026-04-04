"""
Modelo ORM para pagos de suscripciones (cobros recurrentes)
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.shared.config.database import Base


class SubscriptionPayment(Base):
    """
    Modelo para guardar el historial de pagos de suscripciones.
    
    Corresponde a los authorized_payments generados por Mercado Pago
    en cada ciclo de cobro de una suscripción.
    """
    __tablename__ = "subscription_payments"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Relación con suscripción
    subscription_id = Column(
        Integer, 
        ForeignKey("user_subscriptions.id"), 
        nullable=False, 
        index=True
    )
    
    # IDs de Mercado Pago
    mp_payment_id = Column(String(255), nullable=True, unique=True, index=True)
    mp_preapproval_id = Column(String(255), nullable=True, index=True)
    
    # Monto del cobro
    transaction_amount = Column(Float, nullable=False)
    currency_id = Column(String(10), nullable=False, default="MXN")
    
    # Estado del pago
    # processed: cobro exitoso
    # recycling: en proceso de reintento (hasta 4 veces en 10 días)
    # waiting_for_gateway: procesando pago
    # rejected: rechazado definitivamente
    # refunded: devuelto
    status = Column(
        Enum(
            "processed", 
            "recycling", 
            "waiting_for_gateway", 
            "rejected",
            "refunded",
            name="payment_status_enum"
        ),
        nullable=False,
        default="waiting_for_gateway"
    )
    
    # Motivo de rechazo (si aplica)
    rejection_reason = Column(String(255), nullable=True)
    
    # Número de intento de cobro
    retry_attempt = Column(Integer, nullable=False, default=1)
    
    # Fecha programada del cobro
    scheduled_date = Column(DateTime, nullable=True)
    
    # Fecha efectiva del pago
    payment_date = Column(DateTime, nullable=True)
    
    # Información del método de pago
    payment_method_id = Column(String(100), nullable=True)
    payment_type = Column(String(100), nullable=True)  # credit_card, debit_card, etc.
    
    # Últimos 4 dígitos de la tarjeta (para referencia)
    card_last_four = Column(String(4), nullable=True)
    
    # Respuesta completa de Mercado Pago
    mp_response = Column(Text, nullable=True)
    
    # Auditoría
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relación con suscripción
    subscription = relationship("UserSubscription", back_populates="payments")
    
    def __repr__(self):
        return (
            f"<SubscriptionPayment(id={self.id}, subscription_id={self.subscription_id}, "
            f"status={self.status}, amount={self.transaction_amount} {self.currency_id})>"
        )
