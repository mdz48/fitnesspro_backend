"""Modelo ORM para tokens FCM por usuario."""
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.shared.config.database import Base


class UserFcmToken(Base):
    """Token FCM persistido por dispositivo."""

    __tablename__ = "user_fcm_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    fcm_token = Column(String(512), nullable=False, unique=True)
    is_active = Column(Boolean, nullable=False, default=True)
    last_seen_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="fcm_tokens")

    def __repr__(self) -> str:
        return f"<UserFcmToken(id={self.id}, user_id={self.user_id}, is_active={self.is_active})>"