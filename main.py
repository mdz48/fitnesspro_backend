from fastapi import FastAPI

from app.routes import user_routes
from app.shared.config.database import engine, Base, SessionLocal

from app.routes.user_routes import user_router
from app.routes.recipie_routes import recipie_router
from app.routes.list_routes import list_routes
from app.routes.exercise_routes import exercise_router

app = FastAPI()

app.include_router(user_router, prefix="/api", tags=["users"])
app.include_router(recipie_router, prefix="/api", tags=["recipes"])
app.include_router(list_routes, prefix="/api", tags=["lists"])
app.include_router(exercise_router, prefix="/api", tags=["exercises"])


Base.metadata.create_all(bind=engine)