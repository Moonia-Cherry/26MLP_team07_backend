from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue


TaskType = Literal["classification", "regression", "clustering", "anomaly_detection"]
Variant = Literal["base", "optimized"]


class StrictSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class MLBackendStatus(StrictSchema):
    available: bool
    package: str
    detail: str


class HealthResponse(StrictSchema):
    status: Literal["ok"] = "ok"
    ml_backend: MLBackendStatus


class ModelSpec(StrictSchema):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    task_type: TaskType
    variants: list[Variant] = Field(min_length=1)
    parameters: dict[str, JsonValue] = Field(default_factory=dict)


class DatasetSpec(StrictSchema):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    task_type: TaskType


class ExperimentConfig(StrictSchema):
    model: str = Field(min_length=1)
    variant: Variant = "base"
    dataset: str = Field(min_length=1)
    params: dict[str, JsonValue] = Field(default_factory=dict)
    test_size: float = Field(default=0.2, gt=0, lt=1)
    random_state: int = 42


class ExperimentResult(StrictSchema):
    model: str = Field(min_length=1)
    variant: Variant
    dataset: str = Field(min_length=1)
    metrics: dict[str, float | int]
    diagnostics: dict[str, JsonValue] = Field(default_factory=dict)
