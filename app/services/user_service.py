"""
Servicio para la lógica de negocio de usuarios
"""
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.User import User
from app.schemas.user_schema import UserCreate, LoginResponse
from app.shared.config.security import get_password_hash, create_access_token, verify_password


class UserService:
    """Servicio para gestionar usuarios"""
    
    @staticmethod
    def create_user(db: Session, user_data: UserCreate) -> User:
        """
        Crea un nuevo usuario
        
        Args:
            db: Sesión de base de datos
            user_data: Datos del usuario a crear
            
        Returns:
            Usuario creado
            
        Raises:
            HTTPException: Si el email ya está registrado
        """
        # Verificar si el email ya existe
        db_user = db.query(User).filter(User.email == user_data.email).first()
        if db_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Hash de la contraseña
        hashed_password = get_password_hash(user_data.password)
        
        # Crear nuevo usuario
        new_user = User(
            email=user_data.email,
            name=user_data.name,
            lastname=user_data.lastname,
            password=hashed_password
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return new_user
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> User:
        """
        Obtiene un usuario por ID
        
        Args:
            db: Sesión de base de datos
            user_id: ID del usuario
            
        Returns:
            Usuario encontrado
            
        Raises:
            HTTPException: Si el usuario no existe
        """
        db_user = db.query(User).filter(User.id == user_id).first()
        if db_user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return db_user
    
    @staticmethod
    def login_user(db: Session, email: str, password: str) -> LoginResponse:
        """
        Autentica un usuario y genera un token de acceso
        
        Args:
            db: Sesión de base de datos
            email: Email del usuario
            password: Contraseña del usuario
            
        Returns:
            Respuesta con datos del usuario y token
            
        Raises:
            HTTPException: Si las credenciales son inválidas
        """
        # Buscar usuario por email
        db_user = db.query(User).filter(User.email == email).first()
        
        # Verificar credenciales
        if not db_user or not verify_password(password, db_user.password):
            raise HTTPException(status_code=400, detail="Invalid credentials")
        
        # Crear token de acceso
        access_token = create_access_token(data={"sub": db_user.email})
        
        return LoginResponse(
            **db_user.__dict__,
            access_token=access_token,
            token_type="bearer"
        )
    
    @staticmethod
    def get_all_users(db: Session, skip: int = 0, limit: int = 10) -> list[User]:
        """
        Obtiene una lista paginada de usuarios
        
        Args:
            db: Sesión de base de datos
            skip: Número de registros a saltar
            limit: Número máximo de registros a retornar
            
        Returns:
            Lista de usuarios
        """
        users = db.query(User).offset(skip).limit(limit).all()
        return users
