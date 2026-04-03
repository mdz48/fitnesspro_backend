"""
Modelo ORM para planes de suscripción de Mercado Pago
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.shared.config.database import Base


class SubscriptionPlan(Base):
    """
    Modelo para guardar planes de suscripción de Mercado Pago.
    
    Cada plan define precio, frecuencia y características de la suscripción.
    Corresponde al recurso /preapproval_plan de la API de Mercado Pago.
    """
    __tablename__ = "subscription_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # ID del plan en Mercado Pago (preapproval_plan_id)
    mp_plan_id = Column(String(255), nullable=True, unique=True, index=True)
    
    # Información básica del plan
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    reason = Column(String(255), nullable=False)  # Título visible para el usuario en MP
    
    # Configuración de cobros
    frequency = Column(Integer, nullable=False, default=1)  # Cada cuánto se cobra
    frequency_type = Column(
        Enum("days", "months", name="frequency_type_enum"),
        nullable=False,
        default="months"
    )
    transaction_amount = Column(Float, nullable=False)
    currency_id = Column(String(10), nullable=False, default="MXN")
    
    # Configuración de duración
    repetitions = Column(Integer, nullable=True)  # NULL = ilimitado
    billing_day = Column(Integer, nullable=True)  # Día del mes para cobrar (solo mensual)
    billing_day_proportional = Column(Boolean, nullable=False, default=True)
    
    # Período de prueba gratis
    free_trial_frequency = Column(Integer, nullable=True)  # NULL = sin trial
    free_trial_frequency_type = Column(
        Enum("days", "months", name="trial_frequency_type_enum"),
        nullable=True
    )
    
    # URL de retorno
    back_url = Column(String(500), nullable=True)
    
    # Estado del plan
    status = Column(
        Enum("active", "inactive", "cancelled", name="plan_status_enum"),
        nullable=False,
        default="active"
    )
    
    # Respuesta completa de Mercado Pago (para debugging)
    mp_response = Column(Text, nullable=True)
    
    # Auditoría
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relación con suscripciones
    subscriptions = relationship("UserSubscription", back_populates="plan")
    
    def __repr__(self):
        return (
            f"<SubscriptionPlan(id={self.id}, name={self.name}, "
            f"amount={self.transaction_amount} {self.currency_id}, "
            f"frequency={self.frequency} {self.frequency_type})>"
        )
