"""
Servicio para gestionar ejercicios de la API ExerciseDB
"""
from typing import List, Optional, Dict, Any
from app.services.external_api_service import ExternalAPIClient
from app.shared.config.external_api_config import EXERCISEDB_BASE_URL


class ExerciseService:
    """Servicio para consumir ExerciseDB API"""
    
    def __init__(self):
        self.api_client = ExternalAPIClient(EXERCISEDB_BASE_URL)
    
    async def get_all_exercises(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Obtiene todos los ejercicios
        
        Args:
            limit: Número máximo de resultados
            offset: Número de resultados a saltar
            
        Returns:
            Lista de ejercicios
        """
        params = {}
        if limit is not None:
            params['limit'] = limit
        if offset is not None:
            params['offset'] = offset
            
        return await self.api_client.get('/exercises', params=params)
    
    async def get_exercise_by_id(self, exercise_id: str) -> Dict[str, Any]:
        """
        Obtiene un ejercicio por su ID
        
        Args:
            exercise_id: ID del ejercicio
            
        Returns:
            Datos del ejercicio
        """
        return await self.api_client.get(f'/exercises/{exercise_id}')
    
    async def get_exercises_by_bodypart(self, bodypart: str) -> List[Dict[str, Any]]:
        """
        Obtiene ejercicios por parte del cuerpo
        
        Args:
            bodypart: Parte del cuerpo (ej: 'back', 'chest', 'legs')
            
        Returns:
            Lista de ejercicios
        """
        return await self.api_client.get(f'/exercises/bodyPart/{bodypart}')
    
    async def get_exercises_by_target(self, target: str) -> List[Dict[str, Any]]:
        """
        Obtiene ejercicios por músculo objetivo
        
        Args:
            target: Músculo objetivo
            
        Returns:
            Lista de ejercicios
        """
        return await self.api_client.get(f'/exercises/target/{target}')
    
    async def get_exercises_by_equipment(self, equipment: str) -> List[Dict[str, Any]]:
        """
        Obtiene ejercicios por equipo
        
        Args:
            equipment: Tipo de equipo (ej: 'barbell', 'dumbbell', 'bodyweight')
            
        Returns:
            Lista de ejercicios
        """
        return await self.api_client.get(f'/exercises/equipment/{equipment}')
    
    async def get_body_parts(self) -> List[str]:
        """
        Obtiene la lista de partes del cuerpo disponibles
        
        Returns:
            Lista de partes del cuerpo
        """
        return await self.api_client.get('/exercises/bodyPartList')
    
    async def get_target_muscles(self) -> List[str]:
        """
        Obtiene la lista de músculos objetivo disponibles
        
        Returns:
            Lista de músculos
        """
        return await self.api_client.get('/exercises/targetList')
    
    async def get_equipment_list(self) -> List[str]:
        """
        Obtiene la lista de equipos disponibles
        
        Returns:
            Lista de equipos
        """
        return await self.api_client.get('/exercises/equipmentList')
    
    async def close(self):
        """Cierra las conexiones del servicio"""
        await self.api_client.close()
