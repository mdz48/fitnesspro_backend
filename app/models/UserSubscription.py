"""
Modelo ORM para suscripciones de usuarios con Mercado Pago
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.shared.config.database import Base


class UserSubscription(Base):
    """
    Modelo para guardar suscripciones de usuarios a planes de Mercado Pago.
    
    Corresponde al recurso /preapproval de la API de Mercado Pago.
    Cada suscripción vincula un usuario con un plan y gestiona el estado del cobro recurrente.
    """
    __tablename__ = "user_subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Relación con usuario
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Relación con plan (opcional, puede ser suscripción sin plan asociado)
    plan_id = Column(Integer, ForeignKey("subscription_plans.id"), nullable=True, index=True)
    
    # IDs de Mercado Pago
    mp_preapproval_id = Column(String(255), nullable=True, unique=True, index=True)
    mp_plan_id = Column(String(255), nullable=True, index=True)  # ID del plan en MP
    
    # Información del pagador
    payer_email = Column(String(255), nullable=False)
    payer_id = Column(String(255), nullable=True)  # ID del pagador en MP
    
    # Referencia externa para identificar la suscripción
    external_reference = Column(String(255), nullable=True, index=True)
    
    # Descripción de la suscripción
    reason = Column(String(255), nullable=True)
    
    # Configuración de cobros (puede diferir del plan)
    frequency = Column(Integer, nullable=False, default=1)
    frequency_type = Column(
        Enum("days", "months", name="sub_frequency_type_enum"),
        nullable=False,
        default="months"
    )
    transaction_amount = Column(Float, nullable=False)
    currency_id = Column(String(10), nullable=False, default="MXN")
    
    # Fechas de la suscripción
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    next_payment_date = Column(DateTime, nullable=True)
    
    # Estado de la suscripción en Mercado Pago
    # pending: esperando autorización
    # authorized: activa y cobrando
    # paused: pausada temporalmente
    # cancelled: cancelada definitivamente
    status = Column(
        Enum("pending", "authorized", "paused", "cancelled", name="subscription_status_enum"),
        nullable=False,
        default="pending"
    )
    
    # Token de la tarjeta (para cambio de medio de pago)
    card_token_id = Column(String(255), nullable=True)
    
    # Última fecha de pago exitoso
    last_payment_date = Column(DateTime, nullable=True)
    
    # Contador de pagos realizados
    payments_count = Column(Integer, nullable=False, default=0)
    
    # Contador de pagos fallidos consecutivos
    failed_payments_count = Column(Integer, nullable=False, default=0)
    
    # Respuesta completa de Mercado Pago
    mp_response = Column(Text, nullable=True)
    
    # URLs
    init_point = Column(String(500), nullable=True)
    back_url = Column(String(500), nullable=True)
    
    # Auditoría
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    authorized_at = Column(DateTime, nullable=True)  # Fecha de primera autorización
    cancelled_at = Column(DateTime, nullable=True)
    
    # Relaciones
    plan = relationship("SubscriptionPlan", back_populates="subscriptions")
    payments = relationship("SubscriptionPayment", back_populates="subscription")
    
    def __repr__(self):
        return (
            f"<UserSubscription(id={self.id}, user_id={self.user_id}, "
            f"status={self.status}, amount={self.transaction_amount} {self.currency_id})>"
        )
