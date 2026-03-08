"""
Servicio para gestionar ejercicios de la API ExerciseDB y de la base de datos
"""
from typing import List, Optional, Dict, Any
from app.interfaces.api_client_interface import IAPIClient
from app.models.Exercise import Exercise
from app.repositories.exercise_repository import ExerciseRepository
from app.schemas.exercise_schema import ExerciseDatabaseCreate, ExerciseDatabaseUpdate, ExerciseDatabaseResponse, ExerciseDetailResponse, ExerciseListResponse, ExerciseSchema
from app.services.translation_service import translation_service



class ExerciseService:
    """Servicio para consumir ExerciseDB API y gestionar ejercicios en BD"""
    
    def __init__(self, api_client: IAPIClient, repository: ExerciseRepository):
        """
        Inicializa el servicio con sus dependencias
        
        Args:
            api_client: Cliente para APIs externas
            repository: Repositorio de ejercicios para BD
        """
        self.api_client = api_client
        self.repository = repository

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

    async def get_exercises_from_db(self) -> List[ExerciseDatabaseResponse]:
        """Obtiene todos los ejercicios del usuario desde la base de datos"""
        exercises = self.repository.get_all()
        return [
            ExerciseDatabaseResponse(
                id=e.id,
                name=e.name,
                description=e.description,
                user_id=e.user_id,
                scheduled_days=list(e.scheduled_days) if e.scheduled_days else [],
                image_url=e.image_url or "",
                bodyparts=list(e.bodyparts) if e.bodyparts else [],
                equipments=list(e.equipments) if e.equipments else [],
                targetMuscles=list(e.targetMuscles) if e.targetMuscles else [],
                secondaryMuscles=list(e.secondaryMuscles) if e.secondaryMuscles else [],
                exercise_type=e.exercise_type.value if e.exercise_type else "",
                instructions=e.instructions or ""
            ) for e in exercises
        ]
        
    async def get_exercises_by_user(self, user_id: int) -> List[ExerciseDatabaseResponse]:
        """Obtiene los ejercicios de un usuario específico desde la base de datos"""
        exercises = self.repository.get_by_user(user_id)
        return [
            ExerciseDatabaseResponse(
                id=e.id,
                name=e.name,
                description=e.description,
                user_id=e.user_id,
                scheduled_days=list(e.scheduled_days) if e.scheduled_days else [],
                image_url=e.image_url or "",
                bodyparts=list(e.bodyparts) if e.bodyparts else [],
                equipments=list(e.equipments) if e.equipments else [],
                targetMuscles=list(e.targetMuscles) if e.targetMuscles else [],
                secondaryMuscles=list(e.secondaryMuscles) if e.secondaryMuscles else [],
                exercise_type=e.exercise_type.value if e.exercise_type else "",
                instructions=e.instructions or ""
            ) for e in exercises
        ]

    async def create_exercise(self, exercise: ExerciseDatabaseCreate) -> ExerciseDatabaseResponse:
        """Crea un nuevo ejercicio en la base de datos"""
        db_exercise = Exercise(
            name=exercise.name,
            description=exercise.description,
            user_id=exercise.user_id,
            scheduled_days=set(exercise.scheduled_days) if exercise.scheduled_days else set(),
            image_url=exercise.image_url,
            bodyparts=set(exercise.bodyparts) if exercise.bodyparts else set(),
            equipments=set(exercise.equipments) if exercise.equipments else set(),
            targetMuscles=set(exercise.targetMuscles) if exercise.targetMuscles else set(),
            secondaryMuscles=set(exercise.secondaryMuscles) if exercise.secondaryMuscles else set(),
            exercise_type=exercise.exercise_type,
            instructions=exercise.instructions
        )
        created = self.repository.create(db_exercise)
        return ExerciseDatabaseResponse(
            id=created.id,
            name=created.name,
            description=created.description,
            user_id=created.user_id,
            scheduled_days=list(created.scheduled_days) if created.scheduled_days else [],
            image_url=created.image_url or "",
            bodyparts=list(created.bodyparts) if created.bodyparts else [],
            equipments=list(created.equipments) if created.equipments else [],
            targetMuscles=list(created.targetMuscles) if created.targetMuscles else [],
            secondaryMuscles=list(created.secondaryMuscles) if created.secondaryMuscles else [],
            exercise_type=created.exercise_type.value if created.exercise_type else "",
            instructions=created.instructions or ""
        )

    async def update_exercise(self, exercise_id: int, exercise: ExerciseDatabaseUpdate) -> ExerciseDatabaseResponse:
        """Actualiza un ejercicio existente en la base de datos"""
        db_exercise = self.repository.get_by_id(exercise_id)
        if not db_exercise:
            raise ValueError(f"Ejercicio con id {exercise_id} no encontrado")
        
        db_exercise.name = exercise.name
        db_exercise.description = exercise.description
        db_exercise.user_id = exercise.user_id
        db_exercise.scheduled_days = set(exercise.scheduled_days) if exercise.scheduled_days else set()
        db_exercise.image_url = exercise.image_url
        db_exercise.bodyparts = set(exercise.bodyparts) if exercise.bodyparts else set()
        db_exercise.equipments = set(exercise.equipments) if exercise.equipments else set()
        db_exercise.targetMuscles = set(exercise.targetMuscles) if exercise.targetMuscles else set()
        db_exercise.secondaryMuscles = set(exercise.secondaryMuscles) if exercise.secondaryMuscles else set()
        db_exercise.exercise_type = exercise.exercise_type
        db_exercise.instructions = exercise.instructions
        
        updated = self.repository.update(db_exercise)
        return ExerciseDatabaseResponse(
            id=updated.id,
            name=updated.name,
            description=updated.description,
            user_id=updated.user_id,
            scheduled_days=list(updated.scheduled_days) if updated.scheduled_days else [],
            image_url=updated.image_url or "",
            bodyparts=list(updated.bodyparts) if updated.bodyparts else [],
            equipments=list(updated.equipments) if updated.equipments else [],
            targetMuscles=list(updated.targetMuscles) if updated.targetMuscles else [],
            secondaryMuscles=list(updated.secondaryMuscles) if updated.secondaryMuscles else [],
            exercise_type=updated.exercise_type.value if updated.exercise_type else "",
            instructions=updated.instructions or ""
        )

    async def delete_exercise(self, exercise_id: int) -> dict:
        """Elimina un ejercicio de la base de datos"""
        db_exercise = self.repository.get_by_id(exercise_id)
        if not db_exercise:
            raise ValueError(f"Ejercicio con id {exercise_id} no encontrado")
        self.repository.delete(db_exercise)
        return {"message": f"Ejercicio con id {exercise_id} eliminado exitosamente"}
    
    