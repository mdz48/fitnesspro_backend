"""
Modelo ORM para pagos y preferencias de Mercado Pago
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Payment(Base):
    """Modelo para guardar datos de pagos/preferencias de Mercado Pago"""
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    preference_id = Column(String(255), nullable=False, unique=True, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), nullable=False, default="MXN")
    status = Column(String(50), nullable=False, default="pending")  # pending, approved, rejected
    payment_id = Column(String(255), nullable=True, unique=True, index=True)  # ID del pago cuando sea aprobado
    external_reference = Column(String(255), nullable=True, index=True)  # Referencia externa (ej: user_id)
    mercadopago_response = Column(Text, nullable=True)  # JSON con respuesta completa de MP
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    confirmed_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return (
            f"<Payment(id={self.id}, user_id={self.user_id}, preference_id={self.preference_id}, "
            f"status={self.status}, amount={self.amount})>"
        )
