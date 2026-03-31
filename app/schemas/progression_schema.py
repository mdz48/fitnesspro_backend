from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal


class WeightProgressCreate(BaseModel):
    weight: float = Field(gt=0)


class WeightProgressResponse(BaseModel):
    id: int
    user_id: int
    weight: float
    date: datetime

    model_config = ConfigDict(from_attributes=True)


class WeightProgressSummary(BaseModel):
    user_id: int
    goal: Literal["bajar", "mantener", "subir"] | None = None
    initial_weight: float | None = None
    current_weight: float | None = None
    weight_change: float | None = None
    entries_count: int = 0
    on_track: bool | None = None

    model_config = ConfigDict(from_attributes=True)
