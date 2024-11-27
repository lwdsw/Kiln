from datetime import datetime
from enum import Enum

from fastapi import FastAPI, HTTPException
from kiln_ai.adapters.fine_tune.base_finetune import FineTuneParameter
from kiln_ai.adapters.fine_tune.finetune_registry import finetune_registry
from kiln_ai.adapters.ml_model_list import (
    ModelProviderName,
    built_in_models,
    provider_enabled,
    provider_name_from_id,
)
from kiln_ai.datamodel import (
    AllDatasetFilter,
    AllSplitDefinition,
    DatasetSplit,
    Finetune,
    HighRatingDatasetFilter,
    Train60Test20Val20SplitDefinition,
    Train80Test20SplitDefinition,
)
from kiln_server.task_api import task_from_id
from pydantic import BaseModel


class FinetuneProviderModel(BaseModel):
    name: str
    id: str


class FinetuneProvider(BaseModel):
    name: str
    id: str
    enabled: bool
    models: list[FinetuneProviderModel]


class DatasetSplitType(Enum):
    TRAIN_TEST = "train_test"
    TRAIN_TEST_VAL = "train_test_val"
    ALL = "all"


api_split_types = {
    DatasetSplitType.TRAIN_TEST: Train80Test20SplitDefinition,
    DatasetSplitType.TRAIN_TEST_VAL: Train60Test20Val20SplitDefinition,
    DatasetSplitType.ALL: AllSplitDefinition,
}


class DatasetFilterType(Enum):
    ALL = "all"
    HIGH_RATING = "high_rating"


api_filter_types = {
    DatasetFilterType.ALL: AllDatasetFilter,
    DatasetFilterType.HIGH_RATING: HighRatingDatasetFilter,
}


class CreateDatasetSplitRequest(BaseModel):
    dataset_split_type: DatasetSplitType
    filter_type: DatasetFilterType
    name: str | None = None
    description: str | None = None


def connect_fine_tune_api(app: FastAPI):
    @app.get("/api/projects/{project_id}/tasks/{task_id}/dataset_splits")
    async def dataset_splits(project_id: str, task_id: str) -> list[DatasetSplit]:
        task = task_from_id(project_id, task_id)
        return task.dataset_splits()

    @app.get("/api/projects/{project_id}/tasks/{task_id}/finetunes")
    async def finetunes(project_id: str, task_id: str) -> list[Finetune]:
        task = task_from_id(project_id, task_id)
        return task.finetunes()

    @app.get("/api/finetune_providers")
    async def finetune_providers() -> list[FinetuneProvider]:
        provider_models: dict[ModelProviderName, list[FinetuneProviderModel]] = {}

        # Collect models by provider
        for model in built_in_models:
            for provider in model.providers:
                if provider.provider_finetune_id:
                    if provider.name not in provider_models:
                        provider_models[provider.name] = []
                    provider_models[provider.name].append(
                        FinetuneProviderModel(
                            name=model.friendly_name, id=provider.provider_finetune_id
                        )
                    )

        # Create provider entries
        providers: list[FinetuneProvider] = []
        for provider_name, models in provider_models.items():
            providers.append(
                FinetuneProvider(
                    name=provider_name_from_id(provider_name),
                    id=provider_name,
                    enabled=await provider_enabled(provider_name),
                    models=models,
                )
            )

        return providers

    @app.get("/api/finetune/hyperparameters/{provider_id}")
    async def finetune_hyperparameters(
        provider_id: str,
    ) -> list[FineTuneParameter]:
        if provider_id not in finetune_registry:
            raise HTTPException(
                status_code=400, detail=f"Fine tune provider '{provider_id}' not found"
            )
        finetune_adapter_class = finetune_registry[provider_id]
        return finetune_adapter_class.available_parameters()

    @app.post("/api/projects/{project_id}/tasks/{task_id}/dataset_splits")
    async def create_dataset_split(
        project_id: str, task_id: str, request: CreateDatasetSplitRequest
    ) -> DatasetSplit:
        task = task_from_id(project_id, task_id)
        split_definitions = api_split_types[request.dataset_split_type]
        filter = api_filter_types[request.filter_type]

        name = request.name
        if not name:
            name = f"{datetime.now().strftime('%Y-%m-%d %H-%M-%S')} filter--{request.filter_type.value} split--{request.dataset_split_type.value}"

        dataset_split = DatasetSplit.from_task(
            name, task, split_definitions, filter, request.description
        )
        dataset_split.save_to_file()
        return dataset_split
