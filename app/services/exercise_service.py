"""
Servicio para gestionar ejercicios de la API ExerciseDB y de la base de datos
"""
import unicodedata
from typing import List, Optional, Dict, Any, Type
from enum import Enum
from fastapi import HTTPException
from app.interfaces.api_client_interface import IAPIClient
from app.models.Exercise import Exercise
from app.models.Enums import BodyPartEnum, EquipmentEnum, MuscleEnum
from app.repositories.exercise_repository import ExerciseRepository
from app.schemas.exercise_schema import ExerciseDatabaseCreate, ExerciseDatabaseUpdate, ExerciseDatabaseResponse



from app.services.cache_service import cache
from app.services.translation_service import translation_service
from app.shared.config.external_api_config import CACHE_TTL

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
        self.cache_ttl = CACHE_TTL
        self.bodypart_map = self._build_spanish_to_english_map(BodyPartEnum)
        self.target_map = self._build_spanish_to_english_map(MuscleEnum)
        self.equipment_map = self._build_spanish_to_english_map(EquipmentEnum)

    def _remote_base_url(self) -> str:
        return getattr(self.api_client, "base_url", "")

    @staticmethod
    def _extract_remote_items(response: Any) -> List[Dict[str, Any]]:
        """Extrae ejercicios desde respuestas que vengan como lista o envoltorio."""
        if isinstance(response, list):
            return [item for item in response if isinstance(item, dict)]

        if isinstance(response, dict):
            data = response.get("data")
            if isinstance(data, list):
                return [item for item in data if isinstance(item, dict)]
            if isinstance(data, dict):
                return [data]
            if response.get("id") or response.get("exerciseId"):
                return [response]

        return []

    @staticmethod
    def _normalize_remote_exercise(exercise: Dict[str, Any]) -> Dict[str, Any]:
        """Normaliza item remoto al contrato exacto esperado por frontend."""
        normalized = dict(exercise)
        normalized["exerciseId"] = str(normalized.get("exerciseId") or normalized.get("id") or "")
        normalized["imageUrl"] = (
            normalized.get("imageUrl")
            or normalized.get("gifUrl")
            or ""
        )
        if not normalized.get("bodyParts") and normalized.get("bodyPart"):
            normalized["bodyParts"] = [normalized.get("bodyPart")]
        if not normalized.get("equipments") and normalized.get("equipment"):
            normalized["equipments"] = [normalized.get("equipment")]
        if not normalized.get("targetMuscles") and normalized.get("target"):
            normalized["targetMuscles"] = [normalized.get("target")]
        normalized.setdefault("bodyParts", [])
        normalized.setdefault("equipments", [])
        normalized.setdefault("targetMuscles", [])
        normalized.setdefault("secondaryMuscles", [])
        normalized.setdefault("keywords", [])
        normalized.setdefault("instructions", [])
        return normalized

    def _coerce_remote_list_response(self, response: Any) -> Dict[str, Any]:
        """Asegura respuesta success/meta/data aun si el proveedor cambia formato."""
        if isinstance(response, dict) and isinstance(response.get("data"), list):
            meta = response.get("meta") if isinstance(response.get("meta"), dict) else {}
            return {
                "success": bool(response.get("success", True)),
                "meta": {
                    "total": int(meta.get("total", len(response.get("data", [])))),
                    "hasNextPage": bool(meta.get("hasNextPage", False)),
                    "hasPreviousPage": bool(meta.get("hasPreviousPage", False)),
                    "nextCursor": meta.get("nextCursor"),
                },
                "data": [self._normalize_remote_exercise(item) for item in response.get("data", [])],
            }

        if isinstance(response, list):
            normalized_data = [self._normalize_remote_exercise(item) for item in response if isinstance(item, dict)]
            return {
                "success": True,
                "meta": {
                    "total": len(normalized_data),
                    "hasNextPage": False,
                    "hasPreviousPage": False,
                    "nextCursor": None,
                },
                "data": normalized_data,
            }

        return {
            "success": False,
            "meta": {
                "total": 0,
                "hasNextPage": False,
                "hasPreviousPage": False,
                "nextCursor": None,
            },
            "data": [],
        }

    def _coerce_remote_detail_response(self, response: Any) -> Dict[str, Any]:
        """Asegura respuesta success/data para detalle remoto."""
        if isinstance(response, dict) and isinstance(response.get("data"), dict):
            return {
                "success": bool(response.get("success", True)),
                "data": self._normalize_remote_exercise(response.get("data", {})),
            }
        if isinstance(response, dict) and (response.get("exerciseId") or response.get("id")):
            return {
                "success": True,
                "data": self._normalize_remote_exercise(response),
            }
        return {
            "success": False,
            "data": None,
        }

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

    @staticmethod
    def _field_matches(item: Dict[str, Any], field_name: str, expected_value: str) -> bool:
        """Comprueba si un campo normalizado contiene el valor esperado."""
        normalized_expected = ExerciseService._normalize_filter_value(expected_value)
        field_value = item.get(field_name, [])

        if isinstance(field_value, str):
            field_values = [field_value]
        elif isinstance(field_value, list):
            field_values = field_value
        else:
            field_values = []

        return any(
            ExerciseService._normalize_filter_value(str(value)) == normalized_expected
            for value in field_values
            if value is not None
        )

    @staticmethod
    def _search_matches(item: Dict[str, Any], query: str) -> bool:
        """Evalua coincidencia por nombre para búsquedas remotas."""
        normalized_query = ExerciseService._normalize_filter_value(query)
        normalized_name = ExerciseService._normalize_filter_value(str(item.get("name", "")))
        return normalized_query in normalized_name

    @staticmethod
    def _paginate_catalog(
        items: List[Dict[str, Any]],
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        after: Optional[str] = None,
        before: Optional[str] = None,
    ) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Aplica paginación local manteniendo la misma metadata pública."""
        total = len(items)
        start_index = 0
        end_index = total

        if after:
            cursor_index = next(
                (index for index, item in enumerate(items) if str(item.get("exerciseId")) == str(after)),
                None,
            )
            if cursor_index is not None:
                start_index = cursor_index + 1
        elif before:
            cursor_index = next(
                (index for index, item in enumerate(items) if str(item.get("exerciseId")) == str(before)),
                None,
            )
            if cursor_index is not None:
                end_index = cursor_index
                if limit is not None:
                    start_index = max(0, end_index - limit)
        elif offset is not None:
            start_index = max(0, offset)

        if limit is not None and not before:
            end_index = min(end_index, start_index + limit)

        start_index = min(start_index, total)
        end_index = min(max(end_index, start_index), total)

        page = items[start_index:end_index]
        meta = {
            "total": total,
            "hasNextPage": end_index < total,
            "hasPreviousPage": start_index > 0,
            "nextCursor": page[-1].get("exerciseId") if page and end_index < total else None,
        }
        return page, meta

    async def _get_remote_catalog(self) -> List[Dict[str, Any]]:
        """Obtiene y cachea el catálogo remoto normalizado de ejercicios."""
        cached_data = cache.get("exercise_remote_catalog", base_url=self._remote_base_url())
        if cached_data is not None:
            return cached_data

        response = await self.api_client.get("/exercises")
        catalog = [self._normalize_remote_exercise(item) for item in self._extract_remote_items(response)]
        cache.set("exercise_remote_catalog", catalog, self.cache_ttl, base_url=self._remote_base_url())
        return catalog

    @staticmethod
    def _build_list_response(items: List[Dict[str, Any]], total: Optional[int] = None) -> Dict[str, Any]:
        """Construye la respuesta pública esperada por el frontend."""
        resolved_total = total if total is not None else len(items)
        return {
            "success": True,
            "meta": {
                "total": resolved_total,
                "hasNextPage": False,
                "hasPreviousPage": False,
                "nextCursor": items[-1].get("exerciseId") if items else None,
            },
            "data": items,
        }

    @staticmethod
    def _collect_unique_values(items: List[Dict[str, Any]], field_name: str) -> List[str]:
        """Recopila valores únicos conservando el orden original."""
        seen: set[str] = set()
        result: List[str] = []

        for item in items:
            field_value = item.get(field_name, [])
            if isinstance(field_value, str):
                values = [field_value]
            elif isinstance(field_value, list):
                values = field_value
            else:
                values = []

            for value in values:
                normalized_value = " ".join(str(value).split()).strip()
                normalized_key = ExerciseService._normalize_filter_value(normalized_value)
                if normalized_value and normalized_key not in seen:
                    seen.add(normalized_key)
                    result.append(normalized_value)

        return result

    @staticmethod
    async def _translate_remote_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Traduce una lista de ejercicios remotos sin alterar su estructura."""
        translated_items = await translation_service.translate_exercise_data(items)
        if isinstance(translated_items, list):
            return translated_items
        return items

    @staticmethod
    async def _translate_remote_strings(values: List[str]) -> List[str]:
        """Traduce una lista de textos simples del proveedor remoto."""
        translated_values = await translation_service.translate_list(values)
        return translated_values if translated_values else values

    async def get_all_exercises(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        after: Optional[str] = None,
        before: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Obtiene todos los ejercicios
        
        Args:
            limit: Número máximo de resultados
            offset: Compatibilidad legacy (no recomendado)
            after: Cursor siguiente página
            before: Cursor página anterior
            
        Returns:
            Lista de ejercicios
        """
        def _to_non_negative_int(value: Any) -> Optional[int]:
            try:
                parsed = int(str(value))
                return parsed if parsed >= 0 else None
            except (TypeError, ValueError):
                return None

        effective_limit = limit or 10
        effective_offset = offset if offset is not None else 0

        # Compatibilidad de cursor: si `after` o `before` llegan como número,
        # se interpretan como offset para el proveedor remoto.
        after_offset = _to_non_negative_int(after)
        before_offset = _to_non_negative_int(before)
        if after_offset is not None:
            effective_offset = after_offset
        elif before_offset is not None:
            effective_offset = before_offset

        cached_data = cache.get(
            "exercises",
            limit=effective_limit,
            offset=effective_offset,
            after=after,
            before=before,
            base_url=self._remote_base_url(),
        )
        if cached_data is not None:
            return cached_data

        params: Dict[str, Any] = {
            "limit": effective_limit,
            "offset": effective_offset,
        }

        response = await self.api_client.get("/exercises", params=params)
        processed_data = self._coerce_remote_list_response(response)
        translated_page = await self._translate_remote_items(processed_data.get("data", []))

        raw_meta = processed_data.get("meta", {}) if isinstance(processed_data.get("meta"), dict) else {}
        provider_meta = response.get("meta") if isinstance(response, dict) and isinstance(response.get("meta"), dict) else {}
        provider_has_next = provider_meta.get("hasNextPage") if "hasNextPage" in provider_meta else None
        inferred_has_next = (
            bool(provider_has_next)
            if provider_has_next is not None
            else len(translated_page) >= effective_limit
        )
        provider_has_previous = provider_meta.get("hasPreviousPage") if "hasPreviousPage" in provider_meta else None
        inferred_has_previous = (
            bool(provider_has_previous)
            if provider_has_previous is not None
            else effective_offset > 0
        )
        next_cursor = provider_meta.get("nextCursor") if "nextCursor" in provider_meta else None
        if not next_cursor and inferred_has_next:
            next_cursor = str(effective_offset + len(translated_page))

        total_from_provider = raw_meta.get("total")
        if total_from_provider is None:
            resolved_total = effective_offset + len(translated_page) + (1 if inferred_has_next else 0)
        else:
            resolved_total = int(total_from_provider)

        meta = {
            "total": resolved_total,
            "hasNextPage": inferred_has_next,
            "hasPreviousPage": inferred_has_previous,
            "nextCursor": next_cursor,
        }

        processed_data = {
            "success": bool(processed_data.get("success", True)),
            "meta": meta,
            "data": translated_page,
        }
        cache.set(
            "exercises",
            processed_data,
            self.cache_ttl,
            limit=effective_limit,
            offset=effective_offset,
            after=after,
            before=before,
            base_url=self._remote_base_url(),
        )
        return processed_data
    
    async def get_exercise_by_id(self, exercise_id: str) -> Dict[str, Any]:
        """
        Obtiene un ejercicio por su ID
        
        Args:
            exercise_id: ID del ejercicio
            
        Returns:
            Datos del ejercicio
        """
        cached_data = cache.get("exercise_detail", id=exercise_id, base_url=self._remote_base_url())
        if cached_data is not None:
            return cached_data

        catalog = await self._get_remote_catalog()
        matching_exercise = next(
            (
                exercise
                for exercise in catalog
                if str(exercise.get("exerciseId")) == str(exercise_id)
            ),
            None,
        )
        if not matching_exercise:
            raise HTTPException(
                status_code=404,
                detail={"code": "EXERCISE_NOT_FOUND", "message": "Ejercicio no encontrado"},
            )

        translated_exercise = await self._translate_remote_items([matching_exercise])
        exercise_data = translated_exercise[0] if translated_exercise else matching_exercise
        processed_data = {
            "success": True,
            "data": exercise_data,
        }

        cache.set("exercise_detail", processed_data, self.cache_ttl, id=exercise_id, base_url=self._remote_base_url())
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
        cached_data = cache.get("exercises_bodypart", bodypart=bodypart, mapped_bodypart=mapped_bodypart, base_url=self._remote_base_url())
        if cached_data is not None:
            return cached_data

        catalog = await self._get_remote_catalog()
        filtered_items = [item for item in catalog if self._field_matches(item, "bodyParts", mapped_bodypart)]
        translated_items = await self._translate_remote_items(filtered_items)
        processed_data = self._build_list_response(translated_items, total=len(translated_items))
        cache.set("exercises_bodypart", processed_data, self.cache_ttl, bodypart=bodypart, mapped_bodypart=mapped_bodypart, base_url=self._remote_base_url())
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
        cached_data = cache.get("exercises_target", target=target, mapped_target=mapped_target, base_url=self._remote_base_url())
        if cached_data is not None:
            return cached_data

        catalog = await self._get_remote_catalog()
        filtered_items = [item for item in catalog if self._field_matches(item, "targetMuscles", mapped_target)]
        translated_items = await self._translate_remote_items(filtered_items)
        processed_data = self._build_list_response(translated_items, total=len(translated_items))
        cache.set("exercises_target", processed_data, self.cache_ttl, target=target, mapped_target=mapped_target, base_url=self._remote_base_url())
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
        cached_data = cache.get("exercises_equipment", equipment=equipment, mapped_equipment=mapped_equipment, base_url=self._remote_base_url())
        if cached_data is not None:
            return cached_data

        catalog = await self._get_remote_catalog()
        filtered_items = [item for item in catalog if self._field_matches(item, "equipments", mapped_equipment)]
        translated_items = await self._translate_remote_items(filtered_items)
        processed_data = self._build_list_response(translated_items, total=len(translated_items))
        cache.set("exercises_equipment", processed_data, self.cache_ttl, equipment=equipment, mapped_equipment=mapped_equipment, base_url=self._remote_base_url())
        return processed_data
    
    async def get_body_parts(self) -> List[str]:
        """
        Obtiene la lista de partes del cuerpo disponibles
        
        Returns:
            Lista de partes del cuerpo
        """
        cached_data = cache.get("metadata_bodyparts", base_url=self._remote_base_url())
        if cached_data is not None:
            return cached_data

        catalog = await self._get_remote_catalog()
        processed_data = await self._translate_remote_strings(self._collect_unique_values(catalog, "bodyParts"))

        cache.set("metadata_bodyparts", processed_data, self.cache_ttl, base_url=self._remote_base_url())
        return processed_data
    
    async def get_target_muscles(self) -> List[str]:
        """
        Obtiene la lista de músculos objetivo disponibles
        
        Returns:
            Lista de músculos
        """
        cached_data = cache.get("metadata_targets", base_url=self._remote_base_url())
        if cached_data is not None:
            return cached_data

        catalog = await self._get_remote_catalog()
        processed_data = await self._translate_remote_strings(self._collect_unique_values(catalog, "targetMuscles"))

        cache.set("metadata_targets", processed_data, self.cache_ttl, base_url=self._remote_base_url())
        return processed_data
    
    async def get_equipment_list(self) -> List[str]:
        """
        Obtiene la lista de equipos disponibles
        
        Returns:
            Lista de equipos
        """
        cached_data = cache.get("metadata_equipment", base_url=self._remote_base_url())
        if cached_data is not None:
            return cached_data

        catalog = await self._get_remote_catalog()
        processed_data = await self._translate_remote_strings(self._collect_unique_values(catalog, "equipments"))

        cache.set("metadata_equipment", processed_data, self.cache_ttl, base_url=self._remote_base_url())
        return processed_data

    async def search_remote_exercises_by_name(self, name: str) -> Dict[str, Any]:
        """Busca ejercicios remotos por nombre en el proveedor nuevo."""
        cached_data = cache.get("exercises_remote_search", name=name, base_url=self._remote_base_url())
        if cached_data is not None:
            return cached_data

        catalog = await self._get_remote_catalog()
        filtered_items = [item for item in catalog if self._search_matches(item, name)]
        translated_items = await self._translate_remote_items(filtered_items)
        processed_data = self._build_list_response(translated_items, total=len(translated_items))
        cache.set("exercises_remote_search", processed_data, self.cache_ttl, name=name, base_url=self._remote_base_url())
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