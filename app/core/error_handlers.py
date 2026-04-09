"""Manejadores de errores globales para FastAPI."""
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


def register_error_handlers(app: FastAPI) -> None:
	"""Registra manejadores globales de errores para la aplicación."""

	@app.exception_handler(RequestValidationError)
	async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
		body_preview = ""
		try:
			raw_body = await request.body()
			if raw_body:
				body_preview = raw_body.decode("utf-8", errors="ignore")[:1000]
		except Exception:
			body_preview = "<unavailable>"

		logger.warning(
			"Request validation error: method=%s path=%s query=%s errors=%s body=%s",
			request.method,
			request.url.path,
			request.url.query,
			exc.errors(),
			body_preview,
		)

		return JSONResponse(
			status_code=422,
			content={
				"detail": exc.errors(),
			},
		)
