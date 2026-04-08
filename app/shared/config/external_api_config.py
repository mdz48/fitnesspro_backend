"""Configuracion para APIs externas (ExerciseDB y MealDB)."""

import os
from dotenv import load_dotenv

load_dotenv()

_DEFAULT_EXERCISEDB_BASE_URL = "https://exercisedb.p.rapidapi.com"
_DEFAULT_RAPIDAPI_HOST = "exercisedb.p.rapidapi.com"


def _resolve_exercisedb_base_url() -> str:
	configured = os.getenv("EXERCISEDB_BASE_URL")
	if not configured:
		return _DEFAULT_EXERCISEDB_BASE_URL
	return configured


def _resolve_rapidapi_host() -> str:
	configured = os.getenv("RAPIDAPI_HOST")
	if not configured:
		return _DEFAULT_RAPIDAPI_HOST
	return configured


EXERCISEDB_BASE_URL = _resolve_exercisedb_base_url()
MEALDB_BASE_URL = os.getenv("MEALDB_BASE_URL", "https://www.themealdb.com/api/json/v1/1")

RAPIDAPI_HOST = _resolve_rapidapi_host()
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "10"))
CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))


def get_exercisedb_headers() -> dict[str, str]:
    """Devuelve headers requeridos por RapidAPI para ExerciseDB."""
    headers = {
        "x-rapidapi-host": RAPIDAPI_HOST
    }
    if RAPIDAPI_KEY:
        headers["x-rapidapi-key"] = RAPIDAPI_KEY
    return headers
