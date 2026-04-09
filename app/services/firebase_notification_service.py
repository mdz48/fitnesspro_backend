"""Servicio para Firebase Cloud Messaging."""
import base64
import json
import logging
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from app.repositories.user_fcm_token_repository import UserFcmTokenRepository

logger = logging.getLogger(__name__)

load_dotenv()


class FirebaseNotificationService:
    """Envía notificaciones push con FCM y administra la inicialización del SDK."""

    def __init__(self, token_repository: UserFcmTokenRepository):
        self.token_repository = token_repository
        self._app = None
        self._init_error: str | None = None

    def _candidate_credential_paths(self) -> list[Path]:
        project_root = Path(__file__).resolve().parents[2]
        return [
            project_root / "firebasecredencials.json",
            project_root / "firebase_credentials.json",
            project_root / "firebase-credentials.json",
        ]

    def _load_service_account(self) -> dict[str, Any] | None:
        credentials_json = os.getenv("FIREBASE_CREDENTIALS_JSON")
        credentials_base64 = os.getenv("FIREBASE_CREDENTIALS_BASE64")
        credentials_path = os.getenv("FIREBASE_CREDENTIALS_PATH")

        if credentials_json:
            return json.loads(credentials_json)

        if credentials_base64:
            decoded_json = base64.b64decode(credentials_base64).decode("utf-8")
            return json.loads(decoded_json)

        if credentials_path:
            path = Path(credentials_path)
            if path.exists():
                with path.open("r", encoding="utf-8") as file_handle:
                    return json.load(file_handle)

        for candidate_path in self._candidate_credential_paths():
            if candidate_path.exists():
                logger.info("Usando archivo de credenciales Firebase detectado automáticamente: %s", candidate_path.name)
                with candidate_path.open("r", encoding="utf-8") as file_handle:
                    return json.load(file_handle)

        return None

    def _ensure_initialized(self) -> bool:
        if self._app is not None:
            return True

        try:
            import firebase_admin
            from firebase_admin import credentials
        except ImportError:
            self._init_error = "firebase_admin_not_installed"
            logger.warning("Firebase Admin SDK no está instalado; se omitirán notificaciones push")
            return False

        try:
            service_account = self._load_service_account()
            if not service_account:
                self._init_error = "firebase_credentials_missing"
                logger.warning(
                    "Firebase no configurado: define FIREBASE_CREDENTIALS_PATH, FIREBASE_CREDENTIALS_JSON o FIREBASE_CREDENTIALS_BASE64"
                )
                return False

            cred = credentials.Certificate(service_account)
            self._app = firebase_admin.initialize_app(cred)
            self._init_error = None
            logger.info("Firebase Admin SDK inicializado correctamente")
            return True
        except ValueError as exc:
            self._init_error = str(exc)
            logger.exception("Firebase Admin SDK ya estaba inicializado o falló la configuración")
            return False
        except Exception as exc:
            self._init_error = str(exc)
            logger.exception("No fue posible inicializar Firebase Admin SDK")
            return False

    def send_payment_success(self, user_id: int, subscription_id: int) -> dict[str, Any]:
        """Envía la notificación de pago confirmado a todos los tokens activos del usuario."""
        tokens = self.token_repository.get_by_user_id(user_id)
        if not tokens:
            logger.info("No hay tokens FCM activos para user_id=%s", user_id)
            return {"status": "skipped", "reason": "no_tokens", "sent": 0}

        if not self._ensure_initialized():
            return {
                "status": "skipped",
                "reason": self._init_error or "firebase_not_ready",
                "sent": 0,
                "tokens": len(tokens),
            }

        try:
            from firebase_admin import messaging
        except ImportError:
            return {"status": "skipped", "reason": "firebase_admin_not_installed", "sent": 0}

        data_payload = {
            "type": "PAYMENT_SUCCESS",
            "subscription_id": str(subscription_id),
        }
        notification = messaging.Notification(
            title="¡Pago Confirmado!",
            body="Tu suscripción Premium ya está activa.",
        )
        android = messaging.AndroidConfig(priority="high")

        sent = 0
        failed = 0
        failures: list[dict[str, str]] = []

        for token_record in tokens:
            message = messaging.Message(
                token=token_record.fcm_token,
                data=data_payload,
                notification=notification,
                android=android,
            )
            try:
                messaging.send(message)
                sent += 1
            except Exception as exc:
                failed += 1
                failures.append({"token_id": str(token_record.id), "error": str(exc)})
                logger.warning(
                    "Error enviando FCM a user_id=%s token_id=%s: %s",
                    user_id,
                    token_record.id,
                    exc,
                )

        logger.info(
            "Notificación PAYMENT_SUCCESS procesada para user_id=%s subscription_id=%s sent=%s failed=%s",
            user_id,
            subscription_id,
            sent,
            failed,
        )
        return {
            "status": "processed",
            "user_id": user_id,
            "subscription_id": subscription_id,
            "sent": sent,
            "failed": failed,
            "failures": failures,
        }