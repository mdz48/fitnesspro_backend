"""
Repositorio para operaciones de datos de usuarios
"""
from typing import Optional
from sqlalchemy.orm import Session
from app.models.User import User
from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, db: Session):
        super().__init__(User, db)
    
    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()
    
    def email_exists(self, email: str) -> bool:
        return self.get_by_email(email) is not None
