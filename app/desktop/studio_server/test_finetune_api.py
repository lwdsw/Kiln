import unittest.mock
from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from kiln_ai.adapters.fine_tune.base_finetune import FineTuneParameter
from kiln_ai.adapters.ml_model_list import KilnModel, KilnModelProvider
from kiln_ai.datamodel import AllSplitDefinition, DatasetSplit, Finetune

from app.desktop.studio_server.finetune_api import connect_fine_tune_api


@pytest.fixture
def mock_task():
    task = Mock()
    task.dataset_splits.return_value = [
        DatasetSplit(
            id="split1",
            name="Split 1",
            split_contents={"train": ["1", "2"]},
            splits=AllSplitDefinition,
        ),
        DatasetSplit(
            id="split2",
            name="Split 2",
            split_contents={"test": ["3"]},
            splits=AllSplitDefinition,
        ),
    ]
    task.finetunes.return_value = [
        Finetune(
            id="ft1",
            name="Finetune 1",
            provider="openai",
            base_model_id="model1",
            dataset_split_id="split1",
            system_message="System prompt 1",
        ),
        Finetune(
            id="ft2",
            name="Finetune 2",
            provider="openai",
            base_model_id="model2",
            dataset_split_id="split2",
            system_message="System prompt 2",
        ),
    ]
    return task


@pytest.fixture
def mock_task_from_id(mock_task, monkeypatch):
    mock_func = Mock(return_value=mock_task)
    monkeypatch.setattr(
        "app.desktop.studio_server.finetune_api.task_from_id", mock_func
    )
    return mock_func


@pytest.fixture
def client():
    app = FastAPI()
    connect_fine_tune_api(app)
    return TestClient(app)


def test_get_dataset_splits(client, mock_task_from_id, mock_task):
    response = client.get("/api/projects/project1/tasks/task1/dataset_splits")

    assert response.status_code == 200
    splits = response.json()
    assert len(splits) == 2
    assert splits[0]["id"] == "split1"
    assert splits[1]["id"] == "split2"

    mock_task_from_id.assert_called_once_with("project1", "task1")
    mock_task.dataset_splits.assert_called_once()


def test_get_finetunes(client, mock_task_from_id, mock_task):
    response = client.get("/api/projects/project1/tasks/task1/finetunes")

    assert response.status_code == 200
    finetunes = response.json()
    assert len(finetunes) == 2
    assert finetunes[0]["id"] == "ft1"
    assert finetunes[1]["id"] == "ft2"

    mock_task_from_id.assert_called_once_with("project1", "task1")
    mock_task.finetunes.assert_called_once()


@pytest.fixture
def mock_built_in_models():
    models = [
        KilnModel(
            name="model1",
            family="family1",
            friendly_name="Model 1",
            providers=[
                KilnModelProvider(name="groq", provider_finetune_id="ft_model1"),
                KilnModelProvider(name="openai", provider_finetune_id="ft_model1_p2"),
            ],
        ),
        KilnModel(
            name="model2",
            family="family2",
            friendly_name="Model 2",
            providers=[
                KilnModelProvider(name="groq", provider_finetune_id="ft_model2"),
                KilnModelProvider(
                    name="openai",
                    provider_finetune_id=None,  # This one should be skipped
                ),
            ],
        ),
    ]
    with unittest.mock.patch(
        "app.desktop.studio_server.finetune_api.built_in_models", models
    ):
        yield models


@pytest.fixture
def mock_provider_enabled():
    async def mock_enabled(provider: str) -> bool:
        return provider == "groq"

    mock = Mock()
    mock.side_effect = mock_enabled

    with unittest.mock.patch(
        "app.desktop.studio_server.finetune_api.provider_enabled", mock
    ):
        yield mock


@pytest.fixture
def mock_provider_name_from_id():
    def mock_name(provider_id: str) -> str:
        return f"Provider {provider_id.replace('provider', '')}"

    with unittest.mock.patch(
        "app.desktop.studio_server.finetune_api.provider_name_from_id", mock_name
    ):
        yield mock_name


async def test_get_finetune_providers(
    client, mock_built_in_models, mock_provider_name_from_id, mock_provider_enabled
):
    response = client.get("/api/finetune_providers")

    assert response.status_code == 200
    providers = response.json()
    assert len(providers) == 2

    # Check provider1
    provider1 = next(p for p in providers if p["id"] == "groq")
    assert provider1["name"] == "Provider groq"
    assert provider1["enabled"] is True
    assert len(provider1["models"]) == 2
    assert provider1["models"][0]["name"] == "Model 1"
    assert provider1["models"][0]["id"] == "ft_model1"
    assert provider1["models"][1]["name"] == "Model 2"
    assert provider1["models"][1]["id"] == "ft_model2"

    # Check provider2
    provider2 = next(p for p in providers if p["id"] == "openai")
    assert provider2["name"] == "Provider openai"
    assert provider2["enabled"] is False
    assert len(provider2["models"]) == 1
    assert provider2["models"][0]["name"] == "Model 1"
    assert provider2["models"][0]["id"] == "ft_model1_p2"


@pytest.fixture
def mock_finetune_registry():
    mock_adapter = Mock()
    mock_adapter.available_parameters.return_value = [
        FineTuneParameter(
            name="learning_rate",
            type="float",
            description="Learning rate for training",
            optional=True,
        ),
        FineTuneParameter(
            name="epochs",
            type="int",
            description="Number of training epochs",
            optional=False,
        ),
    ]

    mock_registry = {"test_provider": mock_adapter}

    with unittest.mock.patch(
        "app.desktop.studio_server.finetune_api.finetune_registry", mock_registry
    ):
        yield mock_registry


def test_get_finetune_hyperparameters(client, mock_finetune_registry):
    response = client.get("/api/finetune/hyperparameters/test_provider")

    assert response.status_code == 200
    parameters = response.json()
    assert len(parameters) == 2

    assert parameters[0]["name"] == "learning_rate"
    assert parameters[0]["type"] == "float"
    assert parameters[0]["description"] == "Learning rate for training"
    assert parameters[0]["optional"] is True

    assert parameters[1]["name"] == "epochs"
    assert parameters[1]["type"] == "int"
    assert parameters[1]["description"] == "Number of training epochs"
    assert parameters[1]["optional"] is False


def test_get_finetune_hyperparameters_invalid_provider(client, mock_finetune_registry):
    response = client.get("/api/finetune/hyperparameters/invalid_provider")

    assert response.status_code == 400
    assert (
        response.json()["detail"] == "Fine tune provider 'invalid_provider' not found"
    )
