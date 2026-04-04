"""
Repositorio para suscripciones de usuarios
"""
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.UserSubscription import UserSubscription
from app.repositories.base_repository import BaseRepository


class UserSubscriptionRepository(BaseRepository[UserSubscription]):
    """Repositorio para operaciones CRUD de suscripciones de usuarios"""
    
    def __init__(self, session: Session):
        super().__init__(UserSubscription, session)
    
    def get_by_mp_preapproval_id(self, mp_preapproval_id: str) -> UserSubscription | None:
        """Obtiene una suscripción por su ID de preapproval de Mercado Pago"""
        return (
            self.db.query(UserSubscription)
            .filter(UserSubscription.mp_preapproval_id == mp_preapproval_id)
            .first()
        )
    
    def get_by_external_reference(self, external_reference: str) -> UserSubscription | None:
        """Obtiene una suscripción por referencia externa"""
        return (
            self.db.query(UserSubscription)
            .filter(UserSubscription.external_reference == external_reference)
            .first()
        )
    
    def get_by_user_id(self, user_id: int) -> list[UserSubscription]:
        """Obtiene todas las suscripciones de un usuario"""
        return (
            self.db.query(UserSubscription)
            .filter(UserSubscription.user_id == user_id)
            .order_by(desc(UserSubscription.created_at))
            .all()
        )
    
    def get_active_by_user_id(self, user_id: int) -> UserSubscription | None:
        """Obtiene la suscripción activa de un usuario"""
        return (
            self.db.query(UserSubscription)
            .filter(
                UserSubscription.user_id == user_id,
                UserSubscription.status == "authorized"
            )
            .first()
        )
    
    def get_by_status(self, status: str) -> list[UserSubscription]:
        """Obtiene todas las suscripciones por estado"""
        return (
            self.db.query(UserSubscription)
            .filter(UserSubscription.status == status)
            .all()
        )
    
    def get_by_plan_id(self, plan_id: int) -> list[UserSubscription]:
        """Obtiene todas las suscripciones de un plan específico"""
        return (
            self.db.query(UserSubscription)
            .filter(UserSubscription.plan_id == plan_id)
            .order_by(desc(UserSubscription.created_at))
            .all()
        )
    
    def get_by_payer_email(self, payer_email: str) -> list[UserSubscription]:
        """Obtiene suscripciones por email del pagador"""
        return (
            self.db.query(UserSubscription)
            .filter(UserSubscription.payer_email == payer_email)
            .order_by(desc(UserSubscription.created_at))
            .all()
        )
    
    def count_by_status(self, status: str) -> int:
        """Cuenta suscripciones por estado"""
        return (
            self.db.query(UserSubscription)
            .filter(UserSubscription.status == status)
            .count()
        )
