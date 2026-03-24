"""
Servicio para la lógica de negocio de usuarios
"""
import os
import logging
from pathlib import Path
from fastapi import HTTPException
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2 import id_token
from app.models.User import User
from app.schemas.user_schema import UserCreate, UserUpdate, LoginResponse
from app.repositories.user_repository import UserRepository
from app.core.security_service import SecurityService

logger = logging.getLogger(__name__)

ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=ENV_PATH)


class UserService:
    """Servicio para gestionar usuarios con DI"""
    
    def __init__(self, repository: UserRepository, security: SecurityService):
        """
        Inicializa el servicio con sus dependencias
        
        Args:
            repository: Repositorio de usuarios
            security: Servicio de seguridad
        """
        self.repository = repository
        self.security = security

    def _normalize_membership(self, membership: str | None) -> str | None:
        if membership == "free":
            return "gratuito"
        return membership

    def _sync_google_profile(self, user: User, token_info: dict) -> bool:
        """Sincroniza campos disponibles de Google con el usuario local."""
        new_name = token_info.get("given_name") or token_info.get("name")
        new_lastname = token_info.get("family_name")

        changed = False
        if new_name and user.name != new_name:
            user.name = new_name
            changed = True
        if new_lastname and user.lastname != new_lastname:
            user.lastname = new_lastname
            changed = True

        return changed
    
    def create_user(self, user_data: UserCreate) -> User:
        """
        Crea un nuevo usuario
        
        Args:
            user_data: Datos del usuario a crear
            
        Returns:
            Usuario creado
            
        Raises:
            HTTPException: Si el email ya está registrado
        """
        # Verificar si el email ya existe
        if self.repository.email_exists(user_data.email):
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Hash de la contraseña (opcional para cuentas OAuth/híbridas)
        hashed_password = None
        if user_data.password:
            hashed_password = self.security.get_password_hash(user_data.password)
        
        # Crear nuevo usuario
        normalized_membership = self._normalize_membership(user_data.membership)

        new_user = User(
            email=user_data.email,
            name=user_data.name,
            lastname=user_data.lastname,
            password=hashed_password,
            birthdate=user_data.birthdate,
            weight=user_data.weight,
            height=user_data.height,
            gender=user_data.gender,
            weight_goal=user_data.weight_goal,
            membership=normalized_membership
        )
        
        return self.repository.create(new_user)
    
    def get_user_by_id(self, user_id: int) -> User:
        """
        Obtiene un usuario por ID
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Usuario encontrado
            
        Raises:
            HTTPException: Si el usuario no existe
        """
        user = self.repository.get_by_id(user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    
    def login_user(self, email: str, password: str) -> LoginResponse:
        """
        Autentica un usuario y genera un token de acceso
        
        Args:
            email: Email del usuario
            password: Contraseña del usuario
            
        Returns:
            Respuesta con datos del usuario y token
            
        Raises:
            HTTPException: Si las credenciales son inválidas
        """
        # Buscar usuario por email
        user = self.repository.get_by_email(email)
        
        # Verificar credenciales
        if not user or not user.password or not self.security.verify_password(password, user.password):
            raise HTTPException(status_code=400, detail="Invalid credentials")
        
        # Crear token de acceso
        access_token = self.security.create_access_token(data={"sub": user.email})
        
        return LoginResponse(
            **user.__dict__,
            access_token=access_token,
            token_type="bearer"
        )

    def login_google_user(self, google_id_token: str) -> LoginResponse:
        """
        Autentica un usuario usando Google ID Token.

        Si el usuario no existe, solicita completar registro en lugar de crear
        un usuario con datos estáticos.
        """
        google_client_id = os.getenv("GOOGLE_CLIENT_ID")
        debug_google_auth = os.getenv("GOOGLE_AUTH_DEBUG", "false").lower() == "true"

        if not google_client_id:
            logger.error(
                "Google auth misconfigured: GOOGLE_CLIENT_ID is missing | env_path=%s | env_exists=%s",
                str(ENV_PATH),
                ENV_PATH.exists()
            )
            raise HTTPException(
                status_code=500,
                detail={
                    "code": "GOOGLE_CONFIG_MISSING",
                    "message": "Google auth is not configured"
                }
            )

        try:
            token_info = id_token.verify_oauth2_token(
                google_id_token,
                Request(),
                google_client_id
            )
        except ValueError as exc:
            logger.exception("Google token validation failed")
            detail = {
                "code": "INVALID_GOOGLE_TOKEN",
                "message": "Invalid Google token"
            }
            if debug_google_auth:
                detail["debug"] = str(exc)
            raise HTTPException(status_code=400, detail=detail)
        except Exception as exc:
            logger.exception("Unexpected Google auth error")
            detail = {
                "code": "GOOGLE_AUTH_ERROR",
                "message": "Google authentication failed"
            }
            if debug_google_auth:
                detail["debug"] = str(exc)
            raise HTTPException(status_code=500, detail=detail)

        email = token_info.get("email")
        if not email:
            logger.warning("Google token without email claim")
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "GOOGLE_TOKEN_WITHOUT_EMAIL",
                    "message": "Google token without email"
                }
            )

        if token_info.get("email_verified") is False:
            logger.warning("Google token email not verified", extra={"email": email})
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "GOOGLE_EMAIL_NOT_VERIFIED",
                    "message": "Google email is not verified"
                }
            )

        user = self.repository.get_by_email(email)

        if user is None:
            logger.info("Creating user from Google OAuth", extra={"email": email})
            user = User(
                email=email,
                name=token_info.get("given_name") or token_info.get("name"),
                lastname=token_info.get("family_name"),
                password=None,
                birthdate=None,
                weight=None,
                height=None,
                gender=None,
                weight_goal=None,
                membership="gratuito"
            )
            user = self.repository.create(user)
        else:
            if self._sync_google_profile(user, token_info):
                user = self.repository.update(user)

        access_token = self.security.create_access_token(data={"sub": user.email})

        return LoginResponse(
            **user.__dict__,
            access_token=access_token,
            token_type="bearer"
        )
    
    def get_all_users(self) -> list[User]:
        """
        Obtiene la lista de usuarios
            
        Returns:
            Lista de usuarios
        """
        return self.repository.get_all()

    def update_user(self, user_id: int, user_data: UserUpdate) -> User:
        """
        Actualiza un usuario existente

        Args:
            user_id: ID del usuario a actualizar
            user_data: Datos del usuario a actualizar

        Returns:
            Usuario actualizado

        Raises:
            HTTPException: Si el usuario no existe o el email ya está en uso
        """
        user = self.repository.get_by_id(user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        data_to_update = user_data.model_dump(exclude_unset=True)

        new_email = data_to_update.get("email")
        if new_email and new_email != user.email:
            existing_user = self.repository.get_by_email(new_email)
            if existing_user and existing_user.id != user_id:
                raise HTTPException(status_code=400, detail="Email already registered")

        new_password = data_to_update.pop("password", None)
        if new_password is not None:
            user.password = self.security.get_password_hash(new_password)

        if "membership" in data_to_update:
            data_to_update["membership"] = self._normalize_membership(data_to_update.get("membership"))

        for key, value in data_to_update.items():
            if value is not None:
                setattr(user, key, value)

        return self.repository.update(user)
