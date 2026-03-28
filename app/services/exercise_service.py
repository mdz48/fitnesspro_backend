"""
Servicio para gestionar ejercicios de la API ExerciseDB y de la base de datos
"""
import unicodedata
from typing import List, Optional, Dict, Any, Type
from enum import Enum
from app.interfaces.api_client_interface import IAPIClient
from app.models.Exercise import Exercise
from app.models.Enums import BodyPartEnum, EquipmentEnum, MuscleEnum
from app.repositories.exercise_repository import ExerciseRepository
from app.schemas.exercise_schema import ExerciseDatabaseCreate, ExerciseDatabaseUpdate, ExerciseDatabaseResponse, ExerciseDetailResponse, ExerciseListResponse, ExerciseSchema
from app.services.translation_service import translation_service



from app.services.cache_service import cache

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
        self.cache_ttl = 3600 # 1 hora de caché
        self.bodypart_map = self._build_spanish_to_english_map(BodyPartEnum)
        self.target_map = self._build_spanish_to_english_map(MuscleEnum)
        self.equipment_map = self._build_spanish_to_english_map(EquipmentEnum)

    @staticmethod
    def _normalize_filter_value(value: str) -> str:
        """Normaliza texto para búsquedas robustas (sin tildes y en minúsculas)."""
        base_value = (value or "").replace("_", " ").replace("-", " ")
        collapsed_spaces = " ".join(base_value.split())
        normalized = unicodedata.normalize("NFKD", collapsed_spaces)
        return "".join(ch for ch in normalized if not unicodedata.combining(ch)).strip().lower()

    @staticmethod
    def _build_spanish_to_english_map(enum_cls: Type[Enum]) -> Dict[str, str]:
        """Crea mapa de valor en español a valor en inglés esperado por la API remota."""
        result: Dict[str, str] = {}
        for member in enum_cls:
            spanish_key = ExerciseService._normalize_filter_value(str(member.value))
            english_value = member.name.lower().replace("_", " ")
            result[spanish_key] = english_value
            result[ExerciseService._normalize_filter_value(english_value)] = english_value
            result[ExerciseService._normalize_filter_value(member.name)] = english_value
        return result

    def _map_filter_to_english(self, value: str, value_map: Dict[str, str]) -> str:
        """Mapea filtros en español a inglés; si no hay match, conserva el valor original."""
        normalized_value = self._normalize_filter_value(value)
        # Fallback: estandarizar separadores y espacios para la API remota.
        return value_map.get(normalized_value, " ".join((value or "").replace("_", " ").replace("-", " ").split()))

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
        # Intentar obtener del caché
        cached_data = cache.get("exercises", limit=limit, offset=offset)
        if cached_data:
            return cached_data

        params = {}
        if limit is not None:
            params['limit'] = limit
        if offset is not None:
            params['offset'] = offset
            
        response = await self.api_client.get('/exercises', params=params)
        processed_data = await self._process_response(response)
        
        # Guardar en caché
        cache.set("exercises", processed_data, self.cache_ttl, limit=limit, offset=offset)
        return processed_data
    
    async def get_exercise_by_id(self, exercise_id: str) -> Dict[str, Any]:
        """
        Obtiene un ejercicio por su ID
        
        Args:
            exercise_id: ID del ejercicio
            
        Returns:
            Datos del ejercicio
        """
        # Intentar obtener del caché
        cached_data = cache.get("exercise_detail", id=exercise_id)
        if cached_data:
            return cached_data

        response = await self.api_client.get(f'/exercises/{exercise_id}')
        processed_data = await self._process_response(response)

        # Guardar en caché
        cache.set("exercise_detail", processed_data, self.cache_ttl, id=exercise_id)
        return processed_data
    
    async def get_exercises_by_bodypart(self, bodypart: str) -> Dict[str, Any]:
        """
        Obtiene ejercicios por parte del cuerpo
        
        Args:
            bodypart: Parte del cuerpo (ej: 'back', 'chest', 'legs')
            
        Returns:
            Lista de ejercicios
        """
        mapped_bodypart = self._map_filter_to_english(bodypart, self.bodypart_map)

        # Intentar obtener del caché
        cached_data = cache.get("exercises_bodypart", bodypart=mapped_bodypart)
        if cached_data:
            return cached_data

        response = await self.api_client.get('/exercises/filter', params={'bodyParts': mapped_bodypart})
        processed_data = await self._process_response(response)

        # Guardar en caché
        cache.set("exercises_bodypart", processed_data, self.cache_ttl, bodypart=mapped_bodypart)
        return processed_data
    
    async def get_exercises_by_target(self, target: str) -> Dict[str, Any]:
        """
        Obtiene ejercicios por músculo objetivo
        
        Args:
            target: Músculo objetivo
            
        Returns:
            Lista de ejercicios
        """
        mapped_target = self._map_filter_to_english(target, self.target_map)

        # Intentar obtener del caché
        cached_data = cache.get("exercises_target", target=mapped_target)
        if cached_data:
            return cached_data

        response = await self.api_client.get('/exercises/filter', params={'targetMuscles': mapped_target})
        processed_data = await self._process_response(response)

        # Guardar en caché
        cache.set("exercises_target", processed_data, self.cache_ttl, target=mapped_target)
        return processed_data
    
    async def get_exercises_by_equipment(self, equipment: str) -> Dict[str, Any]:
        """
        Obtiene ejercicios por equipo
        
        Args:
            equipment: Tipo de equipo (ej: 'barbell', 'dumbbell', 'bodyweight')
            
        Returns:
            Lista de ejercicios
        """
        mapped_equipment = self._map_filter_to_english(equipment, self.equipment_map)

        # Intentar obtener del caché
        cached_data = cache.get("exercises_equipment", equipment=mapped_equipment)
        if cached_data:
            return cached_data

        response = await self.api_client.get('/exercises/filter', params={'equipments': mapped_equipment})
        processed_data = await self._process_response(response)

        # Guardar en caché
        cache.set("exercises_equipment", processed_data, self.cache_ttl, equipment=mapped_equipment)
        return processed_data
    
    async def get_body_parts(self) -> List[str]:
        """
        Obtiene la lista de partes del cuerpo disponibles
        
        Returns:
            Lista de partes del cuerpo
        """
        # Intentar obtener del caché
        cached_data = cache.get("metadata_bodyparts")
        if cached_data:
            return cached_data

        response = await self.api_client.get('/exercises/bodyPartList')
        processed_data = await self._process_response(response, is_list_of_strings=True)

        # Guardar en caché
        cache.set("metadata_bodyparts", processed_data, self.cache_ttl)
        return processed_data
    
    async def get_target_muscles(self) -> List[str]:
        """
        Obtiene la lista de músculos objetivo disponibles
        
        Returns:
            Lista de músculos
        """
        # Intentar obtener del caché
        cached_data = cache.get("metadata_targets")
        if cached_data:
            return cached_data

        response = await self.api_client.get('/exercises/targetList')
        processed_data = await self._process_response(response, is_list_of_strings=True)

        # Guardar en caché
        cache.set("metadata_targets", processed_data, self.cache_ttl)
        return processed_data
    
    async def get_equipment_list(self) -> List[str]:
        """
        Obtiene la lista de equipos disponibles
        
        Returns:
            Lista de equipos
        """
        # Intentar obtener del caché
        cached_data = cache.get("metadata_equipment")
        if cached_data:
            return cached_data

        response = await self.api_client.get('/exercises/equipmentList')
        processed_data = await self._process_response(response, is_list_of_strings=True)

        # Guardar en caché
        cache.set("metadata_equipment", processed_data, self.cache_ttl)
        return processed_data

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
                instructions=e.instructions or "",
                difficulty=e.difficulty
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
                instructions=e.instructions or "",
                difficulty=e.difficulty
            ) for e in exercises
        ]

    async def get_exercises_by_user_and_day(self, user_id: int, day: str) -> List[ExerciseDatabaseResponse]:
        """Obtiene los ejercicios de un usuario para un día específico."""
        exercises = self.repository.get_by_user_and_day(user_id, day)
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
                instructions=e.instructions or "",
                difficulty=e.difficulty
            ) for e in exercises
        ]
        
    
    async def get_community_exercises(self, user_id: int) -> List[ExerciseDatabaseResponse]:
        """Obtiene los ejercicios de todos menos del usuario que realizo la peticion"""
        exercises = self.repository.get_except_user(user_id)
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
                instructions=e.instructions or "",
                difficulty=e.difficulty
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
            instructions=exercise.instructions,
            difficulty=exercise.difficulty
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
            instructions=created.instructions or "",
            difficulty=created.difficulty
        )

    async def update_exercise(self, exercise_id: int, exercise: ExerciseDatabaseUpdate) -> ExerciseDatabaseResponse:
        """Actualiza un ejercicio existente en la base de datos"""
        db_exercise = self.repository.get_by_id(exercise_id)
        if not db_exercise:
            raise ValueError(f"Ejercicio con id {exercise_id} no encontrado")
        
        if exercise.name is not None: db_exercise.name = exercise.name
        if exercise.description is not None: db_exercise.description = exercise.description
        if exercise.user_id is not None: db_exercise.user_id = exercise.user_id
        if exercise.scheduled_days is not None: db_exercise.scheduled_days = set(exercise.scheduled_days)
        if exercise.image_url is not None: db_exercise.image_url = exercise.image_url
        if exercise.bodyparts is not None: db_exercise.bodyparts = set(exercise.bodyparts)
        if exercise.equipments is not None: db_exercise.equipments = set(exercise.equipments)
        if exercise.targetMuscles is not None: db_exercise.targetMuscles = set(exercise.targetMuscles)
        if exercise.secondaryMuscles is not None: db_exercise.secondaryMuscles = set(exercise.secondaryMuscles)
        if exercise.exercise_type is not None: db_exercise.exercise_type = exercise.exercise_type
        if exercise.instructions is not None: db_exercise.instructions = exercise.instructions
        if exercise.difficulty is not None: db_exercise.difficulty = exercise.difficulty
        
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
            instructions=updated.instructions or "",
            difficulty=updated.difficulty
        )

    async def delete_exercise(self, exercise_id: int) -> dict:
        """Elimina un ejercicio de la base de datos"""
        db_exercise = self.repository.get_by_id(exercise_id)
        if not db_exercise:
            raise ValueError(f"Ejercicio con id {exercise_id} no encontrado")
        self.repository.delete(db_exercise)
        return {"message": f"Ejercicio con id {exercise_id} eliminado exitosamente"}
    
    async def get_exercises_from_db_by_bodypart(self, bodypart: str) -> List[ExerciseDatabaseResponse]:
        """Obtiene los ejercicios de un bodypart específico desde la base de datos"""
        exercises = self.repository.get_by_bodypart(bodypart)
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
                instructions=e.instructions or "",
                difficulty=e.difficulty
            ) for e in exercises
        ]
    
    async def get_exercises_from_db_by_target(self, target: str) -> List[ExerciseDatabaseResponse]:
        """Obtiene los ejercicios de un target específico desde la base de datos"""
        exercises = self.repository.get_by_target(target)
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
                instructions=e.instructions or "",
                difficulty=e.difficulty
            ) for e in exercises
        ]
    
    async def get_exercises_from_db_by_equipment(self, equipment: str) -> List[ExerciseDatabaseResponse]:
        """Obtiene los ejercicios de un equipment específico desde la base de datos"""
        exercises = self.repository.get_by_equipment(equipment)
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
                instructions=e.instructions or "",
                difficulty=e.difficulty
            ) for e in exercises
        ]
    
    async def get_exercises_from_db_by_difficulty(self, difficulty: str) -> List[ExerciseDatabaseResponse]:
        """Obtiene los ejercicios de una dificultad específica desde la base de datos"""
        exercises = self.repository.get_by_difficulty(difficulty)
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
                instructions=e.instructions or "",
                difficulty=e.difficulty
            ) for e in exercises
        ]
    
    async def get_exercises_from_db_by_type(self, exercise_type: str) -> List[ExerciseDatabaseResponse]:
        """Obtiene los ejercicios de un tipo específico desde la base de datos"""
        exercises = self.repository.get_by_type(exercise_type)
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
                instructions=e.instructions or "",
                difficulty=e.difficulty
            ) for e in exercises
        ]
    
    async def search_exercises_by_name(self, name: str) -> List[ExerciseDatabaseResponse]:
        """Busca ejercicios cuyo nombre contenga el texto proporcionado"""
        exercises = self.repository.search_by_name(name)
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
                instructions=e.instructions or "",
                difficulty=e.difficulty
            ) for e in exercises
        ]