# Changelog

Todos los cambios notables en este proyecto serán documentados en este archivo.



## [1.0.0] - 2026-03-05

### Añadido

- **Integración con AWS S3**: Implementación de subida de archivos para imágenes de recetas.
- **Soporte Multimedia en Recetas**: Se habilitó la recepción de archivos de imagen (jpg, jpeg, png) vía `multipart/form-data` en el endpoint de creación de recetas.
- **Configuración de S3**: Añadida lógica centralizada en `app/shared/config/s3_files.py` para gestionar la comunicación con AWS.
- **Esquema de Base de Datos**: Actualizado para incluir `image_url` en el modelo y esquema de Recetas.
- **Dependencias**: Se agregaron `boto3` y librerías relacionadas al archivo `requirements.txt`.

### Cambios

- Refactorización de la ruta `POST /recipes` para soportar `Form` y `File` de FastAPI en lugar de solo JSON Raw.
