"""
Ejemplos de tests con la nueva arquitectura basada en DI
Estos tests demuestran cómo la inyección de dependencias facilita el testing
"""
import pytest
from unittest.mock import Mock, MagicMock
from app.services.user_service import UserService
from app.services.recipe_service import RecipeService
from app.repositories.user_repository import UserRepository
from app.repositories.recipe_repository import RecipeRepository
from app.core.security_service import SecurityService
from app.models.User import User
from app.models.Recipe import Recipe
from app.schemas.user_schema import UserCreate
from app.schemas.recipe_schema import RecipeCreate
from fastapi import HTTPException


# ============================================================================
# TESTS DE USER SERVICE
# ============================================================================

class TestUserService:
    """Tests para UserService usando mocks inyectados"""
    
    def test_create_user_success(self):
        """Test exitoso de creación de usuario"""
        # Arrange: Configurar mocks
        mock_repository = Mock(spec=UserRepository)
        mock_security = Mock(spec=SecurityService)
        
        # Configurar comportamiento de mocks
        mock_repository.email_exists.return_value = False
        mock_security.get_password_hash.return_value = "hashed_password_123"
        mock_repository.create.return_value = User(
            id=1,
            email="test@example.com",
            name="Test",
            lastname="User",
            password="hashed_password_123"
        )
        
        # Inyectar mocks en el servicio
        service = UserService(mock_repository, mock_security)
        
        # Datos de entrada
        user_data = UserCreate(
            email="test@example.com",
            name="Test",
            lastname="User",
            password="secret123"
        )
        
        # Act: Ejecutar el método
        result = service.create_user(user_data)
        
        # Assert: Verificar resultados
        assert result.id == 1
        assert result.email == "test@example.com"
        assert result.password == "hashed_password_123"
        
        # Verificar que se llamaron los métodos correctos
        mock_repository.email_exists.assert_called_once_with("test@example.com")
        mock_security.get_password_hash.assert_called_once_with("secret123")
        mock_repository.create.assert_called_once()
    
    def test_create_user_email_already_exists(self):
        """Test cuando el email ya está registrado"""
        # Arrange
        mock_repository = Mock(spec=UserRepository)
        mock_security = Mock(spec=SecurityService)
        
        # Simular que el email ya existe
        mock_repository.email_exists.return_value = True
        
        service = UserService(mock_repository, mock_security)
        user_data = UserCreate(
            email="existing@example.com",
            name="Test",
            lastname="User",
            password="secret123"
        )
        
        # Act & Assert: Verificar que lanza excepción
        with pytest.raises(HTTPException) as exc_info:
            service.create_user(user_data)
        
        assert exc_info.value.status_code == 400
        assert "Email already registered" in str(exc_info.value.detail)
        
        # Verificar que NO se intentó crear el usuario
        mock_repository.create.assert_not_called()
        mock_security.get_password_hash.assert_not_called()
    
    def test_get_user_by_id_success(self):
        """Test exitoso de obtener usuario por ID"""
        # Arrange
        mock_repository = Mock(spec=UserRepository)
        mock_security = Mock(spec=SecurityService)
        
        expected_user = User(
            id=1,
            email="test@example.com",
            name="Test",
            lastname="User",
            password="hashed"
        )
        mock_repository.get_by_id.return_value = expected_user
        
        service = UserService(mock_repository, mock_security)
        
        # Act
        result = service.get_user_by_id(1)
        
        # Assert
        assert result == expected_user
        mock_repository.get_by_id.assert_called_once_with(1)
    
    def test_get_user_by_id_not_found(self):
        """Test cuando el usuario no existe"""
        # Arrange
        mock_repository = Mock(spec=UserRepository)
        mock_security = Mock(spec=SecurityService)
        
        mock_repository.get_by_id.return_value = None
        
        service = UserService(mock_repository, mock_security)
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            service.get_user_by_id(999)
        
        assert exc_info.value.status_code == 404
        assert "User not found" in str(exc_info.value.detail)
    
    def test_login_user_success(self):
        """Test exitoso de login"""
        # Arrange
        mock_repository = Mock(spec=UserRepository)
        mock_security = Mock(spec=SecurityService)
        
        stored_user = User(
            id=1,
            email="test@example.com",
            name="Test",
            lastname="User",
            password="hashed_password"
        )
        mock_repository.get_by_email.return_value = stored_user
        mock_security.verify_password.return_value = True
        mock_security.create_access_token.return_value = "jwt_token_xyz"
        
        service = UserService(mock_repository, mock_security)
        
        # Act
        result = service.login_user("test@example.com", "correct_password")
        
        # Assert
        assert result.access_token == "jwt_token_xyz"
        assert result.token_type == "bearer"
        assert result.email == "test@example.com"
        
        mock_repository.get_by_email.assert_called_once_with("test@example.com")
        mock_security.verify_password.assert_called_once_with("correct_password", "hashed_password")
        mock_security.create_access_token.assert_called_once()
    
    def test_login_user_invalid_credentials(self):
        """Test login con credenciales inválidas"""
        # Arrange
        mock_repository = Mock(spec=UserRepository)
        mock_security = Mock(spec=SecurityService)
        
        stored_user = User(
            id=1,
            email="test@example.com",
            name="Test",
            lastname="User",
            password="hashed_password"
        )
        mock_repository.get_by_email.return_value = stored_user
        mock_security.verify_password.return_value = False  # Password incorrecto
        
        service = UserService(mock_repository, mock_security)
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            service.login_user("test@example.com", "wrong_password")
        
        assert exc_info.value.status_code == 400
        assert "Invalid credentials" in str(exc_info.value.detail)


# ============================================================================
# TESTS DE RECIPE SERVICE
# ============================================================================

class TestRecipeService:
    """Tests para RecipeService usando mocks inyectados"""
    
    def test_create_recipe_success(self):
        """Test exitoso de creación de receta"""
        # Arrange
        mock_repository = Mock(spec=RecipeRepository)
        
        recipe_data = RecipeCreate(
            name="Pasta Carbonara",
            description="Delicious Italian pasta",
            instructions="Cook pasta, mix with eggs and bacon",
            ingredients="Pasta, eggs, bacon, cheese",
            portions=4,
            user_id=1
        )
        
        expected_recipe = Recipe(
            id=1,
            name="Pasta Carbonara",
            description="Delicious Italian pasta",
            instructions="Cook pasta, mix with eggs and bacon",
            ingredients="Pasta, eggs, bacon, cheese",
            portions=4,
            user_id=1
        )
        mock_repository.create.return_value = expected_recipe
        
        service = RecipeService(mock_repository)
        
        # Act
        result = service.create_recipe(recipe_data)
        
        # Assert
        assert result.id == 1
        assert result.name == "Pasta Carbonara"
        mock_repository.create.assert_called_once()
    
    def test_get_recipe_by_id_success(self):
        """Test exitoso de obtener receta por ID"""
        # Arrange
        mock_repository = Mock(spec=RecipeRepository)
        
        expected_recipe = Recipe(
            id=1,
            name="Pasta Carbonara",
            description="Delicious",
            instructions="Cook it",
            ingredients="pasta, eggs",
            portions=4,
            user_id=1
        )
        mock_repository.get_by_id.return_value = expected_recipe
        
        service = RecipeService(mock_repository)
        
        # Act
        result = service.get_recipe_by_id(1)
        
        # Assert
        assert result == expected_recipe
        mock_repository.get_by_id.assert_called_once_with(1)
    
    def test_delete_recipe_success(self):
        """Test exitoso de eliminación de receta"""
        # Arrange
        mock_repository = Mock(spec=RecipeRepository)
        
        existing_recipe = Recipe(id=1, name="Test Recipe")
        mock_repository.get_by_id.return_value = existing_recipe
        
        service = RecipeService(mock_repository)
        
        # Act
        service.delete_recipe(1)
        
        # Assert
        mock_repository.get_by_id.assert_called_once_with(1)
        mock_repository.delete.assert_called_once_with(existing_recipe)
    
    def test_delete_recipe_not_found(self):
        """Test eliminación de receta que no existe"""
        # Arrange
        mock_repository = Mock(spec=RecipeRepository)
        mock_repository.get_by_id.return_value = None
        
        service = RecipeService(mock_repository)
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            service.delete_recipe(999)
        
        assert exc_info.value.status_code == 404
        assert "Recipe not found" in str(exc_info.value.detail)
        mock_repository.delete.assert_not_called()
    
    def test_update_recipe_success(self):
        """Test exitoso de actualización de receta"""
        # Arrange
        mock_repository = Mock(spec=RecipeRepository)
        
        existing_recipe = Recipe(
            id=1,
            name="Old Name",
            description="Old Description",
            instructions="Old Instructions",
            ingredients="Old Ingredients",
            portions=2,
            user_id=1
        )
        mock_repository.get_by_id.return_value = existing_recipe
        
        updated_data = RecipeCreate(
            name="New Name",
            description="New Description",
            instructions="New Instructions",
            ingredients="New Ingredients",
            portions=4,
            user_id=1
        )
        
        mock_repository.update.return_value = existing_recipe  # Retorna la receta actualizada
        
        service = RecipeService(mock_repository)
        
        # Act
        result = service.update_recipe(1, updated_data)
        
        # Assert
        mock_repository.get_by_id.assert_called_once_with(1)
        mock_repository.update.assert_called_once_with(existing_recipe)
        # Verificar que los atributos se actualizaron
        assert existing_recipe.name == "New Name"
        assert existing_recipe.portions == 4
    
    def test_get_recipes_by_user(self):
        """Test obtener recetas de un usuario"""
        # Arrange
        mock_repository = Mock(spec=RecipeRepository)
        
        user_recipes = [
            Recipe(id=1, name="Recipe 1", user_id=1),
            Recipe(id=2, name="Recipe 2", user_id=1),
            Recipe(id=3, name="Recipe 3", user_id=1),
        ]
        mock_repository.get_by_user.return_value = user_recipes
        
        service = RecipeService(mock_repository)
        
        # Act
        result = service.get_recipes_by_user(1)
        
        # Assert
        assert len(result) == 3
        assert all(recipe.user_id == 1 for recipe in result)
        mock_repository.get_by_user.assert_called_once_with(1)


# ============================================================================
# EJEMPLO DE INTEGRACIÓN: Testing de Endpoint Completo
# ============================================================================

def test_create_user_endpoint_integration():
    """
    Ejemplo de cómo testear un endpoint completo inyectando mocks.
    Este test simula una petición HTTP sin necesidad de levantar el servidor.
    """
    from fastapi.testclient import TestClient
    from app.main import app
    from app.core.dependencies import get_user_service
    
    # Crear mock del servicio
    mock_service = Mock(spec=UserService)
    mock_service.create_user.return_value = User(
        id=1,
        email="test@example.com",
        name="Test",
        lastname="User",
        password="hashed"
    )
    
    # Override de la dependencia para usar el mock
    app.dependency_overrides[get_user_service] = lambda: mock_service
    
    # Cliente de test
    client = TestClient(app)
    
    # Hacer request
    response = client.post("/api/users", json={
        "email": "test@example.com",
        "name": "Test",
        "lastname": "User",
        "password": "secret123"
    })
    
    # Verificar respuesta
    assert response.status_code == 201
    assert response.json()["email"] == "test@example.com"
    
    # Verificar que el servicio fue llamado
    mock_service.create_user.assert_called_once()
    
    # Limpiar override
    app.dependency_overrides.clear()


# ============================================================================
# FIXTURE EXAMPLES (para pytest)
# ============================================================================

@pytest.fixture
def mock_user_repository():
    """Fixture reutilizable para UserRepository"""
    return Mock(spec=UserRepository)


@pytest.fixture
def mock_security_service():
    """Fixture reutilizable para SecurityService"""
    return Mock(spec=SecurityService)


@pytest.fixture
def user_service(mock_user_repository, mock_security_service):
    """Fixture que provee UserService con mocks inyectados"""
    return UserService(mock_user_repository, mock_security_service)


def test_example_using_fixtures(user_service, mock_user_repository):
    """Ejemplo usando fixtures de pytest"""
    # Configurar comportamiento del mock
    mock_user_repository.get_by_id.return_value = User(id=1, email="test@test.com")
    
    # Usar el servicio
    user = user_service.get_user_by_id(1)
    
    # Verificar
    assert user.id == 1
    mock_user_repository.get_by_id.assert_called_once_with(1)


# ============================================================================
# EJECUTAR TESTS
# ============================================================================
"""
Para ejecutar estos tests:

1. Instalar pytest:
   pip install pytest pytest-cov

2. Ejecutar todos los tests:
   pytest tests/test_services_with_di.py -v

3. Ejecutar con cobertura:
   pytest tests/test_services_with_di.py --cov=app --cov-report=html

4. Ejecutar un test específico:
   pytest tests/test_services_with_di.py::TestUserService::test_create_user_success -v
"""
