# AGENTS.md

## Descripción del Proyecto
Este proyecto es una API REST construida con FastAPI y Python.

## Reglas de Codificación
- Usar type hinting en todas las funciones.
- Comentarios en formato docstring.
- Seguir la estructura de carpetas `app/services`, `app/models`.
- Librerias nuevas deben incluirse en `requirements.txt` y documentarse en el changelog.md.

## Arquitectura
- `app/services`: Lógica de negocio.
- `app/models`: Definición de modelos de datos.
- `main.py`: Punto de entrada de la aplicación.
- `app/shared`: Funciones y utilidades comunes.
- `app/schemas`: Esquemas de validación de datos.
- `app/routes`: Definición de rutas y endpoints.
- `app/repositories`: Interacción con la base de datos.

## Comandos Técnicos
- Tests: `pytest`
- Ejecutar: `uvicorn main:app --reload`

## Límite de Acciones
- No modificar el archivo `.env`.

## Reglas de Interacción
- Modificar changelog.md para documentar cambios significativos.
- Mantener la comunicación clara y concisa en los comentarios y documentación.
- Seguir las mejores prácticas de desarrollo de software y diseño de API REST.

## Reglas de comunicación
- Si hay una implementacion compleja entre Backend y Frontend, se debe documentar en CONTEXTO_FRONT.MD para que el equipo de Frontend pueda entender la lógica y cómo interactuar con la API.

## Reglas con APIs externas
- Documentar cualquier cambio en la forma en que se interactúa con APIs externas en el changelog.md.
- Las APIs externas deben ser encapsuladas en servicios dentro de `app/services` para mantener una separación clara de responsabilidades.
- Las apis tienen que pasar por el servicio de cache para evitar llamadas innecesarias a la API externa.
- Es obligatorio el uso de caché para las llamadas a APIs externas, con un TTL de 24 horas, para mejorar el rendimiento y reducir la carga en las APIs externas.