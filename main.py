import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.shared.config.database import engine, Base
from app.models.UserProgression import WeightProgress
from app.models.SubscriptionPlan import SubscriptionPlan
from app.models.UserSubscription import UserSubscription
from app.models.SubscriptionPayment import SubscriptionPayment
from app.routes.user_routes import user_router
from app.routes.recipe_routes import recipe_router
from app.routes.list_routes import list_routes
from app.routes.exercise_routes import exercise_router
from app.routes.workout_plan_routes import workout_plan_router
from app.routes.recipe_plan_routes import recipe_plan_router
from app.routes.progression_routes import progression_router
from app.routes.subscription_routes import subscription_router


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

app = FastAPI()

app.include_router(user_router, prefix="/api", tags=["users"])
app.include_router(recipe_router, prefix="/api", tags=["recipes"])
app.include_router(list_routes, prefix="/api", tags=["lists"])
app.include_router(exercise_router, prefix="/api", tags=["exercises"])
app.include_router(workout_plan_router, prefix="/api/workout_plans", tags=["workout_plans"])
app.include_router(recipe_plan_router, prefix="/api/recipe_plans", tags=["recipe_plans"])
app.include_router(progression_router, prefix="/api", tags=["progression"])
app.include_router(subscription_router, prefix="/api", tags=["subscriptions"])


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


Base.metadata.create_all(bind=engine)