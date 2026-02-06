"""
Cliente HTTP para consumir APIs externas
"""
import httpx
from typing import Optional, Dict, Any
from fastapi import HTTPException
from app.shared.config.external_api_config import REQUEST_TIMEOUT, CACHE_TTL
from app.services.cache_service import cache


class ExternalAPIClient:
    """Cliente base para hacer peticiones HTTP a APIs externas con caché"""
    
    def __init__(self, base_url: str, enable_cache: bool = True):
        self.base_url = base_url.rstrip('/')
        self.client = httpx.AsyncClient(timeout=REQUEST_TIMEOUT)
        self.enable_cache = enable_cache
    
    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None, use_cache: bool = True) -> Any:
        """
        Realiza una petición GET a la API externa con soporte de caché
        
        Args:
            endpoint: Endpoint relativo (ej: '/exercises')
            params: Parámetros de query string opcionales
            use_cache: Si debe usar caché (default: True)
            
        Returns:
            Respuesta JSON de la API
            
        Raises:
            HTTPException: Si la petición falla
        """
        # Intentar obtener del caché primero
        if self.enable_cache and use_cache:
            cached_data = cache.get("api_request", endpoint, params=params)
            if cached_data is not None:
                return cached_data
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Guardar en caché
            if self.enable_cache and use_cache:
                cache.set("api_request", data, CACHE_TTL, endpoint, params=params)
            
            return data
            
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Error en API externa: {e.response.text}"
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=503,
                detail=f"No se pudo conectar a la API externa: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error inesperado: {str(e)}"
            )
    
    async def close(self):
        """Cierra la conexión del cliente HTTP"""
        await self.client.aclose()
