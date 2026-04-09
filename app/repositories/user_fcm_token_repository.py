"""Repositorio para tokens FCM de usuarios."""
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.UserFcmToken import UserFcmToken
from app.repositories.base_repository import BaseRepository


class UserFcmTokenRepository(BaseRepository[UserFcmToken]):
    """Operaciones CRUD para tokens FCM."""

    def __init__(self, db: Session):
        super().__init__(UserFcmToken, db)

    def get_by_token(self, fcm_token: str) -> UserFcmToken | None:
        return self.db.query(UserFcmToken).filter(UserFcmToken.fcm_token == fcm_token).first()

    def get_by_user_id(self, user_id: int) -> list[UserFcmToken]:
        return (
            self.db.query(UserFcmToken)
            .filter(UserFcmToken.user_id == user_id, UserFcmToken.is_active.is_(True))
            .order_by(UserFcmToken.created_at.asc())
            .all()
        )

    def upsert_token(self, user_id: int, fcm_token: str) -> UserFcmToken:
        normalized_token = fcm_token.strip()
        token = self.get_by_token(normalized_token)

        if token:
            token.user_id = user_id
            token.is_active = True
            token.last_seen_at = datetime.utcnow()
            return self.update(token)

        token = UserFcmToken(
            user_id=user_id,
            fcm_token=normalized_token,
            is_active=True,
            last_seen_at=datetime.utcnow(),
        )
        return self.create(token)