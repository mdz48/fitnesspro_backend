"""
Schemas para la API de ejercicios (ExerciseDB)
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class ExerciseSchema(BaseModel):
    """Esquema de un ejercicio individual"""
    exerciseId: str = Field(..., description="ID único del ejercicio")
    name: str = Field(..., description="Nombre del ejercicio")
    imageUrl: str = Field(..., description="URL de imagen del ejercicio")
    bodyParts: List[str] = Field(default_factory=list, description="Partes del cuerpo involucradas")
    equipments: List[str] = Field(default_factory=list, description="Equipos necesarios")
    exerciseType: Optional[str] = Field(None, description="Tipo de ejercicio")
    targetMuscles: List[str] = Field(default_factory=list, description="Músculos principales trabajados")
    secondaryMuscles: List[str] = Field(default_factory=list, description="Músculos secundarios trabajados")
    keywords: List[str] = Field(default_factory=list, description="Palabras clave")
    instructions: List[str] = Field(default_factory=list, description="Instrucciones paso a paso")


class CursorMeta(BaseModel):
    """Metadata cursor-based del proveedor remoto"""
    total: int = Field(..., description="Total de ejercicios")
    hasNextPage: bool = Field(..., description="Si existe página siguiente")
    hasPreviousPage: bool = Field(..., description="Si existe página anterior")
    nextCursor: Optional[str] = Field(None, description="Cursor para la siguiente página")


class ExerciseListResponse(BaseModel):
    """Respuesta completa de la API para lista de ejercicios"""
    success: bool = Field(..., description="Indica si la petición fue exitosa")
    meta: CursorMeta = Field(..., description="Metadata cursor-based")
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
    exercise_type: Optional[str] = Field(default="FUERZA", description="Tipo de ejercicio")
    instructions: Optional[str] = Field(None, description="Instrucciones")
    difficulty: str = Field(..., description="Dificultad del ejercicio")

class ExerciseDatabaseUpdate(BaseModel):
    """Esquema para actualizar un ejercicio de nuestra base de datos"""
    id: int = Field(..., description="ID del ejercicio")
    name: Optional[str] = Field(None, description="Nombre del ejercicio")
    description: Optional[str] = Field(None, description="Descripción del ejercicio")
    user_id: Optional[int] = Field(None, description="ID del usuario")
    scheduled_days: Optional[List[str]] = Field(None, description="Días programados")
    image_url: Optional[str] = Field(None, description="URL de la imagen")
    bodyparts: Optional[List[str]] = Field(None, description="Partes del cuerpo")
    equipments: Optional[List[str]] = Field(None, description="Equipos")
    targetMuscles: Optional[List[str]] = Field(None, description="Músculos")
    secondaryMuscles: Optional[List[str]] = Field(None, description="Músculos secundarios")
    exercise_type: Optional[str] = Field(None, description="Tipo de ejercicio")
    instructions: Optional[str] = Field(None, description="Instrucciones")
    difficulty: Optional[str] = Field(None, description="Dificultad del ejercicio")

class ExerciseDatabaseResponse(ExerciseDatabaseCreate):
    """Esquema para la respuesta de un ejercicio de nuestra base de datos"""
    id: int = Field(..., description="ID del ejercicio")