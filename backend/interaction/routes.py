from fastapi import APIRouter, Depends, HTTPException, Request, status

from backend.integration.ml_backend import (
    MLBackend,
    MLBackendUnavailable,
    MLExecutionError,
    MLRequestError,
)
from backend.interaction.schemas import (
    DatasetSpec,
    ExperimentConfig,
    ExperimentResult,
    HealthResponse,
    ModelSpec,
)


router = APIRouter(prefix="/api")


def get_ml_backend(request: Request) -> MLBackend:
    return request.app.state.ml_backend


def _translate_error(exc: Exception) -> HTTPException:
    if isinstance(exc, MLBackendUnavailable):
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "ml_backend_unavailable", "message": str(exc)},
        )
    if isinstance(exc, MLRequestError):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "ml_request_rejected", "message": str(exc)},
        )
    return HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail={"code": "ml_execution_failed", "message": str(exc)},
    )


@router.get("/health", response_model=HealthResponse)
def health(backend: MLBackend = Depends(get_ml_backend)) -> HealthResponse:
    return HealthResponse(ml_backend=backend.status())


@router.get("/models", response_model=list[ModelSpec])
def list_models(backend: MLBackend = Depends(get_ml_backend)) -> list[ModelSpec]:
    try:
        return backend.list_models()
    except (MLBackendUnavailable, MLRequestError, MLExecutionError) as exc:
        raise _translate_error(exc) from exc


@router.get("/datasets", response_model=list[DatasetSpec])
def list_datasets(backend: MLBackend = Depends(get_ml_backend)) -> list[DatasetSpec]:
    try:
        return backend.list_datasets()
    except (MLBackendUnavailable, MLRequestError, MLExecutionError) as exc:
        raise _translate_error(exc) from exc


@router.post("/experiments", response_model=ExperimentResult)
def run_experiment(
    config: ExperimentConfig,
    backend: MLBackend = Depends(get_ml_backend),
) -> ExperimentResult:
    try:
        return backend.run_experiment(config)
    except (MLBackendUnavailable, MLRequestError, MLExecutionError) as exc:
        raise _translate_error(exc) from exc
