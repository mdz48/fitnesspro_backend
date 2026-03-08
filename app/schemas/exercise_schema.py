"""
Schemas para la API de ejercicios (ExerciseDB)
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class ExerciseSchema(BaseModel):
    """Esquema de un ejercicio individual"""
    exerciseId: str = Field(..., description="ID único del ejercicio")
    name: str = Field(..., description="Nombre del ejercicio")
    gifUrl: str = Field(..., description="URL del GIF demostrativo")
    targetMuscles: List[str] = Field(..., description="Músculos principales trabajados")
    bodyParts: List[str] = Field(..., description="Partes del cuerpo involucradas")
    equipments: List[str] = Field(..., description="Equipos necesarios")
    secondaryMuscles: List[str] = Field(..., description="Músculos secundarios trabajados")
    instructions: List[str] = Field(..., description="Instrucciones paso a paso")


class PaginationMetadata(BaseModel):
    """Metadata de paginación"""
    totalExercises: int = Field(..., description="Total de ejercicios")
    totalPages: int = Field(..., description="Total de páginas")
    currentPage: int = Field(..., description="Página actual")
    previousPage: Optional[str] = Field(None, description="URL de la página anterior")
    nextPage: Optional[str] = Field(None, description="URL de la página siguiente")


class ExerciseListResponse(BaseModel):
    """Respuesta completa de la API para lista de ejercicios"""
    success: bool = Field(..., description="Indica si la petición fue exitosa")
    metadata: PaginationMetadata = Field(..., description="Metadata de paginación")
    data: List[ExerciseSchema] = Field(..., description="Lista de ejercicios")


class ExerciseDetailResponse(BaseModel):
    """Respuesta completa de la API para un ejercicio individual"""
    success: bool = Field(..., description="Indica si la petición fue exitosa")
    data: ExerciseSchema = Field(..., description="Datos del ejercicio")

class ExerciseDatabaseCreate(BaseModel):
    """Esquema para crear un nuevo ejercicio de nuestra base de datos"""
    name: str = Field(..., description="Nombre del ejercicio")
    description: str = Field(..., description="Descripción del ejercicio")
    user_id: int = Field(..., description="ID del usuario")
    scheduled_days: Optional[List[str]] = Field(default=[], description="Días programados")
    image_url: Optional[str] = Field(default="", description="URL de la imagen")
    bodyparts: Optional[List[str]] = Field(default=[], description="Partes del cuerpo")
    equipments: Optional[List[str]] = Field(default=[], description="Equipos")
    targetMuscles: Optional[List[str]] = Field(default=[], description="Músculos")
    secondaryMuscles: Optional[List[str]] = Field(default=[], description="Músculos secundarios")
    exercise_type: Optional[str] = Field(default=None, description="Tipo de ejercicio")
    instructions: Optional[str] = Field(default="", description="Instrucciones")

class ExerciseDatabaseUpdate(BaseModel):
    """Esquema para actualizar un ejercicio de nuestra base de datos"""
    id: int = Field(..., description="ID del ejercicio")
    name: str = Field(..., description="Nombre del ejercicio")
    description: str = Field(..., description="Descripción del ejercicio")
    user_id: int = Field(..., description="ID del usuario")
    scheduled_days: Optional[List[str]] = Field(default=[], description="Días programados")
    image_url: Optional[str] = Field(default="", description="URL de la imagen")
    bodyparts: Optional[List[str]] = Field(default=[], description="Partes del cuerpo")
    equipments: Optional[List[str]] = Field(default=[], description="Equipos")
    targetMuscles: Optional[List[str]] = Field(default=[], description="Músculos")
    secondaryMuscles: Optional[List[str]] = Field(default=[], description="Músculos secundarios")
    exercise_type: Optional[str] = Field(default=None, description="Tipo de ejercicio")
    instructions: Optional[str] = Field(default="", description="Instrucciones")

class ExerciseDatabaseResponse(BaseModel):
    """Esquema para la respuesta de un ejercicio de nuestra base de datos"""
    id: int = Field(..., description="ID del ejercicio")
    name: str = Field(..., description="Nombre del ejercicio")
    description: str = Field(..., description="Descripción del ejercicio")
    user_id: int = Field(..., description="ID del usuario")
    scheduled_days: Optional[List[str]] = Field(default=[], description="Días programados")
    image_url: Optional[str] = Field(default="", description="URL de la imagen")
    bodyparts: Optional[List[str]] = Field(default=[], description="Partes del cuerpo")
    equipments: Optional[List[str]] = Field(default=[], description="Equipos")
    targetMuscles: Optional[List[str]] = Field(default=[], description="Músculos")
    secondaryMuscles: Optional[List[str]] = Field(default=[], description="Músculos secundarios")
    exercise_type: Optional[str] = Field(default=None, description="Tipo de ejercicio")
    instructions: Optional[str] = Field(default="", description="Instrucciones")