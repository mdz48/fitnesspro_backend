"""
Repositorio para pagos
"""
from sqlalchemy.orm import Session
from app.models.Payment import Payment
from app.repositories.base_repository import BaseRepository


class PaymentRepository(BaseRepository[Payment]):
    """Repositorio para operaciones CRUD de pagos"""
    
    def __init__(self, session: Session):
        super().__init__(Payment, session)
    
    def get_by_preference_id(self, preference_id: str) -> Payment | None:
        """Obtiene un pago por preference_id de Mercado Pago"""
        return self.db.query(Payment).filter(Payment.preference_id == preference_id).first()
    
    def get_by_payment_id(self, payment_id: str) -> Payment | None:
        """Obtiene un pago por payment_id de Mercado Pago"""
        return self.db.query(Payment).filter(Payment.payment_id == payment_id).first()
    
    def get_by_user_id(self, user_id: int) -> list[Payment]:
        """Obtiene todos los pagos de un usuario"""
        return self.db.query(Payment).filter(Payment.user_id == user_id).order_by(Payment.created_at.desc()).all()
    
    def get_by_external_reference(self, external_reference: str) -> Payment | None:
        """Obtiene un pago por referencia externa"""
        return self.db.query(Payment).filter(Payment.external_reference == external_reference).first()
