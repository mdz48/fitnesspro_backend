# Changelog

## [1.3.3] - 2026-03-23
### Cambios
- Se corrigió el filtrado para la API externa y los ENUMs estaban mal

## [1.3.2] - 2026-03-23
### Cambios
- Se corrigió el error con google auth, ahora se puede iniciar sesión con google sin registrarse por completo.

## [1.3.1] - 2026-03-22
### Cambios
- Se corrigieron cosas opciones
- La tabla de user ahora tiene un nuevo campo llamado membership que puede ser gratuito, premium o admin. por defecto es gratuito.
- Se corrigió el error de que no se podían actualizar los campos de los usuarios.

## [1.3.0] - 2026-03-11

### Añadido
- Nuevos endpoints para buscar ejercicios y recetas por nombre.

## [1.2.0] - 2026-03-10

### Añadido
- Nueva feature de los planes de recetas en la base de datos.

## [1.1.0] - 2026-03-09

### Añadido
- Nueva feature de los planes de workout en la base de datos.

## [1.0.4] - 2026-03-09

### Añadido
- Filtro para ejercicios locales por parte del cuerpo, musculo, equipo, dificultad y tipo.

## [1.0.3] - 2026-03-08

### Cambios
- No se estaba cacheando los ejercicios traducidos

## [1.0.2] - 2026-03-08

### Añadido
- Ahora se pueden subir archivos PNG, JPG y JPEG en las recetas. y mp4 en los ejercicios.
- Se le agrego dificultad a los ejercicios.

### Cambios
- Se corrigió el error de que no se pudieran actualizar los campos de las recetas.
- Se corrigió el error de que no se pudieran actualizar los campos de los ejercicios.


## [1.0.1] - 2026-03-08

### Añadido

- **Cálculo de edad automático**: Se eliminó el campo `age` del modelo y esquema de usuarios, y se implementó un cálculo automático basado en la fecha de nacimiento.

### Cambios

- Se eliminó el campo `age` del modelo `User`.
- Se eliminó el campo `age` del esquema `UserBase`.
- Se agregó un cálculo automático de edad en el método `create` del servicio de usuarios.


## [1.0.0] - 2026-03-08

### Añadido

- **Integración con AWS S3**: Implementación de subida de archivos para imágenes de recetas.
- **Soporte Multimedia en Recetas**: Se habilitó la recepción de archivos de imagen (jpg, jpeg, png) vía `multipart/form-data` en el endpoint de creación de recetas.
- **Configuración de S3**: Añadida lógica centralizada en `app/shared/config/s3_files.py` para gestionar la comunicación con AWS.
- **Esquema de Base de Datos**: Actualizado para incluir `image_url` en el modelo y esquema de Recetas.
- **Dependencias**: Se agregaron `boto3` y librerías relacionadas al archivo `requirements.txt`.

### Cambios

- Refactorización de la ruta `POST /recipes` para soportar `Form` y `File` de FastAPI en lugar de solo JSON Raw.
