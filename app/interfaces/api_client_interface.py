"""
Interface para clientes de APIs externas (abstracción)
"""
from typing import Protocol, Optional, Dict, Any


class IAPIClient(Protocol):
    """Protocolo para clientes de APIs externas"""
    
    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None, use_cache: bool = True) -> Any:
        """
        Realiza una petición GET
        
        Args:
            endpoint: Endpoint a consultar
            params: Parámetros opcionales
            use_cache: Si debe usar caché
            
        Returns:
            Respuesta de la API
        """
        ...
    
    async def close(self) -> None:
        """Cierra el cliente HTTP"""
        ...
