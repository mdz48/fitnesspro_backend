"""
Servicio para gestionar pagos con Mercado Pago
"""
import logging
import json
from datetime import datetime
from fastapi import HTTPException
from app.shared.config.mercado_pago import MercadoPagoConfig
from app.repositories.payment_repository import PaymentRepository
from app.repositories.user_repository import UserRepository
from app.models.Payment import Payment

logger = logging.getLogger(__name__)


class PaymentService:
    """Servicio para gestionar pagos con Mercado Pago"""
    
    AMOUNT = 149.0  # MXN
    CURRENCY = "MXN"
    DESCRIPTION = "Acceso Premium FitnessPro - Pago Único"
    
    def __init__(
        self,
        payment_repository: PaymentRepository,
        user_repository: UserRepository,
        mp_config: MercadoPagoConfig
    ):
        self.payment_repo = payment_repository
        self.user_repo = user_repository
        self.mp_config = mp_config
        self.mp_client = mp_config.get_client()
    
    def create_checkout_preference(self, user_id: int, success_url: str, pending_url: str, failure_url: str) -> dict:
        """
        Crea una preferencia de pago en Mercado Pago
        
        Args:
            user_id: ID del usuario que realiza el pago
            success_url: URL de retorno en caso de pago exitoso
            pending_url: URL de retorno si el pago está pendiente
            failure_url: URL de retorno si el pago falla
            
        Returns:
            Diccionario con preference_id e init_point de Mercado Pago
            
        Raises:
            HTTPException: Si el usuario no existe o hay error con MP
        """
        # Verificar que el usuario existe
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        try:
            # Construir la preferencia para Mercado Pago
            preference_data = {
                "items": [
                    {
                        "title": self.DESCRIPTION,
                        "quantity": 1,
                        "unit_price": self.AMOUNT,
                        "currency_id": self.CURRENCY,
                        "description": "Acceso a todas las características premium de FitnessPro"
                    }
                ],
                "payer": {
                    "email": user.email,
                    "name": user.name,
                    "surname": user.lastname or ""
                },
                "back_urls": {
                    "success": success_url,
                    "pending": pending_url,
                    "failure": failure_url
                },
                "auto_return": "approved",
                "external_reference": f"user_{user_id}",
                "additional_info": {
                    "custom_field": json.dumps({
                        "user_id": user_id,
                        "email": user.email
                    })
                }
            }
            
            # Crear preferencia en Mercado Pago
            response = self.mp_client.preference().create(preference_data)
            
            if response.get("status") != 201:
                logger.error(f"MP Error creating preference: {response}")
                raise HTTPException(
                    status_code=503,
                    detail={
                        "code": "MERCADOPAGO_ERROR",
                        "message": "Failed to create payment preference"
                    }
                )
            
            response_data = response.get("response", {})
            preference_id = response_data.get("id")
            
            if not preference_id:
                logger.error(f"MP response without preference ID: {response_data}")
                raise HTTPException(
                    status_code=503,
                    detail={
                        "code": "MERCADOPAGO_ERROR",
                        "message": "No preference ID received from Mercado Pago"
                    }
                )
            
            # Guardar preferencia en BD
            payment = Payment(
                user_id=user_id,
                preference_id=preference_id,
                amount=self.AMOUNT,
                currency=self.CURRENCY,
                status="pending",
                external_reference=f"user_{user_id}",
                mercadopago_response=json.dumps(response_data)
            )
            payment = self.payment_repo.create(payment)
            
            logger.info(f"Payment preference created: preference_id={preference_id}, user_id={user_id}")
            
            return {
                "preference_id": preference_id,
                "init_point": response_data.get("init_point"),
                "sandbox_init_point": response_data.get("sandbox_init_point")
            }
        
        except HTTPException:
            raise
        except Exception as exc:
            logger.exception(f"Error creating payment preference for user {user_id}: {str(exc)}")
            raise HTTPException(
                status_code=500,
                detail={
                    "code": "PAYMENT_ERROR",
                    "message": "Error creating payment preference"
                }
            )
    
    def get_payment_status(self, preference_id: str) -> dict:
        """
        Obtiene el estado de un pago por preference_id
        
        Args:
            preference_id: ID de preferencia de Mercado Pago
            
        Returns:
            Información del estado del pago
            
        Raises:
            HTTPException: Si no existe el pago
        """
        payment = self.payment_repo.get_by_preference_id(preference_id)
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        
        return {
            "preference_id": payment.preference_id,
            "status": payment.status,
            "user_id": payment.user_id,
            "amount": payment.amount,
            "currency": payment.currency,
            "created_at": payment.created_at,
            "confirmed_at": payment.confirmed_at
        }
    
    def process_webhook_notification(self, notification: dict) -> dict:
        """
        Procesa notificaciones de webhook de Mercado Pago
        
        Args:
            notification: Diccionario con datos de notificación
            
        Returns:
            Diccionario con resultado del procesamiento
            
        Raises:
            HTTPException: Si hay error al procesar la notificación
        """
        try:
            notification_type = notification.get("type")
            notification_id = notification.get("id")
            
            logger.info(f"Processing webhook notification: type={notification_type}, id={notification_id}")
            
            # Solo procesar notificaciones de pago
            if notification_type != "payment":
                logger.info(f"Ignoring notification type: {notification_type}")
                return {"status": "ignored", "type": notification_type}
            
            # Obtener datos del pago desde MP
            payment_data = notification.get("data", {})
            payment_id = payment_data.get("id")
            
            if not payment_id:
                logger.warning("Webhook notification without payment ID")
                raise HTTPException(
                    status_code=400,
                    detail={"code": "INVALID_WEBHOOK", "message": "No payment ID in notification"}
                )
            
            # Buscar pago en nuestra BD
            payment = self.payment_repo.get_by_payment_id(payment_id)
            
            if not payment:
                # Intentar obtener el pago desde Mercado Pago para sincronizar
                mp_payment = self.mp_client.payment().get(payment_id)
                mp_status = mp_payment.get("status")
                
                if mp_status != 200:
                    logger.warning(f"Could not fetch payment from MP: payment_id={payment_id}")
                    return {"status": "ignored", "reason": "payment_not_found_in_mp", "payment_id": payment_id}
                
                mp_payment_data = mp_payment.get("response", {})
                external_ref = mp_payment_data.get("external_reference", "")
                
                # Buscar por referencia externa
                if external_ref.startswith("user_"):
                    user_id = int(external_ref.replace("user_", ""))
                    payment = self.payment_repo.get_by_user_id(user_id)
                    if payment:
                        payment = payment[0]  # Obtener el más reciente
            
            if not payment:
                logger.warning(f"Payment not found in DB: payment_id={payment_id}")
                return {"status": "ignored", "reason": "payment_not_in_db"}
            
            # Consultar estado completo del pago en MP
            mp_payment_response = self.mp_client.payment().get(payment_id)
            
            if mp_payment_response.get("status") != 200:
                logger.warning(f"Could not fetch payment status from MP: {mp_payment_response}")
                return {"status": "ignored", "reason": "payment_status_unavailable", "payment_id": payment_id}
            
            mp_payment_info = mp_payment_response.get("response", {})
            mp_payment_status = mp_payment_info.get("status")
            
            logger.info(f"Payment status from MP: {mp_payment_status}")
            
            # Actualizar estado del pago
            payment.payment_id = payment_id
            payment.mercadopago_response = json.dumps(mp_payment_info)
            
            # Mapear estado de Mercado Pago a nuestro sistema
            if mp_payment_status == "approved":
                payment.status = "approved"
                payment.confirmed_at = datetime.utcnow()
                logger.info(f"Payment approved: payment_id={payment_id}, user_id={payment.user_id}")
            elif mp_payment_status == "pending":
                payment.status = "pending"
                logger.info(f"Payment pending: payment_id={payment_id}, user_id={payment.user_id}")
            elif mp_payment_status in ["rejected", "cancelled", "refunded"]:
                payment.status = "rejected"
                logger.info(f"Payment rejected/cancelled: payment_id={payment_id}, status={mp_payment_status}")
            
            payment.updated_at = datetime.utcnow()
            self.payment_repo.update(payment)
            
            return {
                "status": "processed",
                "payment_id": payment_id,
                "payment_status": payment.status,
                "user_id": payment.user_id
            }
        
        except HTTPException:
            raise
        except Exception as exc:
            logger.exception(f"Error processing webhook: {str(exc)}")
            raise HTTPException(
                status_code=500,
                detail={"code": "WEBHOOK_ERROR", "message": "Error processing webhook notification"}
            )
