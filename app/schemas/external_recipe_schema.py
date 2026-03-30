"""Schemas para recetas provenientes de API externa."""

from typing import List, Optional
from pydantic import BaseModel, Field


class ExternalRecipeResponse(BaseModel):
    """Esquema normalizado de una receta externa."""

    id: str = Field(..., description="ID único de la receta en el proveedor externo")
    name: str = Field(..., description="Nombre de la receta")
    category: Optional[str] = Field(None, description="Categoría de la receta")
    area: Optional[str] = Field(None, description="Región o cocina de origen")
    instructions: Optional[str] = Field(None, description="Instrucciones de preparación")
    image_url: Optional[str] = Field(None, description="URL de imagen")
    youtube_url: Optional[str] = Field(None, description="URL de video de apoyo")
    source_url: Optional[str] = Field(None, description="URL fuente original")
    tags: List[str] = Field(default_factory=list, description="Etiquetas asociadas")
    ingredients: List[str] = Field(default_factory=list, description="Ingredientes")
    measures: List[str] = Field(default_factory=list, description="Medidas por ingrediente")


class ExternalRecipeListResponse(BaseModel):
    """Respuesta de búsqueda de recetas externas."""

    recipes: List[ExternalRecipeResponse] = Field(
        default_factory=list,
        description="Listado de recetas encontradas"
    )
