from dataclasses import dataclass
from types import ModuleType

import pytest

from backend.integration.ml_backend import (
    MLBackendUnavailable,
    MLExecutionError,
    PackageMLBackend,
)
from backend.interaction.schemas import ExperimentConfig


@dataclass
class PackageExperimentConfig:
    model: str
    variant: str
    dataset: str
    params: dict
    test_size: float
    random_state: int


def _contract_module() -> ModuleType:
    module = ModuleType("ml_core")
    module.ModelSpec = dict
    module.DatasetSpec = dict
    module.ExperimentConfig = PackageExperimentConfig
    module.ExperimentResult = dict
    module.list_models = lambda: [
        {
            "id": "kmeans",
            "name": "K-Means",
            "task_type": "clustering",
            "variants": ["base", "optimized"],
            "parameters": {},
        }
    ]
    module.list_datasets = lambda: [
        {"id": "seeds", "name": "Seeds", "task_type": "clustering"}
    ]
    module.run_experiment = lambda config: {
        "model": config.model,
        "variant": config.variant,
        "dataset": config.dataset,
        "metrics": {"silhouette": 0.61},
        "diagnostics": {"labels": [0, 1, 1]},
    }
    return module


def test_package_boundary_calls_only_public_contract() -> None:
    backend = PackageMLBackend(importer=lambda _name: _contract_module())

    assert backend.status().available is True
    assert backend.list_models()[0].id == "kmeans"
    assert backend.list_datasets()[0].id == "seeds"

    result = backend.run_experiment(
        ExperimentConfig(model="kmeans", dataset="seeds", variant="optimized")
    )
    assert result.metrics["silhouette"] == 0.61


def test_missing_public_export_marks_package_unavailable() -> None:
    incomplete_module = ModuleType("ml_core")
    backend = PackageMLBackend(importer=lambda _name: incomplete_module)

    assert backend.status().available is False
    with pytest.raises(MLBackendUnavailable):
        backend.list_models()


def test_invalid_package_result_is_rejected_at_boundary() -> None:
    module = _contract_module()
    module.list_models = lambda: [{"id": "missing-required-fields"}]
    backend = PackageMLBackend(importer=lambda _name: module)

    with pytest.raises(MLExecutionError):
        backend.list_models()
