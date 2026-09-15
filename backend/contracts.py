from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, FiniteFloat, JsonValue


TaskType = Literal[
    "classification",
    "regression",
    "clustering",
    "anomaly_detection",
]
Variant = Literal["base", "optimized"]


class StrictContract(BaseModel):
    model_config = ConfigDict(extra="forbid")


class MLBackendStatus(StrictContract):
    available: bool
    package: str
    detail: str


class ModelSpec(StrictContract):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    task_type: TaskType
    variants: list[Variant] = Field(min_length=1)
    parameters: dict[str, JsonValue] = Field(default_factory=dict)


class DatasetSpec(StrictContract):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    task_type: TaskType


class ExperimentConfig(StrictContract):
    model: str = Field(min_length=1)
    variant: Variant = "base"
    dataset: str = Field(min_length=1)
    params: dict[str, JsonValue] = Field(default_factory=dict)
    test_size: float = Field(default=0.2, gt=0, lt=1)
    random_state: int = 42


class ExperimentResult(StrictContract):
    model: str = Field(min_length=1)
    variant: Variant
    dataset: str = Field(min_length=1)
    metrics: dict[str, int | FiniteFloat]
    diagnostics: dict[str, JsonValue] = Field(default_factory=dict)
