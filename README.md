# FitnessPro Backend 🏋️‍♂️🥗

Backend oficial para la aplicación FitnessPro, diseñado para gestionar usuarios, recetas saludables, rutinas de ejercicio y listas personalizadas. Construido con una arquitectura sólida y escalable.

## 🚀 Tecnologías Utilizadas

- **Core:** [FastAPI](https://fastapi.tiangolo.com/)
- **Base de Datos:** [MySQL](https://www.mysql.com/)
- **ORM:** [SQLAlchemy](https://www.sqlalchemy.org/)
- **Almacenamiento:** [AWS S3](https://aws.amazon.com/s3/) (para imágenes de recetas)
- **Seguridad:** JWT (JSON Web Tokens) & Passlib (Bcrypt)

## 📋 Requisitos Previos

- Python 3.10+
- Servidor MySQL
- Cuenta de AWS (para configuración de S3)

## 🛠️ Configuración e Instalación

1. **Clonar el repositorio:**

   ```bash
   git clone <url-del-repositorio>
   cd fitnesspro_backend
   ```

2. **Crear y activar un entorno virtual:**

   ```bash
   # Windows
   python -m venv .venv
   .\.venv\Scripts\activate

   # Linux/macOS
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Instalar dependencias:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno:**
   Copia el archivo `.env.example` a `.env` y completa tus credenciales:
   ```bash
   cp .env.example .env
   ```
   Asegúrate de configurar:
   - Conexión a la base de Datos.
   - Credenciales de AWS (Key ID, Secret Access Key).
   - Nombre del bucket de S3.

## 🖥️ Ejecución del Servidor

Para iniciar el servidor en modo desarrollo con recarga automática:

```bash
uvicorn main:app --reload
```

El servidor estará disponible en `http://127.0.0.1:8000`.
Puedes acceder a la documentación interactiva de la API en:

- **Swagger UI:** `http://127.0.0.1:8000/docs`
- **ReDoc:** `http://127.0.0.1:8000/redoc`

## 📁 Estructura del Proyecto

- `app/models/`: Definiciones de tablas de SQLAlchemy.
- `app/schemas/`: Modelos de validación de Pydantic.
- `app/routes/`: Definición de endpoints de la API.
- `app/services/`: Lógica de negocio.
- `app/repositories/`: Capa de acceso a datos.
- `app/shared/config/`: Configuraciones de base de datos, S3, etc.
