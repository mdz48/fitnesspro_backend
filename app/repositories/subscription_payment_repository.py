"""
Repositorio para pagos de suscripciones (cobros recurrentes)
"""
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.SubscriptionPayment import SubscriptionPayment
from app.repositories.base_repository import BaseRepository


class SubscriptionPaymentRepository(BaseRepository[SubscriptionPayment]):
    """Repositorio para operaciones CRUD de pagos de suscripciones"""
    
    def __init__(self, session: Session):
        super().__init__(SubscriptionPayment, session)
    
    def get_by_mp_payment_id(self, mp_payment_id: str) -> SubscriptionPayment | None:
        """Obtiene un pago por su ID de Mercado Pago"""
        return (
            self.db.query(SubscriptionPayment)
            .filter(SubscriptionPayment.mp_payment_id == mp_payment_id)
            .first()
        )
    
    def get_by_subscription_id(self, subscription_id: int) -> list[SubscriptionPayment]:
        """Obtiene todos los pagos de una suscripción"""
        return (
            self.db.query(SubscriptionPayment)
            .filter(SubscriptionPayment.subscription_id == subscription_id)
            .order_by(desc(SubscriptionPayment.created_at))
            .all()
        )
    
    def get_by_mp_preapproval_id(self, mp_preapproval_id: str) -> list[SubscriptionPayment]:
        """Obtiene pagos por ID de preapproval de Mercado Pago"""
        return (
            self.db.query(SubscriptionPayment)
            .filter(SubscriptionPayment.mp_preapproval_id == mp_preapproval_id)
            .order_by(desc(SubscriptionPayment.created_at))
            .all()
        )
    
    def get_by_status(self, status: str) -> list[SubscriptionPayment]:
        """Obtiene pagos por estado"""
        return (
            self.db.query(SubscriptionPayment)
            .filter(SubscriptionPayment.status == status)
            .all()
        )
    
    def get_last_payment(self, subscription_id: int) -> SubscriptionPayment | None:
        """Obtiene el último pago de una suscripción"""
        return (
            self.db.query(SubscriptionPayment)
            .filter(SubscriptionPayment.subscription_id == subscription_id)
            .order_by(desc(SubscriptionPayment.created_at))
            .first()
        )
    
    def get_successful_payments(self, subscription_id: int) -> list[SubscriptionPayment]:
        """Obtiene los pagos exitosos de una suscripción"""
        return (
            self.db.query(SubscriptionPayment)
            .filter(
                SubscriptionPayment.subscription_id == subscription_id,
                SubscriptionPayment.status == "processed"
            )
            .order_by(desc(SubscriptionPayment.payment_date))
            .all()
        )
    
    def count_by_subscription(self, subscription_id: int) -> int:
        """Cuenta el total de pagos de una suscripción"""
        return (
            self.db.query(SubscriptionPayment)
            .filter(SubscriptionPayment.subscription_id == subscription_id)
            .count()
        )
    
    def count_successful_by_subscription(self, subscription_id: int) -> int:
        """Cuenta los pagos exitosos de una suscripción"""
        return (
            self.db.query(SubscriptionPayment)
            .filter(
                SubscriptionPayment.subscription_id == subscription_id,
                SubscriptionPayment.status == "processed"
            )
            .count()
        )
