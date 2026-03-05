"""
Servicio para gestionar ejercicios de la API ExerciseDB
"""
from typing import List, Optional, Dict, Any
from app.interfaces.api_client_interface import IAPIClient
from app.services.translation_service import translation_service


class ExerciseService:
    """Servicio para consumir ExerciseDB API con DI"""
    
    def __init__(self, api_client: IAPIClient):
        """
        Inicializa el servicio con sus dependencias
        
        Args:
            api_client: Cliente para APIs externas
        """
        self.api_client = api_client

    async def _process_response(self, response: Any, is_list_of_strings: bool = False) -> Any:
        """Procesa y traduce la respuesta de la API"""
        if isinstance(response, dict):
            if 'data' in response:
                response['data'] = await translation_service.translate_exercise_data(response['data'])
            else:
                response = await translation_service.translate_exercise_data(response)
        elif isinstance(response, list):
            if is_list_of_strings:
                response = await translation_service.translate_list(response)
            else:
                response = await translation_service.translate_exercise_data(response)
        return response
    
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
            
        response = await self.api_client.get('/exercises', params=params)
        return await self._process_response(response)
    
    async def get_exercise_by_id(self, exercise_id: str) -> Dict[str, Any]:
        """
        Obtiene un ejercicio por su ID
        
        Args:
            exercise_id: ID del ejercicio
            
        Returns:
            Datos del ejercicio
        """
        response = await self.api_client.get(f'/exercises/{exercise_id}')
        return await self._process_response(response)
    
    async def get_exercises_by_bodypart(self, bodypart: str) -> Dict[str, Any]:
        """
        Obtiene ejercicios por parte del cuerpo
        
        Args:
            bodypart: Parte del cuerpo (ej: 'back', 'chest', 'legs')
            
        Returns:
            Lista de ejercicios
        """
        response = await self.api_client.get('/exercises/filter', params={'bodyParts': bodypart})
        return await self._process_response(response)
    
    async def get_exercises_by_target(self, target: str) -> Dict[str, Any]:
        """
        Obtiene ejercicios por músculo objetivo
        
        Args:
            target: Músculo objetivo
            
        Returns:
            Lista de ejercicios
        """
        response = await self.api_client.get('/exercises/filter', params={'targetMuscles': target})
        return await self._process_response(response)
    
    async def get_exercises_by_equipment(self, equipment: str) -> Dict[str, Any]:
        """
        Obtiene ejercicios por equipo
        
        Args:
            equipment: Tipo de equipo (ej: 'barbell', 'dumbbell', 'bodyweight')
            
        Returns:
            Lista de ejercicios
        """
        response = await self.api_client.get('/exercises/filter', params={'equipments': equipment})
        return await self._process_response(response)
    
    async def get_body_parts(self) -> List[str]:
        """
        Obtiene la lista de partes del cuerpo disponibles
        
        Returns:
            Lista de partes del cuerpo
        """
        response = await self.api_client.get('/exercises/bodyPartList')
        return await self._process_response(response, is_list_of_strings=True)
    
    async def get_target_muscles(self) -> List[str]:
        """
        Obtiene la lista de músculos objetivo disponibles
        
        Returns:
            Lista de músculos
        """
        response = await self.api_client.get('/exercises/targetList')
        return await self._process_response(response, is_list_of_strings=True)
    
    async def get_equipment_list(self) -> List[str]:
        """
        Obtiene la lista de equipos disponibles
        
        Returns:
            Lista de equipos
        """
        response = await self.api_client.get('/exercises/equipmentList')
        return await self._process_response(response, is_list_of_strings=True)
    
    async def close(self):
        """Cierra las conexiones del servicio"""
        await self.api_client.close()
