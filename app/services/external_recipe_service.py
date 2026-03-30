"""Servicio para recetas externas con caché y traducción."""

import asyncio
from typing import Any, Dict, List, Optional, Tuple
from fastapi import HTTPException

from app.interfaces.api_client_interface import IAPIClient
from app.schemas.external_recipe_schema import ExternalRecipeResponse
from app.services.cache_service import cache
from app.services.translation_service import translation_service
from app.shared.config.external_api_config import CACHE_TTL


class ExternalRecipeService:
    """Gestiona consultas a recetas externas con caché y traducción al español."""

    def __init__(self, api_client: IAPIClient):
        """Inicializa el servicio con cliente API externo."""
        self.api_client = api_client
        self.cache_ttl = CACHE_TTL

    @staticmethod
    def _extract_ingredients_and_measures(raw_recipe: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """Extrae ingredientes y medidas del formato dinámico del proveedor."""
        ingredients: List[str] = []
        measures: List[str] = []

        for index in range(1, 21):
            ingredient = str(raw_recipe.get(f"strIngredient{index}", "")).strip()
            measure = str(raw_recipe.get(f"strMeasure{index}", "")).strip()

            if ingredient:
                ingredients.append(ingredient)
                measures.append(measure)

        return ingredients, measures

    @staticmethod
    def _parse_tags(raw_tags: Optional[str]) -> List[str]:
        """Convierte el string de tags del proveedor a lista."""
        if not raw_tags:
            return []
        return [tag.strip() for tag in raw_tags.split(",") if tag and tag.strip()]

    def _normalize_recipe(self, raw_recipe: Dict[str, Any]) -> ExternalRecipeResponse:
        """Normaliza el payload de receta externa al esquema interno."""
        ingredients, measures = self._extract_ingredients_and_measures(raw_recipe)
        return ExternalRecipeResponse(
            id=str(raw_recipe.get("idMeal", "")),
            name=str(raw_recipe.get("strMeal", "")),
            category=raw_recipe.get("strCategory"),
            area=raw_recipe.get("strArea"),
            instructions=raw_recipe.get("strInstructions"),
            image_url=raw_recipe.get("strMealThumb"),
            youtube_url=raw_recipe.get("strYoutube"),
            source_url=raw_recipe.get("strSource"),
            tags=self._parse_tags(raw_recipe.get("strTags")),
            ingredients=ingredients,
            measures=measures,
        )

    async def _translate_recipe(self, recipe: ExternalRecipeResponse) -> ExternalRecipeResponse:
        """Traduce campos relevantes de receta al español."""
        texts_to_translate: List[str] = []
        text_positions: Dict[str, Tuple[int, int]] = {}

        if recipe.name:
            text_positions["name"] = (len(texts_to_translate), len(texts_to_translate) + 1)
            texts_to_translate.append(recipe.name)

        if recipe.category:
            text_positions["category"] = (len(texts_to_translate), len(texts_to_translate) + 1)
            texts_to_translate.append(recipe.category)

        if recipe.area:
            text_positions["area"] = (len(texts_to_translate), len(texts_to_translate) + 1)
            texts_to_translate.append(recipe.area)

        if recipe.instructions:
            text_positions["instructions"] = (len(texts_to_translate), len(texts_to_translate) + 1)
            texts_to_translate.append(recipe.instructions)

        if recipe.tags:
            text_positions["tags"] = (len(texts_to_translate), len(texts_to_translate) + len(recipe.tags))
            texts_to_translate.extend(recipe.tags)

        if recipe.ingredients:
            text_positions["ingredients"] = (
                len(texts_to_translate),
                len(texts_to_translate) + len(recipe.ingredients)
            )
            texts_to_translate.extend(recipe.ingredients)

        if recipe.measures:
            text_positions["measures"] = (
                len(texts_to_translate),
                len(texts_to_translate) + len(recipe.measures)
            )
            texts_to_translate.extend(recipe.measures)

        if not texts_to_translate:
            return recipe

        translated_texts = await translation_service.translate_list(texts_to_translate)

        if "name" in text_positions:
            start, _ = text_positions["name"]
            recipe.name = translated_texts[start]

        if "category" in text_positions:
            start, _ = text_positions["category"]
            recipe.category = translated_texts[start]

        if "area" in text_positions:
            start, _ = text_positions["area"]
            recipe.area = translated_texts[start]

        if "instructions" in text_positions:
            start, _ = text_positions["instructions"]
            recipe.instructions = translated_texts[start]

        if "tags" in text_positions:
            start, end = text_positions["tags"]
            recipe.tags = translated_texts[start:end]

        if "ingredients" in text_positions:
            start, end = text_positions["ingredients"]
            recipe.ingredients = translated_texts[start:end]

        if "measures" in text_positions:
            start, end = text_positions["measures"]
            recipe.measures = translated_texts[start:end]

        return recipe

    async def search_recipes(self, name: str) -> List[ExternalRecipeResponse]:
        """Busca recetas por nombre en el proveedor externo."""
        normalized_name = (name or "").strip().lower()
        cached_data = cache.get("external_recipe_search", name=normalized_name)
        if cached_data is not None:
            return [ExternalRecipeResponse(**item) for item in cached_data]

        response = await self.api_client.get("/search.php", params={"s": normalized_name})
        meals = response.get("meals") if isinstance(response, dict) else None
        if not meals:
            cache.set("external_recipe_search", [], self.cache_ttl, name=normalized_name)
            return []

        translated_recipes: List[ExternalRecipeResponse] = []
        for meal in meals:
            normalized_recipe = self._normalize_recipe(meal)
            translated_recipe = await self._translate_recipe(normalized_recipe)
            translated_recipes.append(translated_recipe)

        cache.set(
            "external_recipe_search",
            [recipe.model_dump() for recipe in translated_recipes],
            self.cache_ttl,
            name=normalized_name
        )
        return translated_recipes

    async def get_recipe_by_id(self, recipe_id: str) -> ExternalRecipeResponse:
        """Obtiene una receta externa por ID."""
        normalized_id = str(recipe_id).strip()
        cached_data = cache.get("external_recipe_detail", id=normalized_id)
        if cached_data is not None:
            return ExternalRecipeResponse(**cached_data)

        response = await self.api_client.get("/lookup.php", params={"i": normalized_id})
        meals = response.get("meals") if isinstance(response, dict) else None
        if not meals:
            raise HTTPException(status_code=404, detail="Recipe not found in external provider")

        normalized_recipe = self._normalize_recipe(meals[0])
        translated_recipe = await self._translate_recipe(normalized_recipe)

        cache.set(
            "external_recipe_detail",
            translated_recipe.model_dump(),
            self.cache_ttl,
            id=normalized_id
        )
        return translated_recipe

    async def get_random_recipe(self) -> ExternalRecipeResponse:
        """Obtiene una receta aleatoria desde el proveedor externo."""
        response = await self.api_client.get("/random.php", use_cache=False)
        meals = response.get("meals") if isinstance(response, dict) else None
        if not meals:
            raise HTTPException(status_code=404, detail="No random recipes available")

        normalized_recipe = self._normalize_recipe(meals[0])
        return await self._translate_recipe(normalized_recipe)

    async def get_random_recipes(self, count: int) -> List[ExternalRecipeResponse]:
        """Obtiene múltiples recetas aleatorias traducidas y cacheadas."""
        safe_count = max(1, min(count, 20))
        cached_data = cache.get("external_recipe_random_list", count=safe_count)
        if cached_data is not None:
            return [ExternalRecipeResponse(**item) for item in cached_data]

        tasks = [self.api_client.get("/random.php", use_cache=False) for _ in range(safe_count)]
        responses = await asyncio.gather(*tasks)

        translated_recipes: List[ExternalRecipeResponse] = []
        for response in responses:
            meals = response.get("meals") if isinstance(response, dict) else None
            if not meals:
                continue

            normalized_recipe = self._normalize_recipe(meals[0])
            translated_recipe = await self._translate_recipe(normalized_recipe)
            translated_recipes.append(translated_recipe)

        if not translated_recipes:
            raise HTTPException(status_code=404, detail="No random recipes available")

        cache.set(
            "external_recipe_random_list",
            [recipe.model_dump() for recipe in translated_recipes],
            600,
            count=safe_count
        )
        return translated_recipes
