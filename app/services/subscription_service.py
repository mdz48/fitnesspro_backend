"""
Servicio para gestionar suscripciones de usuarios con Mercado Pago
"""
import logging
import json
import hmac
import hashlib
from datetime import datetime, timedelta
from fastapi import HTTPException
from app.shared.config.mercado_pago import MercadoPagoConfig
from app.repositories.subscription_plan_repository import SubscriptionPlanRepository
from app.repositories.user_subscription_repository import UserSubscriptionRepository
from app.repositories.subscription_payment_repository import SubscriptionPaymentRepository
from app.repositories.user_repository import UserRepository
from app.services.firebase_notification_service import FirebaseNotificationService
from app.models.UserSubscription import UserSubscription
from app.models.SubscriptionPayment import SubscriptionPayment

logger = logging.getLogger(__name__)


class SubscriptionService:
    """Servicio para gestionar suscripciones de usuarios con Mercado Pago"""
    
    def __init__(
        self,
        subscription_repo: UserSubscriptionRepository,
        payment_repo: SubscriptionPaymentRepository,
        plan_repo: SubscriptionPlanRepository,
        user_repo: UserRepository,
        mp_config: MercadoPagoConfig,
        notification_service: FirebaseNotificationService | None = None,
    ):
        self.subscription_repo = subscription_repo
        self.payment_repo = payment_repo
        self.plan_repo = plan_repo
        self.user_repo = user_repo
        self.mp_config = mp_config
        self.mp_client = mp_config.get_client()
        self.notification_service = notification_service

    def _send_payment_success_notification(self, subscription: UserSubscription) -> None:
        """Envía una notificación de pago aprobado sin interrumpir el webhook."""
        if not self.notification_service:
            return

        try:
            result = self.notification_service.send_payment_success(subscription.user_id, subscription.id)
            logger.info(
                "FCM payment success notification result: user_id=%s subscription_id=%s result=%s",
                subscription.user_id,
                subscription.id,
                result,
            )
        except Exception as exc:
            logger.warning(
                "Failed to send FCM payment success notification for user_id=%s subscription_id=%s: %s",
                subscription.user_id,
                subscription.id,
                exc,
            )

    @staticmethod
    def _summarize_mp_response(response: dict | None) -> dict:
        """Resume una respuesta de Mercado Pago para logs sin exponer el payload completo."""
        if not isinstance(response, dict):
            return {"type": type(response).__name__}

        response_data = response.get("response", {})
        summary: dict = {
            "status": response.get("status"),
            "response_keys": sorted(response_data.keys()) if isinstance(response_data, dict) else [],
        }

        if isinstance(response_data, dict):
            summary["message"] = response_data.get("message")
            summary["error"] = response_data.get("error")
            summary["cause"] = response_data.get("cause")
            summary["id_present"] = bool(response_data.get("id"))

        return summary
    
    def create_subscription(
        self,
        user_id: int,
        plan_id: int,
        card_token_id: str | None = None,
        back_url: str | None = None,
        notification_url: str | None = None
    ) -> dict:
        """
        Crea una suscripción para un usuario basada en un plan.
        
        Args:
            user_id: ID del usuario
            plan_id: ID del plan de suscripción
            card_token_id: Token de tarjeta para pago autorizado (opcional)
            back_url: URL de retorno (opcional, usa la del plan si no se especifica)
            
        Returns:
            Diccionario con datos de la suscripción e init_point
            
        Raises:
            HTTPException: Si hay error en la creación
        """
        logger.info(
            "Subscription create requested: user_id=%s plan_id=%s has_card_token=%s has_back_url=%s has_notification_url=%s",
            user_id,
            plan_id,
            bool(card_token_id),
            bool(back_url),
            bool(notification_url),
        )

        # Verificar usuario
        user = self.user_repo.get_by_id(user_id)
        if not user:
            logger.warning(
                "Subscription creation rejected: user not found (user_id=%s, plan_id=%s)",
                user_id,
                plan_id,
            )
            raise HTTPException(
                status_code=404,
                detail={"code": "USER_NOT_FOUND", "message": "Usuario no encontrado"}
            )
        
        # Verificar plan
        plan = self.plan_repo.get_by_id(plan_id)
        if not plan:
            logger.warning(
                "Subscription creation rejected: plan not found (user_id=%s, plan_id=%s)",
                user_id,
                plan_id,
            )
            raise HTTPException(
                status_code=404,
                detail={"code": "PLAN_NOT_FOUND", "message": "Plan de suscripción no encontrado"}
            )
        
        if plan.status != "active":
            logger.warning(
                "Subscription creation rejected: inactive plan (user_id=%s, plan_id=%s, plan_status=%s)",
                user_id,
                plan_id,
                plan.status,
            )
            raise HTTPException(
                status_code=400,
                detail={"code": "PLAN_INACTIVE", "message": "El plan no está activo"}
            )
        
        # Verificar que el usuario no tenga una suscripción activa
        active_sub = self.subscription_repo.get_active_by_user_id(user_id)
        if active_sub:
            logger.warning(
                "Subscription creation rejected: active subscription already exists (user_id=%s, plan_id=%s, active_subscription_id=%s, active_status=%s)",
                user_id,
                plan_id,
                active_sub.id,
                active_sub.status,
            )
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "SUBSCRIPTION_EXISTS",
                    "message": "El usuario ya tiene una suscripción activa"
                }
            )
        
        try:
            external_reference = f"user_{user_id}_plan_{plan_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            
            # Construir datos para Mercado Pago
            # auto_recurring NO se envía cuando se usa preapproval_plan_id;
            # el plan ya contiene esos datos y mandarlos duplicados hace que
            # MP intente cobrar inmediatamente requiriendo card_token_id.
            subscription_data = {
                "preapproval_plan_id": plan.mp_plan_id,
                "reason": plan.reason,
                "external_reference": external_reference,
                "payer_email": user.email,
                "back_url": back_url or plan.back_url
            }

            if notification_url:
                subscription_data["notification_url"] = notification_url
            
            # Si hay token de tarjeta, crear como autorizado
            if card_token_id:
                subscription_data["card_token_id"] = card_token_id
                subscription_data["status"] = "authorized"
            
            logger.info(
                "Subscription payload prepared for Mercado Pago: %s",
                {
                    "user_id": user_id,
                    "plan_id": plan_id,
                    "external_reference": external_reference,
                    "preapproval_plan_id": plan.mp_plan_id,
                    "has_card_token": bool(card_token_id),
                    "has_notification_url": bool(notification_url),
                    "back_url": subscription_data["back_url"],
                },
            )
            
            # Crear suscripción en Mercado Pago
            response = self.mp_client.preapproval().create(subscription_data)

            if (
                response.get("status") == 400
                and not card_token_id
                and (response.get("response", {}).get("message", "").lower() == "card_token_id is required")
            ):
                logger.warning(
                    "Mercado Pago rejected plan-based subscription with missing card token: %s",
                    {
                        "user_id": user_id,
                        "plan_id": plan_id,
                        "response": self._summarize_mp_response(response),
                    },
                )
                logger.info(
                    "MP requires card_token_id for plan-based subscription. "
                    "Falling back to no-plan checkout flow while preserving local plan_id=%s",
                    plan_id,
                )

                fallback_data = {
                    "reason": plan.reason,
                    "external_reference": external_reference,
                    "payer_email": user.email,
                    "auto_recurring": {
                        "frequency": plan.frequency,
                        "frequency_type": plan.frequency_type,
                        "transaction_amount": plan.transaction_amount,
                        "currency_id": plan.currency_id,
                    },
                    "back_url": back_url or plan.back_url,
                }

                # En fallback (sin preapproval_plan_id), MP no toma el free_trial del plan.
                # Para mantener comportamiento equivalente, diferimos el primer cobro con start_date.
                if (
                    plan.free_trial_frequency
                    and plan.free_trial_frequency > 0
                    and plan.free_trial_frequency_type
                ):
                    start_date = None
                    if plan.free_trial_frequency_type == "days":
                        start_date = datetime.utcnow() + timedelta(days=plan.free_trial_frequency)
                    elif plan.free_trial_frequency_type == "months":
                        # Aproximación operativa para fallback: 30 días por mes de trial.
                        start_date = datetime.utcnow() + timedelta(days=30 * plan.free_trial_frequency)

                    if start_date:
                        fallback_data["auto_recurring"]["start_date"] = start_date.isoformat() + "Z"

                if notification_url:
                    fallback_data["notification_url"] = notification_url

                logger.info(
                    "Fallback payload prepared for Mercado Pago: %s",
                    {
                        "user_id": user_id,
                        "plan_id": plan_id,
                        "external_reference": external_reference,
                        "has_notification_url": bool(notification_url),
                        "has_card_token": bool(card_token_id),
                        "auto_recurring": {
                            "frequency": fallback_data["auto_recurring"]["frequency"],
                            "frequency_type": fallback_data["auto_recurring"]["frequency_type"],
                            "transaction_amount": fallback_data["auto_recurring"]["transaction_amount"],
                            "currency_id": fallback_data["auto_recurring"]["currency_id"],
                            "has_start_date": "start_date" in fallback_data["auto_recurring"],
                        },
                    },
                )

                response = self.mp_client.preapproval().create(fallback_data)
            
            if response.get("status") not in [200, 201]:
                logger.error(
                    "Mercado Pago returned an error creating the subscription: %s",
                    {
                        "user_id": user_id,
                        "plan_id": plan_id,
                        "response": self._summarize_mp_response(response),
                    },
                )
                raise HTTPException(
                    status_code=503,
                    detail={
                        "code": "MERCADOPAGO_ERROR",
                        "message": "Error al crear la suscripción en Mercado Pago",
                        "mp_response": response
                    }
                )
            
            response_data = response.get("response", {})
            mp_preapproval_id = response_data.get("id")
            init_point = response_data.get("init_point")
            sandbox_init_point = response_data.get("sandbox_init_point")
            mp_status = response_data.get("status", "pending")
            
            if not mp_preapproval_id:
                logger.error(
                    "Mercado Pago response without preapproval ID: %s",
                    {
                        "user_id": user_id,
                        "plan_id": plan_id,
                        "response": self._summarize_mp_response(response),
                    },
                )
                raise HTTPException(
                    status_code=503,
                    detail={
                        "code": "MERCADOPAGO_ERROR",
                        "message": "No se recibió ID de suscripción de Mercado Pago"
                    }
                )
            
            # Guardar suscripción en BD
            subscription = UserSubscription(
                user_id=user_id,
                plan_id=plan_id,
                mp_preapproval_id=mp_preapproval_id,
                mp_plan_id=plan.mp_plan_id,
                payer_email=user.email,
                external_reference=external_reference,
                reason=plan.reason,
                frequency=plan.frequency,
                frequency_type=plan.frequency_type,
                transaction_amount=plan.transaction_amount,
                currency_id=plan.currency_id,
                status=mp_status,
                card_token_id=card_token_id,
                init_point=init_point,
                back_url=back_url or plan.back_url,
                mp_response=json.dumps(response_data)
            )
            
            # Si está autorizado, actualizar fechas
            if mp_status == "authorized":
                subscription.authorized_at = datetime.utcnow()
                # Actualizar membresía del usuario
                user.membership = "premium"
                self.user_repo.update(user)
                logger.info(f"User {user_id} upgraded to premium via subscription")
            
            subscription = self.subscription_repo.create(subscription)
            
            logger.info(
                "Subscription created successfully: %s",
                {
                    "subscription_id": subscription.id,
                    "user_id": user_id,
                    "plan_id": plan_id,
                    "mp_preapproval_id": mp_preapproval_id,
                    "status": mp_status,
                },
            )
            
            return {
                "subscription_id": subscription.id,
                "mp_preapproval_id": mp_preapproval_id,
                "init_point": init_point,
                "sandbox_init_point": sandbox_init_point,
                "status": mp_status,
                "plan_name": plan.name,
                "amount": plan.transaction_amount,
                "currency": plan.currency_id
            }
            
        except HTTPException:
            raise
        except Exception as exc:
            logger.exception(
                "Error creating subscription for user %s with plan %s",
                user_id,
                plan_id,
            )
            raise HTTPException(
                status_code=500,
                detail={"code": "SUBSCRIPTION_ERROR", "message": "Error al crear la suscripción"}
            )
    
    def create_subscription_without_plan(
        self,
        user_id: int,
        reason: str,
        transaction_amount: float,
        currency_id: str = "MXN",
        frequency: int = 1,
        frequency_type: str = "months",
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        card_token_id: str | None = None,
        back_url: str | None = None,
        notification_url: str | None = None
    ) -> dict:
        """
        Crea una suscripción sin plan asociado (más flexible, menos organizado).
        
        Args:
            user_id: ID del usuario
            reason: Descripción de la suscripción
            transaction_amount: Monto del cobro
            currency_id: Moneda
            frequency: Frecuencia de cobro
            frequency_type: Tipo de frecuencia
            start_date: Fecha de inicio
            end_date: Fecha de fin
            card_token_id: Token de tarjeta
            back_url: URL de retorno
            
        Returns:
            Diccionario con datos de la suscripción
        """
        logger.info(
            "Subscription without plan requested: user_id=%s reason=%s amount=%s currency=%s frequency=%s frequency_type=%s has_card_token=%s has_back_url=%s has_notification_url=%s",
            user_id,
            reason,
            transaction_amount,
            currency_id,
            frequency,
            frequency_type,
            bool(card_token_id),
            bool(back_url),
            bool(notification_url),
        )

        user = self.user_repo.get_by_id(user_id)
        if not user:
            logger.warning(
                "Subscription without plan rejected: user not found (user_id=%s)",
                user_id,
            )
            raise HTTPException(
                status_code=404,
                detail={"code": "USER_NOT_FOUND", "message": "Usuario no encontrado"}
            )
        
        active_sub = self.subscription_repo.get_active_by_user_id(user_id)
        if active_sub:
            logger.warning(
                "Subscription without plan rejected: active subscription already exists (user_id=%s, active_subscription_id=%s, active_status=%s)",
                user_id,
                active_sub.id,
                active_sub.status,
            )
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "SUBSCRIPTION_EXISTS",
                    "message": "El usuario ya tiene una suscripción activa"
                }
            )
        
        try:
            external_reference = f"user_{user_id}_nosplan_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            
            subscription_data = {
                "reason": reason,
                "external_reference": external_reference,
                "payer_email": user.email,
                "auto_recurring": {
                    "frequency": frequency,
                    "frequency_type": frequency_type,
                    "transaction_amount": transaction_amount,
                    "currency_id": currency_id
                }
            }
            
            if start_date:
                subscription_data["auto_recurring"]["start_date"] = start_date.isoformat()
            if end_date:
                subscription_data["auto_recurring"]["end_date"] = end_date.isoformat()
            if back_url:
                subscription_data["back_url"] = back_url
            if notification_url:
                subscription_data["notification_url"] = notification_url
            if card_token_id:
                subscription_data["card_token_id"] = card_token_id
                subscription_data["status"] = "authorized"
            
            logger.info(
                "Subscription without plan payload prepared for Mercado Pago: %s",
                {
                    "user_id": user_id,
                    "external_reference": external_reference,
                    "has_card_token": bool(card_token_id),
                    "has_notification_url": bool(notification_url),
                    "has_back_url": bool(back_url),
                    "auto_recurring": {
                        "frequency": frequency,
                        "frequency_type": frequency_type,
                        "transaction_amount": transaction_amount,
                        "currency_id": currency_id,
                        "has_start_date": bool(start_date),
                        "has_end_date": bool(end_date),
                    },
                },
            )

            response = self.mp_client.preapproval().create(subscription_data)
            
            if response.get("status") not in [200, 201]:
                logger.error(
                    "Mercado Pago returned an error creating the subscription without plan: %s",
                    {
                        "user_id": user_id,
                        "response": self._summarize_mp_response(response),
                    },
                )
                response_status = int(response.get("status") or 503)
                raise HTTPException(
                    status_code=response_status if 400 <= response_status < 600 else 503,
                    detail={
                        "code": "MERCADOPAGO_ERROR",
                        "message": "Error al crear la suscripción en Mercado Pago",
                        "mp_response": response
                    }
                )
            
            response_data = response.get("response", {})
            mp_preapproval_id = response_data.get("id")
            mp_status = response_data.get("status", "pending")
            
            subscription = UserSubscription(
                user_id=user_id,
                plan_id=None,
                mp_preapproval_id=mp_preapproval_id,
                payer_email=user.email,
                external_reference=external_reference,
                reason=reason,
                frequency=frequency,
                frequency_type=frequency_type,
                transaction_amount=transaction_amount,
                currency_id=currency_id,
                start_date=start_date,
                end_date=end_date,
                status=mp_status,
                card_token_id=card_token_id,
                init_point=response_data.get("init_point"),
                back_url=back_url,
                mp_response=json.dumps(response_data)
            )
            
            if mp_status == "authorized":
                subscription.authorized_at = datetime.utcnow()
                user.membership = "premium"
                self.user_repo.update(user)
            
            subscription = self.subscription_repo.create(subscription)

            logger.info(
                "Subscription without plan created successfully: %s",
                {
                    "subscription_id": subscription.id,
                    "user_id": user_id,
                    "mp_preapproval_id": mp_preapproval_id,
                    "status": mp_status,
                },
            )
            
            return {
                "subscription_id": subscription.id,
                "mp_preapproval_id": mp_preapproval_id,
                "init_point": response_data.get("init_point"),
                "sandbox_init_point": response_data.get("sandbox_init_point"),
                "status": mp_status
            }
            
        except HTTPException:
            raise
        except Exception as exc:
            logger.exception("Error creating subscription without plan for user %s", user_id)
            raise HTTPException(
                status_code=500,
                detail={"code": "SUBSCRIPTION_ERROR", "message": "Error al crear la suscripción"}
            )
    
    def get_subscription(self, subscription_id: int) -> UserSubscription:
        """Obtiene una suscripción por ID"""
        subscription = self.subscription_repo.get_by_id(subscription_id)
        if not subscription:
            raise HTTPException(
                status_code=404,
                detail={"code": "SUBSCRIPTION_NOT_FOUND", "message": "Suscripción no encontrada"}
            )
        return subscription
    
    def get_subscription_by_mp_id(self, mp_preapproval_id: str) -> UserSubscription:
        """Obtiene una suscripción por ID de Mercado Pago"""
        subscription = self.subscription_repo.get_by_mp_preapproval_id(mp_preapproval_id)
        if not subscription:
            raise HTTPException(
                status_code=404,
                detail={"code": "SUBSCRIPTION_NOT_FOUND", "message": "Suscripción no encontrada"}
            )
        return subscription
    
    def get_user_subscriptions(self, user_id: int) -> list[UserSubscription]:
        """Obtiene todas las suscripciones de un usuario"""
        return self.subscription_repo.get_by_user_id(user_id)
    
    def get_active_subscription(self, user_id: int) -> UserSubscription | None:
        """
        Obtiene la suscripción activa de un usuario.

        Sincroniza contra Mercado Pago cuando exista una suscripción local activa para
        evitar falsos positivos cuando el usuario cancela desde MP y el webhook tarda.
        """
        active_subscription = self.subscription_repo.get_active_by_user_id(user_id)

        if active_subscription and active_subscription.mp_preapproval_id:
            # Reconciliar estado y membresía con MP antes de devolver resultado.
            self.get_subscription_status(active_subscription.id)
            return self.subscription_repo.get_active_by_user_id(user_id)

        return active_subscription
    
    def get_subscription_status(self, subscription_id: int) -> dict:
        """
        Obtiene el estado detallado de una suscripción.
        
        Sincroniza con Mercado Pago si es necesario.
        """
        subscription = self.get_subscription(subscription_id)
        
        # Sincronizar con Mercado Pago
        if subscription.mp_preapproval_id:
            try:
                response = self.mp_client.preapproval().get(subscription.mp_preapproval_id)
                if response.get("status") == 200:
                    mp_data = response.get("response", {})
                    mp_status = mp_data.get("status")
                    
                    if mp_status and mp_status != subscription.status:
                        subscription.status = mp_status
                        subscription.mp_response = json.dumps(mp_data)
                        subscription.updated_at = datetime.utcnow()
                        self.subscription_repo.update(subscription)
                        logger.info(f"Subscription {subscription_id} status updated to {mp_status}")

                    effective_status = mp_status or subscription.status
                    user = self.user_repo.get_by_id(subscription.user_id)
                    if user:
                        if effective_status == "authorized" and user.membership != "premium":
                            user.membership = "premium"
                            self.user_repo.update(user)
                        elif effective_status in ["paused", "cancelled"] and user.membership == "premium":
                            user.membership = "gratuito"
                            self.user_repo.update(user)
            except Exception as exc:
                logger.warning(f"Could not sync subscription status from MP: {exc}")
        
        return {
            "id": subscription.id,
            "user_id": subscription.user_id,
            "status": subscription.status,
            "transaction_amount": subscription.transaction_amount,
            "currency_id": subscription.currency_id,
            "next_payment_date": subscription.next_payment_date,
            "last_payment_date": subscription.last_payment_date,
            "payments_count": subscription.payments_count,
            "failed_payments_count": subscription.failed_payments_count,
            "is_active": subscription.status == "authorized"
        }
    
    def pause_subscription(self, subscription_id: int, reason: str | None = None) -> UserSubscription:
        """
        Pausa una suscripción temporalmente.
        
        Args:
            subscription_id: ID de la suscripción
            reason: Motivo de la pausa (opcional)
            
        Returns:
            Suscripción pausada
        """
        subscription = self.get_subscription(subscription_id)
        
        if subscription.status != "authorized":
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "INVALID_STATUS",
                    "message": "Solo se pueden pausar suscripciones activas"
                }
            )
        
        try:
            if subscription.mp_preapproval_id:
                response = self.mp_client.preapproval().update(
                    subscription.mp_preapproval_id,
                    {"status": "paused"}
                )
                
                if response.get("status") not in [200, 201]:
                    logger.error(f"MP Error pausing subscription: {response}")
                    raise HTTPException(
                        status_code=503,
                        detail={"code": "MERCADOPAGO_ERROR", "message": "Error al pausar en Mercado Pago"}
                    )
            
            subscription.status = "paused"
            subscription.updated_at = datetime.utcnow()
            subscription = self.subscription_repo.update(subscription)
            
            # Actualizar membresía del usuario
            user = self.user_repo.get_by_id(subscription.user_id)
            if user:
                user.membership = "gratuito"
                self.user_repo.update(user)
            
            logger.info(f"Subscription {subscription_id} paused. Reason: {reason}")
            return subscription
            
        except HTTPException:
            raise
        except Exception as exc:
            logger.exception(f"Error pausing subscription: {str(exc)}")
            raise HTTPException(
                status_code=500,
                detail={"code": "SUBSCRIPTION_ERROR", "message": "Error al pausar la suscripción"}
            )
    
    def reactivate_subscription(self, subscription_id: int) -> UserSubscription:
        """
        Reactiva una suscripción pausada.
        
        Args:
            subscription_id: ID de la suscripción
            
        Returns:
            Suscripción reactivada
        """
        subscription = self.get_subscription(subscription_id)
        
        if subscription.status != "paused":
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "INVALID_STATUS",
                    "message": "Solo se pueden reactivar suscripciones pausadas"
                }
            )
        
        try:
            if subscription.mp_preapproval_id:
                response = self.mp_client.preapproval().update(
                    subscription.mp_preapproval_id,
                    {"status": "authorized"}
                )
                
                if response.get("status") not in [200, 201]:
                    logger.error(f"MP Error reactivating subscription: {response}")
                    raise HTTPException(
                        status_code=503,
                        detail={"code": "MERCADOPAGO_ERROR", "message": "Error al reactivar en Mercado Pago"}
                    )
            
            subscription.status = "authorized"
            subscription.updated_at = datetime.utcnow()
            subscription = self.subscription_repo.update(subscription)
            
            # Restaurar membresía premium
            user = self.user_repo.get_by_id(subscription.user_id)
            if user:
                user.membership = "premium"
                self.user_repo.update(user)
            
            logger.info(f"Subscription {subscription_id} reactivated")
            return subscription
            
        except HTTPException:
            raise
        except Exception as exc:
            logger.exception(f"Error reactivating subscription: {str(exc)}")
            raise HTTPException(
                status_code=500,
                detail={"code": "SUBSCRIPTION_ERROR", "message": "Error al reactivar la suscripción"}
            )
    
    def cancel_subscription(self, subscription_id: int, reason: str | None = None) -> UserSubscription:
        """
        Cancela una suscripción definitivamente.
        
        Args:
            subscription_id: ID de la suscripción
            reason: Motivo de la cancelación (opcional)
            
        Returns:
            Suscripción cancelada
        """
        subscription = self.get_subscription(subscription_id)
        
        if subscription.status == "cancelled":
            raise HTTPException(
                status_code=400,
                detail={"code": "ALREADY_CANCELLED", "message": "La suscripción ya está cancelada"}
            )
        
        try:
            if subscription.mp_preapproval_id:
                response = self.mp_client.preapproval().update(
                    subscription.mp_preapproval_id,
                    {"status": "cancelled"}
                )
                
                if response.get("status") not in [200, 201]:
                    logger.error(f"MP Error cancelling subscription: {response}")
                    raise HTTPException(
                        status_code=503,
                        detail={"code": "MERCADOPAGO_ERROR", "message": "Error al cancelar en Mercado Pago"}
                    )
            
            subscription.status = "cancelled"
            subscription.cancelled_at = datetime.utcnow()
            subscription.updated_at = datetime.utcnow()
            subscription = self.subscription_repo.update(subscription)
            
            # Revocar membresía premium
            user = self.user_repo.get_by_id(subscription.user_id)
            if user:
                user.membership = "gratuito"
                self.user_repo.update(user)
            
            logger.info(f"Subscription {subscription_id} cancelled. Reason: {reason}")
            return subscription
            
        except HTTPException:
            raise
        except Exception as exc:
            logger.exception(f"Error cancelling subscription: {str(exc)}")
            raise HTTPException(
                status_code=500,
                detail={"code": "SUBSCRIPTION_ERROR", "message": "Error al cancelar la suscripción"}
            )
    
    def update_subscription_amount(
        self,
        subscription_id: int,
        transaction_amount: float,
        currency_id: str = "MXN"
    ) -> UserSubscription:
        """
        Modifica el monto de una suscripción.
        
        Args:
            subscription_id: ID de la suscripción
            transaction_amount: Nuevo monto
            currency_id: Moneda
            
        Returns:
            Suscripción actualizada
        """
        subscription = self.get_subscription(subscription_id)
        
        if subscription.status not in ["authorized", "paused"]:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "INVALID_STATUS",
                    "message": "No se puede modificar el monto de esta suscripción"
                }
            )
        
        try:
            if subscription.mp_preapproval_id:
                response = self.mp_client.preapproval().update(
                    subscription.mp_preapproval_id,
                    {
                        "auto_recurring": {
                            "transaction_amount": transaction_amount,
                            "currency_id": currency_id
                        }
                    }
                )
                
                if response.get("status") not in [200, 201]:
                    logger.error(f"MP Error updating amount: {response}")
                    raise HTTPException(
                        status_code=503,
                        detail={"code": "MERCADOPAGO_ERROR", "message": "Error al actualizar monto en Mercado Pago"}
                    )
            
            subscription.transaction_amount = transaction_amount
            subscription.currency_id = currency_id
            subscription.updated_at = datetime.utcnow()
            subscription = self.subscription_repo.update(subscription)
            
            logger.info(f"Subscription {subscription_id} amount updated to {transaction_amount} {currency_id}")
            return subscription
            
        except HTTPException:
            raise
        except Exception as exc:
            logger.exception(f"Error updating subscription amount: {str(exc)}")
            raise HTTPException(
                status_code=500,
                detail={"code": "SUBSCRIPTION_ERROR", "message": "Error al actualizar el monto"}
            )
    
    def update_subscription_card(self, subscription_id: int, card_token_id: str) -> UserSubscription:
        """
        Actualiza la tarjeta de una suscripción.
        
        Args:
            subscription_id: ID de la suscripción
            card_token_id: Nuevo token de tarjeta
            
        Returns:
            Suscripción actualizada
        """
        subscription = self.get_subscription(subscription_id)
        
        if subscription.status not in ["authorized", "paused"]:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "INVALID_STATUS",
                    "message": "No se puede cambiar la tarjeta de esta suscripción"
                }
            )
        
        try:
            if subscription.mp_preapproval_id:
                response = self.mp_client.preapproval().update(
                    subscription.mp_preapproval_id,
                    {"card_token_id": card_token_id}
                )
                
                if response.get("status") not in [200, 201]:
                    logger.error(f"MP Error updating card: {response}")
                    raise HTTPException(
                        status_code=503,
                        detail={"code": "MERCADOPAGO_ERROR", "message": "Error al actualizar tarjeta en Mercado Pago"}
                    )
            
            subscription.card_token_id = card_token_id
            subscription.updated_at = datetime.utcnow()
            subscription = self.subscription_repo.update(subscription)
            
            logger.info(f"Subscription {subscription_id} card updated")
            return subscription
            
        except HTTPException:
            raise
        except Exception as exc:
            logger.exception(f"Error updating subscription card: {str(exc)}")
            raise HTTPException(
                status_code=500,
                detail={"code": "SUBSCRIPTION_ERROR", "message": "Error al actualizar la tarjeta"}
            )
    
    def get_subscription_payments(self, subscription_id: int) -> list[SubscriptionPayment]:
        """Obtiene el historial de pagos de una suscripción"""
        self.get_subscription(subscription_id)  # Validar que existe
        return self.payment_repo.get_by_subscription_id(subscription_id)
    
    def process_webhook_notification(self, notification: dict) -> dict:
        """
        Procesa notificaciones de webhook de suscripciones de Mercado Pago.
        
        Tipos de notificación soportados:
        - subscription_preapproval: Cambios en la suscripción
        - subscription_authorized_payment: Pagos recurrentes
        
        Args:
            notification: Diccionario con datos de la notificación
            
        Returns:
            Diccionario con resultado del procesamiento
        """
        notification_type = notification.get("type")
        notification_id = notification.get("id")
        data = notification.get("data", {})
        resource_id = data.get("id")
        
        logger.info(f"Processing subscription webhook: type={notification_type}, id={notification_id}, resource={resource_id}")
        
        if notification_type == "subscription_preapproval":
            return self._process_preapproval_notification(resource_id)
        elif notification_type == "subscription_authorized_payment":
            return self._process_authorized_payment_notification(resource_id)
        else:
            logger.info(f"Ignoring webhook type: {notification_type}")
            return {"status": "ignored", "type": notification_type}
    
    def _process_preapproval_notification(self, preapproval_id: str) -> dict:
        """Procesa notificaciones de cambios en la suscripción"""
        try:
            # Obtener datos de Mercado Pago
            response = self.mp_client.preapproval().get(preapproval_id)
            
            if response.get("status") != 200:
                logger.warning(f"Could not fetch preapproval from MP: {preapproval_id}")
                return {"status": "ignored", "reason": "preapproval_not_found_in_mp"}
            
            mp_data = response.get("response", {})
            mp_status = mp_data.get("status")
            external_ref = mp_data.get("external_reference", "")
            payer_email = mp_data.get("payer_email")
            
            # Buscar suscripción en BD
            subscription = self.subscription_repo.get_by_mp_preapproval_id(preapproval_id)
            
            if not subscription:
                # Intentar buscar por referencia externa
                subscription = self.subscription_repo.get_by_external_reference(external_ref)
            
            if not subscription:
                logger.warning(f"Subscription not found in DB: {preapproval_id}")
                return {"status": "ignored", "reason": "subscription_not_in_db"}
            
            # Actualizar estado
            old_status = subscription.status
            subscription.status = mp_status
            subscription.mp_response = json.dumps(mp_data)
            subscription.updated_at = datetime.utcnow()
            should_notify_payment_success = False
            
            # Procesar cambios de estado
            if mp_status == "authorized" and old_status != "authorized":
                subscription.authorized_at = datetime.utcnow()
                # Activar premium
                user = self.user_repo.get_by_id(subscription.user_id)
                if user:
                    user.membership = "premium"
                    self.user_repo.update(user)
                    logger.info(f"User {subscription.user_id} upgraded to premium")
                should_notify_payment_success = True
            
            elif mp_status in ["cancelled", "paused"] and old_status == "authorized":
                # Revocar premium
                user = self.user_repo.get_by_id(subscription.user_id)
                if user:
                    user.membership = "gratuito"
                    self.user_repo.update(user)
                    logger.info(f"User {subscription.user_id} downgraded to free")
            
            if mp_status == "cancelled":
                subscription.cancelled_at = datetime.utcnow()
            
            self.subscription_repo.update(subscription)

            if should_notify_payment_success:
                logger.info(
                    "Subscription %s transitioned %s -> %s via preapproval webhook; triggering PAYMENT_SUCCESS notification",
                    subscription.id,
                    old_status,
                    mp_status,
                )
                self._send_payment_success_notification(subscription)
            
            logger.info(f"Subscription {subscription.id} updated: {old_status} -> {mp_status}")
            
            return {
                "status": "processed",
                "subscription_id": subscription.id,
                "old_status": old_status,
                "new_status": mp_status
            }
            
        except Exception as exc:
            logger.exception(f"Error processing preapproval notification: {str(exc)}")
            return {"status": "error", "reason": str(exc)}
    
    def _process_authorized_payment_notification(self, payment_id: str) -> dict:
        """Procesa notificaciones de pagos recurrentes"""
        try:
            # Obtener datos del pago de Mercado Pago
            response = self.mp_client.payment().get(payment_id)
            
            if response.get("status") != 200:
                logger.warning(f"Could not fetch payment from MP: {payment_id}")
                return {"status": "ignored", "reason": "payment_not_found_in_mp"}
            
            mp_data = response.get("response", {})
            mp_status = mp_data.get("status")
            preapproval_id = mp_data.get("metadata", {}).get("preapproval_id")
            
            # Buscar suscripción
            subscription = None
            if preapproval_id:
                subscription = self.subscription_repo.get_by_mp_preapproval_id(preapproval_id)
            
            if not subscription:
                external_ref = mp_data.get("external_reference", "")
                subscription = self.subscription_repo.get_by_external_reference(external_ref)
            
            if not subscription:
                logger.warning(f"Subscription not found for payment: {payment_id}")
                return {"status": "ignored", "reason": "subscription_not_found"}
            
            # Verificar si ya existe el pago
            existing_payment = self.payment_repo.get_by_mp_payment_id(payment_id)
            if existing_payment:
                # Actualizar estado si cambió
                if existing_payment.status != self._map_mp_payment_status(mp_status):
                    existing_payment.status = self._map_mp_payment_status(mp_status)
                    existing_payment.mp_response = json.dumps(mp_data)
                    existing_payment.updated_at = datetime.utcnow()
                    if mp_status == "approved":
                        existing_payment.payment_date = datetime.utcnow()
                    self.payment_repo.update(existing_payment)

                # Mantener suscripción/membresía alineadas aunque el pago ya existiera.
                if mp_status == "approved" and subscription.status != "authorized":
                    subscription.status = "authorized"
                    if not subscription.authorized_at:
                        subscription.authorized_at = datetime.utcnow()
                    subscription.updated_at = datetime.utcnow()
                    self.subscription_repo.update(subscription)

                    user = self.user_repo.get_by_id(subscription.user_id)
                    if user and user.membership != "premium":
                        user.membership = "premium"
                        self.user_repo.update(user)

                    self._send_payment_success_notification(subscription)

                return {"status": "updated", "payment_id": existing_payment.id}
            
            # Crear registro de pago
            payment = SubscriptionPayment(
                subscription_id=subscription.id,
                mp_payment_id=payment_id,
                mp_preapproval_id=subscription.mp_preapproval_id,
                transaction_amount=mp_data.get("transaction_amount", subscription.transaction_amount),
                currency_id=mp_data.get("currency_id", subscription.currency_id),
                status=self._map_mp_payment_status(mp_status),
                payment_method_id=mp_data.get("payment_method_id"),
                payment_type=mp_data.get("payment_type_id"),
                mp_response=json.dumps(mp_data)
            )
            
            if mp_status == "approved":
                payment.payment_date = datetime.utcnow()
                subscription.status = "authorized"
                if not subscription.authorized_at:
                    subscription.authorized_at = datetime.utcnow()
                subscription.last_payment_date = datetime.utcnow()
                subscription.payments_count += 1
                subscription.failed_payments_count = 0

                user = self.user_repo.get_by_id(subscription.user_id)
                if user and user.membership != "premium":
                    user.membership = "premium"
                    self.user_repo.update(user)
                self._send_payment_success_notification(subscription)
            elif mp_status in ["rejected", "cancelled"]:
                payment.rejection_reason = mp_data.get("status_detail")
                subscription.failed_payments_count += 1
                
                # Cancelar suscripción después de 3 pagos fallidos consecutivos
                if subscription.failed_payments_count >= 3:
                    subscription.status = "cancelled"
                    subscription.cancelled_at = datetime.utcnow()
                    user = self.user_repo.get_by_id(subscription.user_id)
                    if user:
                        user.membership = "gratuito"
                        self.user_repo.update(user)
                    logger.warning(f"Subscription {subscription.id} cancelled due to 3 failed payments")
            
            subscription.updated_at = datetime.utcnow()
            self.subscription_repo.update(subscription)
            payment = self.payment_repo.create(payment)
            
            logger.info(f"Payment recorded: id={payment.id}, subscription={subscription.id}, status={payment.status}")
            
            return {
                "status": "processed",
                "payment_id": payment.id,
                "subscription_id": subscription.id,
                "payment_status": payment.status
            }
            
        except Exception as exc:
            logger.exception(f"Error processing payment notification: {str(exc)}")
            return {"status": "error", "reason": str(exc)}
    
    def _map_mp_payment_status(self, mp_status: str) -> str:
        """Mapea el estado de pago de Mercado Pago al estado interno"""
        status_map = {
            "approved": "processed",
            "pending": "waiting_for_gateway",
            "in_process": "waiting_for_gateway",
            "rejected": "rejected",
            "cancelled": "rejected",
            "refunded": "refunded",
            "charged_back": "refunded"
        }
        return status_map.get(mp_status, "waiting_for_gateway")

    def verify_webhook_signature(
        self,
        signature_header: str | None,
        resource_id: str | None,
        request_id: str | None
    ) -> bool:
        """
        Valida la firma HMAC del webhook de Mercado Pago cuando está habilitada.

        Formato esperado en `x-signature`: ts=<timestamp>,v1=<hmac_hex>
        Template oficial: id:{data.id};request-id:{x-request-id};ts:{ts};
        """
        if not self.mp_config.validate_webhook_signature:
            return True

        secret = self.mp_config.webhook_secret
        if not secret:
            logger.warning("Webhook signature validation enabled but secret is missing")
            return False

        if not signature_header or not resource_id or not request_id:
            return False

        parts: dict[str, str] = {}
        for item in signature_header.split(","):
            if "=" not in item:
                continue
            key, value = item.split("=", 1)
            parts[key.strip()] = value.strip()

        ts = parts.get("ts")
        received_hash = parts.get("v1")
        if not ts or not received_hash:
            return False

        manifest = f"id:{resource_id};request-id:{request_id};ts:{ts};"
        expected_hash = hmac.new(
            secret.encode("utf-8"),
            manifest.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(received_hash, expected_hash)
