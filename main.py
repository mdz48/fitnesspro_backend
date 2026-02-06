from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.shared.config.database import engine, Base
from app.routes.user_routes import user_router
from app.routes.recipe_routes import recipe_router
from app.routes.list_routes import list_routes
from app.routes.exercise_routes import exercise_router

app = FastAPI()

app.include_router(user_router, prefix="/api", tags=["users"])
app.include_router(recipe_router, prefix="/api", tags=["recipes"])
app.include_router(list_routes, prefix="/api", tags=["lists"])
app.include_router(exercise_router, prefix="/api", tags=["exercises"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


Base.metadata.create_all(bind=engine)