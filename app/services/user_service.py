"""
Servicio para la lógica de negocio de usuarios
"""
from fastapi import HTTPException
from app.models.User import User
from app.schemas.user_schema import UserCreate, LoginResponse
from app.repositories.user_repository import UserRepository
from app.core.security_service import SecurityService


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
        
        # Hash de la contraseña
        hashed_password = self.security.get_password_hash(user_data.password)
        
        # Crear nuevo usuario
        new_user = User(
            email=user_data.email,
            name=user_data.name,
            lastname=user_data.lastname,
            password=hashed_password,
            birthdate=user_data.birthdate,
            weight=user_data.weight,
            height=user_data.height,
            gender=user_data.gender
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
        if not user or not self.security.verify_password(password, user.password):
            raise HTTPException(status_code=400, detail="Invalid credentials")
        
        # Crear token de acceso
        access_token = self.security.create_access_token(data={"sub": user.email})
        
        return LoginResponse(
            **user.__dict__,
            access_token=access_token,
            token_type="bearer"
        )
    
    def get_all_users(self, skip: int = 0, limit: int = 10) -> list[User]:
        """
        Obtiene una lista paginada de usuarios
        
        Args:
            skip: Número de registros a saltar
            limit: Número máximo de registros a retornar
            
        Returns:
            Lista de usuarios
        """
        return self.repository.get_all(skip, limit)
