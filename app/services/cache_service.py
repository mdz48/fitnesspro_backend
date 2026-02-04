"""
Sistema de caché en memoria con TTL (Time To Live)
"""
from typing import Any, Optional
from datetime import datetime, timedelta
import hashlib
import json


class InMemoryCache:
    """Caché simple en memoria con expiración automática"""
    
    def __init__(self):
        self._cache = {}  # {key: {"data": Any, "expires_at": datetime}}
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """
        Genera una clave única basada en los parámetros
        
        Args:
            prefix: Prefijo para la clave (ej: 'exercise', 'bodypart')
            *args: Argumentos posicionales
            **kwargs: Argumentos nombrados
            
        Returns:
            Clave hash única
        """
        # Crear un string único con todos los parámetros
        key_data = {
            "prefix": prefix,
            "args": args,
            "kwargs": sorted(kwargs.items()) if kwargs else []
        }
        key_string = json.dumps(key_data, sort_keys=True)
        
        # Generar hash MD5 para la clave
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(self, prefix: str, *args, **kwargs) -> Optional[Any]:
        """
        Obtiene un valor del caché si existe y no ha expirado
        
        Args:
            prefix: Prefijo de la clave
            *args: Argumentos para generar la clave
            **kwargs: Argumentos nombrados para generar la clave
            
        Returns:
            Valor en caché o None si no existe o expiró
        """
        key = self._generate_key(prefix, *args, **kwargs)
        
        if key not in self._cache:
            return None
        
        cache_entry = self._cache[key]
        
        # Verificar si expiró
        if datetime.now() > cache_entry["expires_at"]:
            del self._cache[key]
            return None
        
        return cache_entry["data"]
    
    def set(self, prefix: str, value: Any, ttl_seconds: int, *args, **kwargs) -> None:
        """
        Guarda un valor en el caché con tiempo de expiración
        
        Args:
            prefix: Prefijo de la clave
            value: Valor a guardar
            ttl_seconds: Tiempo de vida en segundos
            *args: Argumentos para generar la clave
            **kwargs: Argumentos nombrados para generar la clave
        """
        key = self._generate_key(prefix, *args, **kwargs)
        expires_at = datetime.now() + timedelta(seconds=ttl_seconds)
        
        self._cache[key] = {
            "data": value,
            "expires_at": expires_at
        }
    
    def clear(self) -> None:
        """Limpia todo el caché"""
        self._cache.clear()
    
    def clear_expired(self) -> int:
        """
        Limpia las entradas expiradas del caché
        
        Returns:
            Número de entradas eliminadas
        """
        now = datetime.now()
        expired_keys = [
            key for key, value in self._cache.items()
            if now > value["expires_at"]
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        return len(expired_keys)
    
    def size(self) -> int:
        """Retorna el número de entradas en caché"""
        return len(self._cache)


# Instancia global del caché
cache = InMemoryCache()
