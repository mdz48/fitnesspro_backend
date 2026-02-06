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
