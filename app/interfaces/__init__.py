"""
Interfaces y protocolos para abstracciones
"""
from app.interfaces.security_interface import ISecurityService
from app.interfaces.api_client_interface import IAPIClient

__all__ = [
    "ISecurityService",
    "IAPIClient",
]
