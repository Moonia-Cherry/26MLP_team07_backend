from __future__ import annotations

from dataclasses import asdict, is_dataclass
from importlib import import_module
from types import ModuleType
from typing import Any, Callable, Protocol, Sequence, cast

from pydantic import BaseModel, ValidationError

from backend.interaction.schemas import (
    DatasetSpec,
    ExperimentConfig,
    ExperimentResult,
    MLBackendStatus,
    ModelSpec,
)


class MLBackendError(RuntimeError):
    """Base error understood by the interaction layer."""


class MLBackendUnavailable(MLBackendError):
    """The external package is missing or does not satisfy the public contract."""


class MLRequestError(MLBackendError):
    """The ML package rejected a valid HTTP request for domain reasons."""


class MLExecutionError(MLBackendError):
    """The ML package failed while executing an experiment."""


class MLBackend(Protocol):
    def status(self) -> MLBackendStatus: ...

    def list_models(self) -> list[ModelSpec]: ...

    def list_datasets(self) -> list[DatasetSpec]: ...

    def run_experiment(self, config: ExperimentConfig) -> ExperimentResult: ...


class PackageMLBackend:
    """Call only the stable public API exported by the external ``ml_core`` package."""

    _required_exports = (
        "list_models",
        "list_datasets",
        "run_experiment",
        "ModelSpec",
        "DatasetSpec",
        "ExperimentConfig",
        "ExperimentResult",
    )

    def __init__(
        self,
        package_name: str = "ml_core",
        importer: Callable[[str], ModuleType] = import_module,
    ) -> None:
        self._package_name = package_name
        self._module: ModuleType | None = None
        self._unavailable_reason: str | None = None

        try:
            module = importer(package_name)
        except (ImportError, ModuleNotFoundError) as exc:
            self._unavailable_reason = f"无法导入 {package_name}: {exc}"
            return

        missing = [name for name in self._required_exports if not hasattr(module, name)]
        if missing:
            self._unavailable_reason = (
                f"{package_name} 缺少公共导出: {', '.join(sorted(missing))}"
            )
            return
        self._module = module

    def status(self) -> MLBackendStatus:
        if self._module is None:
            return MLBackendStatus(
                available=False,
                package=self._package_name,
                detail=self._unavailable_reason or "ML package 不可用",
            )
        return MLBackendStatus(
            available=True,
            package=self._package_name,
            detail="ML public package API 已连接",
        )

    def list_models(self) -> list[ModelSpec]:
        values = self._call("list_models")
        return self._validate_sequence(values, ModelSpec, "model")

    def list_datasets(self) -> list[DatasetSpec]:
        values = self._call("list_datasets")
        return self._validate_sequence(values, DatasetSpec, "dataset")

    def run_experiment(self, config: ExperimentConfig) -> ExperimentResult:
        module = self._require_module()
        config_type = cast(Callable[..., Any], getattr(module, "ExperimentConfig"))
        try:
            package_config = config_type(**config.model_dump(mode="python"))
            value = cast(Callable[[Any], Any], getattr(module, "run_experiment"))(
                package_config
            )
            return ExperimentResult.model_validate(self._to_mapping(value))
        except (TypeError, ValueError, ValidationError) as exc:
            raise MLRequestError(str(exc)) from exc
        except Exception as exc:  # package exceptions are isolated at this boundary
            raise MLExecutionError(str(exc)) from exc

    def _call(self, name: str) -> Any:
        module = self._require_module()
        try:
            return cast(Callable[[], Any], getattr(module, name))()
        except (TypeError, ValueError, ValidationError) as exc:
            raise MLRequestError(str(exc)) from exc
        except Exception as exc:  # package exceptions are isolated at this boundary
            raise MLExecutionError(str(exc)) from exc

    def _require_module(self) -> ModuleType:
        if self._module is None:
            raise MLBackendUnavailable(
                self._unavailable_reason or f"{self._package_name} 不可用"
            )
        return self._module

    @classmethod
    def _validate_sequence(
        cls,
        values: Any,
        schema: type[BaseModel],
        item_name: str,
    ) -> list[Any]:
        if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
            raise MLExecutionError(f"ML package 返回的 {item_name} 列表格式无效")
        try:
            return [schema.model_validate(cls._to_mapping(item)) for item in values]
        except (TypeError, ValueError, ValidationError) as exc:
            raise MLExecutionError(
                f"ML package 返回的 {item_name} 数据不符合公共合同: {exc}"
            ) from exc

    @staticmethod
    def _to_mapping(value: Any) -> Any:
        if isinstance(value, BaseModel):
            return value.model_dump(mode="python")
        if is_dataclass(value) and not isinstance(value, type):
            return asdict(value)
        return value
