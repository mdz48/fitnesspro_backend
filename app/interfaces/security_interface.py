"""
Interface para servicios de seguridad (abstracción)
"""
from typing import Protocol, Optional
from datetime import timedelta


class ISecurityService(Protocol):
    """Protocolo para servicios de seguridad"""
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verifica que una contraseña coincida con su hash"""
        ...
    
    def get_password_hash(self, password: str) -> str:
        """Genera el hash de una contraseña"""
        ...
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Crea un token de acceso JWT"""
        ...
