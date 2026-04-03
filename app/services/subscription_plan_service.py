"""
Servicio para gestionar planes de suscripción con Mercado Pago
"""
import logging
import json
import httpx
from datetime import datetime
from fastapi import HTTPException
from app.shared.config.mercado_pago import MercadoPagoConfig
from app.repositories.subscription_plan_repository import SubscriptionPlanRepository
from app.models.SubscriptionPlan import SubscriptionPlan

logger = logging.getLogger(__name__)


class SubscriptionPlanService:
    """Servicio para gestionar planes de suscripción con Mercado Pago"""
    
    def __init__(
        self,
        plan_repository: SubscriptionPlanRepository,
        mp_config: MercadoPagoConfig
    ):
        self.plan_repo = plan_repository
        self.mp_config = mp_config
        self.mp_client = mp_config.get_client()

    def _mp_create_plan(self, plan_data: dict) -> dict:
        """Crea un preapproval_plan en Mercado Pago con fallback REST para SDKs antiguos."""
        if hasattr(self.mp_client, "preapproval_plan"):
            return self.mp_client.preapproval_plan().create(plan_data)

        headers = {
            "Authorization": f"Bearer {self.mp_config.access_token}",
            "Content-Type": "application/json"
        }
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                "https://api.mercadopago.com/preapproval_plan",
                headers=headers,
                json=plan_data
            )

        response_json = {}
        try:
            response_json = response.json()
        except Exception:
            response_json = {"message": response.text}

        return {
            "status": response.status_code,
            "response": response_json
        }

    def _mp_update_plan(self, mp_plan_id: str, update_data: dict) -> dict:
        """Actualiza un preapproval_plan en Mercado Pago con fallback REST para SDKs antiguos."""
        if hasattr(self.mp_client, "preapproval_plan"):
            return self.mp_client.preapproval_plan().update(mp_plan_id, update_data)

        headers = {
            "Authorization": f"Bearer {self.mp_config.access_token}",
            "Content-Type": "application/json"
        }
        with httpx.Client(timeout=30.0) as client:
            response = client.put(
                f"https://api.mercadopago.com/preapproval_plan/{mp_plan_id}",
                headers=headers,
                json=update_data
            )

        response_json = {}
        try:
            response_json = response.json()
        except Exception:
            response_json = {"message": response.text}

        return {
            "status": response.status_code,
            "response": response_json
        }

    def _raise_mp_error(self, response: dict, fallback_message: str) -> None:
        """Normaliza errores de Mercado Pago conservando status/code originales."""
        status_code = int(response.get("status") or 503)
        response_data = response.get("response", {})
        mp_code = response_data.get("code", "MERCADOPAGO_ERROR")
        mp_message = response_data.get("message") or fallback_message

        raise HTTPException(
            status_code=status_code if 400 <= status_code < 600 else 503,
            detail={
                "code": mp_code,
                "message": mp_message,
                "mp_response": response
            }
        )
    
    def create_plan(
        self,
        name: str,
        reason: str,
        transaction_amount: float,
        currency_id: str = "MXN",
        frequency: int = 1,
        frequency_type: str = "months",
        description: str | None = None,
        repetitions: int | None = None,
        billing_day: int | None = None,
        billing_day_proportional: bool = True,
        free_trial_frequency: int | None = None,
        free_trial_frequency_type: str | None = None,
        back_url: str | None = None,
        notification_url: str | None = None
    ) -> dict:
        """
        Crea un plan de suscripción en Mercado Pago y lo guarda en BD.
        
        Args:
            name: Nombre interno del plan
            reason: Título visible para el usuario en MP
            transaction_amount: Monto del cobro
            currency_id: Moneda (default: MXN)
            frequency: Cada cuánto se cobra
            frequency_type: Tipo de frecuencia (days/months)
            description: Descripción del plan
            repetitions: Número de cobros (None=ilimitado)
            billing_day: Día del mes para cobro (solo mensual)
            billing_day_proportional: Cobrar proporcional al suscribirse
            free_trial_frequency: Duración del trial
            free_trial_frequency_type: Tipo de duración del trial
            back_url: URL de retorno
            
        Returns:
            Diccionario con datos del plan creado
            
        Raises:
            HTTPException: Si hay error en la creación
        """
        # Verificar que no exista un plan con el mismo nombre
        existing = self.plan_repo.get_by_name(name)
        if existing:
            raise HTTPException(
                status_code=400,
                detail={"code": "PLAN_EXISTS", "message": f"Ya existe un plan con el nombre '{name}'"}
            )
        
        try:
            # Construir datos para Mercado Pago
            plan_data = {
                "reason": reason,
                "auto_recurring": {
                    "frequency": frequency,
                    "frequency_type": frequency_type,
                    "transaction_amount": transaction_amount,
                    "currency_id": currency_id
                }
            }
            
            # Agregar campos opcionales
            if repetitions:
                plan_data["auto_recurring"]["repetitions"] = repetitions
            
            if billing_day and frequency_type == "months":
                plan_data["auto_recurring"]["billing_day"] = billing_day
                plan_data["auto_recurring"]["billing_day_proportional"] = billing_day_proportional
            
            if free_trial_frequency and free_trial_frequency_type:
                plan_data["auto_recurring"]["free_trial"] = {
                    "frequency": free_trial_frequency,
                    "frequency_type": free_trial_frequency_type
                }
            
            if back_url:
                plan_data["back_url"] = back_url

            if notification_url:
                plan_data["notification_url"] = notification_url
            
            logger.info(f"Creating subscription plan in MP: {plan_data}")
            
            # Crear plan en Mercado Pago
            response = self._mp_create_plan(plan_data)
            
            if response.get("status") not in [200, 201]:
                logger.error(f"MP Error creating plan: {response}")
                self._raise_mp_error(response, "Error al crear el plan en Mercado Pago")
            
            response_data = response.get("response", {})
            mp_plan_id = response_data.get("id")
            
            if not mp_plan_id:
                logger.error(f"MP response without plan ID: {response_data}")
                raise HTTPException(
                    status_code=503,
                    detail={
                        "code": "MERCADOPAGO_ERROR",
                        "message": "No se recibió ID del plan de Mercado Pago"
                    }
                )
            
            # Guardar plan en BD
            plan = SubscriptionPlan(
                mp_plan_id=mp_plan_id,
                name=name,
                description=description,
                reason=reason,
                frequency=frequency,
                frequency_type=frequency_type,
                transaction_amount=transaction_amount,
                currency_id=currency_id,
                repetitions=repetitions,
                billing_day=billing_day,
                billing_day_proportional=billing_day_proportional,
                free_trial_frequency=free_trial_frequency,
                free_trial_frequency_type=free_trial_frequency_type,
                back_url=back_url,
                status="active",
                mp_response=json.dumps(response_data)
            )
            plan = self.plan_repo.create(plan)
            
            logger.info(f"Subscription plan created: id={plan.id}, mp_plan_id={mp_plan_id}")
            
            return {
                "id": plan.id,
                "mp_plan_id": mp_plan_id,
                "name": plan.name,
                "reason": plan.reason,
                "transaction_amount": plan.transaction_amount,
                "currency_id": plan.currency_id,
                "frequency": plan.frequency,
                "frequency_type": plan.frequency_type,
                "status": plan.status
            }
            
        except HTTPException:
            raise
        except Exception as exc:
            logger.exception(f"Error creating subscription plan: {str(exc)}")
            raise HTTPException(
                status_code=500,
                detail={"code": "PLAN_ERROR", "message": "Error al crear el plan de suscripción"}
            )
    
    def get_plan(self, plan_id: int) -> SubscriptionPlan:
        """
        Obtiene un plan por ID.
        
        Args:
            plan_id: ID del plan
            
        Returns:
            Plan de suscripción
            
        Raises:
            HTTPException: Si el plan no existe
        """
        plan = self.plan_repo.get_by_id(plan_id)
        if not plan:
            raise HTTPException(
                status_code=404,
                detail={"code": "PLAN_NOT_FOUND", "message": "Plan de suscripción no encontrado"}
            )
        return plan
    
    def get_plan_by_mp_id(self, mp_plan_id: str) -> SubscriptionPlan:
        """
        Obtiene un plan por ID de Mercado Pago.
        
        Args:
            mp_plan_id: ID del plan en Mercado Pago
            
        Returns:
            Plan de suscripción
            
        Raises:
            HTTPException: Si el plan no existe
        """
        plan = self.plan_repo.get_by_mp_plan_id(mp_plan_id)
        if not plan:
            raise HTTPException(
                status_code=404,
                detail={"code": "PLAN_NOT_FOUND", "message": "Plan de suscripción no encontrado"}
            )
        return plan
    
    def list_active_plans(self) -> list[SubscriptionPlan]:
        """
        Lista todos los planes activos.
        
        Returns:
            Lista de planes activos ordenados por precio
        """
        return self.plan_repo.get_active_plans()
    
    def list_all_plans(self) -> list[SubscriptionPlan]:
        """
        Lista todos los planes.
        
        Returns:
            Lista de todos los planes
        """
        return self.plan_repo.get_all()
    
    def update_plan(
        self,
        plan_id: int,
        name: str | None = None,
        description: str | None = None,
        reason: str | None = None,
        transaction_amount: float | None = None,
        status: str | None = None,
        back_url: str | None = None
    ) -> SubscriptionPlan:
        """
        Actualiza un plan de suscripción.
        
        Args:
            plan_id: ID del plan
            name: Nuevo nombre (opcional)
            description: Nueva descripción (opcional)
            reason: Nuevo título visible (opcional)
            transaction_amount: Nuevo monto (opcional)
            status: Nuevo estado (opcional)
            back_url: Nueva URL de retorno (opcional)
            
        Returns:
            Plan actualizado
            
        Raises:
            HTTPException: Si el plan no existe o hay error en MP
        """
        plan = self.get_plan(plan_id)
        
        try:
            # Preparar datos para actualizar en MP
            update_data = {}
            
            if reason:
                update_data["reason"] = reason
            
            if transaction_amount:
                update_data["auto_recurring"] = {
                    "transaction_amount": transaction_amount,
                    "currency_id": plan.currency_id
                }
            
            if back_url:
                update_data["back_url"] = back_url
            
            # Actualizar en Mercado Pago si hay cambios relevantes
            if update_data and plan.mp_plan_id:
                logger.info(f"Updating plan in MP: {plan.mp_plan_id}, data={update_data}")
                response = self._mp_update_plan(plan.mp_plan_id, update_data)
                
                if response.get("status") not in [200, 201]:
                    logger.error(f"MP Error updating plan: {response}")
                    self._raise_mp_error(response, "Error al actualizar el plan en Mercado Pago")
            
            # Actualizar en BD
            if name:
                plan.name = name
            if description is not None:
                plan.description = description
            if reason:
                plan.reason = reason
            if transaction_amount:
                plan.transaction_amount = transaction_amount
            if status:
                plan.status = status
            if back_url is not None:
                plan.back_url = back_url
            
            plan.updated_at = datetime.utcnow()
            plan = self.plan_repo.update(plan)
            
            logger.info(f"Subscription plan updated: id={plan.id}")
            return plan
            
        except HTTPException:
            raise
        except Exception as exc:
            logger.exception(f"Error updating subscription plan: {str(exc)}")
            raise HTTPException(
                status_code=500,
                detail={"code": "PLAN_ERROR", "message": "Error al actualizar el plan"}
            )
    
    def deactivate_plan(self, plan_id: int) -> SubscriptionPlan:
        """
        Desactiva un plan (no lo elimina).
        
        Args:
            plan_id: ID del plan
            
        Returns:
            Plan desactivado
        """
        return self.update_plan(plan_id, status="inactive")
    
    def cancel_plan(self, plan_id: int) -> SubscriptionPlan:
        """
        Cancela un plan definitivamente.
        
        IMPORTANTE: Los suscriptores existentes seguirán activos.
        
        Args:
            plan_id: ID del plan
            
        Returns:
            Plan cancelado
        """
        return self.update_plan(plan_id, status="cancelled")
