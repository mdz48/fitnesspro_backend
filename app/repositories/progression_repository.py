"""
Repositorio para operaciones de progreso de peso de usuarios
"""
from sqlalchemy.orm import Session
from app.models.UserProgression import WeightProgress
from app.repositories.base_repository import BaseRepository


class ProgressionRepository(BaseRepository[WeightProgress]):
    def __init__(self, db: Session):
        super().__init__(WeightProgress, db)

    def get_by_user_id(self, user_id: int) -> list[WeightProgress]:
        return (
            self.db.query(WeightProgress)
            .filter(WeightProgress.user_id == user_id)
            .order_by(WeightProgress.date.asc())
            .all()
        )

    def get_latest_by_user_id(self, user_id: int) -> WeightProgress | None:
        return (
            self.db.query(WeightProgress)
            .filter(WeightProgress.user_id == user_id)
            .order_by(WeightProgress.date.desc())
            .first()
        )
