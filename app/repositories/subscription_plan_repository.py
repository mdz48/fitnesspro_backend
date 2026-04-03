"""
Repositorio para planes de suscripción
"""
from sqlalchemy.orm import Session
from app.models.SubscriptionPlan import SubscriptionPlan
from app.repositories.base_repository import BaseRepository


class SubscriptionPlanRepository(BaseRepository[SubscriptionPlan]):
    """Repositorio para operaciones CRUD de planes de suscripción"""
    
    def __init__(self, session: Session):
        super().__init__(SubscriptionPlan, session)
    
    def get_by_mp_plan_id(self, mp_plan_id: str) -> SubscriptionPlan | None:
        """Obtiene un plan por su ID de Mercado Pago"""
        return (
            self.db.query(SubscriptionPlan)
            .filter(SubscriptionPlan.mp_plan_id == mp_plan_id)
            .first()
        )
    
    def get_by_name(self, name: str) -> SubscriptionPlan | None:
        """Obtiene un plan por nombre"""
        return (
            self.db.query(SubscriptionPlan)
            .filter(SubscriptionPlan.name == name)
            .first()
        )
    
    def get_active_plans(self) -> list[SubscriptionPlan]:
        """Obtiene todos los planes activos"""
        return (
            self.db.query(SubscriptionPlan)
            .filter(SubscriptionPlan.status == "active")
            .order_by(SubscriptionPlan.transaction_amount)
            .all()
        )
    
    def get_by_status(self, status: str) -> list[SubscriptionPlan]:
        """Obtiene planes por estado"""
        return (
            self.db.query(SubscriptionPlan)
            .filter(SubscriptionPlan.status == status)
            .all()
        )
