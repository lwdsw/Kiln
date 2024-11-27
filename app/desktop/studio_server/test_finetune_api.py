import unittest.mock
from datetime import datetime
from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from kiln_ai.adapters.fine_tune.base_finetune import FineTuneParameter
from kiln_ai.adapters.ml_model_list import KilnModel, KilnModelProvider
from kiln_ai.datamodel import (
    AllDatasetFilter,
    AllSplitDefinition,
    DatasetSplit,
    Finetune,
    HighRatingDatasetFilter,
    Train60Test20Val20SplitDefinition,
    Train80Test20SplitDefinition,
)

from app.desktop.studio_server.finetune_api import (
    CreateDatasetSplitRequest,
    DatasetFilterType,
    DatasetSplitType,
    connect_fine_tune_api,
)


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


def test_dataset_split_type_enum():
    assert DatasetSplitType.TRAIN_TEST.value == "train_test"
    assert DatasetSplitType.TRAIN_TEST_VAL.value == "train_test_val"
    assert DatasetSplitType.ALL.value == "all"


def test_dataset_filter_type_enum():
    assert DatasetFilterType.ALL.value == "all"
    assert DatasetFilterType.HIGH_RATING.value == "high_rating"


def test_api_split_types_mapping():
    from app.desktop.studio_server.finetune_api import api_split_types

    assert api_split_types[DatasetSplitType.TRAIN_TEST] == Train80Test20SplitDefinition
    assert (
        api_split_types[DatasetSplitType.TRAIN_TEST_VAL]
        == Train60Test20Val20SplitDefinition
    )
    assert api_split_types[DatasetSplitType.ALL] == AllSplitDefinition
    for split_type in DatasetSplitType:
        assert split_type in api_split_types


def test_api_filter_types_mapping():
    from app.desktop.studio_server.finetune_api import api_filter_types

    assert api_filter_types[DatasetFilterType.ALL] == AllDatasetFilter
    assert api_filter_types[DatasetFilterType.HIGH_RATING] == HighRatingDatasetFilter
    for filter_type in DatasetFilterType:
        assert filter_type in api_filter_types


@pytest.fixture
def mock_dataset_split():
    split = DatasetSplit(
        id="new_split",
        name="Test Split",
        split_contents={"train": ["1", "2"], "test": ["3"]},
        splits=AllSplitDefinition,
    )
    return split


def test_create_dataset_split(client, mock_task_from_id, mock_dataset_split):
    # Mock DatasetSplit.from_task and save_to_file
    mock_from_task = unittest.mock.patch.object(
        DatasetSplit, "from_task", return_value=mock_dataset_split
    )
    mock_save = unittest.mock.patch.object(DatasetSplit, "save_to_file")

    with mock_from_task as from_task_mock, mock_save as save_mock:
        request_data = {
            "dataset_split_type": "train_test",
            "filter_type": "all",
            "name": "Test Split",
            "description": "Test description",
        }

        response = client.post(
            "/api/projects/project1/tasks/task1/dataset_splits", json=request_data
        )

        assert response.status_code == 200
        result = response.json()
        assert result["id"] == "new_split"
        assert result["name"] == "Test Split"

        # Verify the mocks were called correctly
        mock_task_from_id.assert_called_once_with("project1", "task1")
        from_task_mock.assert_called_once()
        save_mock.assert_called_once()


def test_create_dataset_split_auto_name(client, mock_task_from_id, mock_dataset_split):
    # Mock DatasetSplit.from_task and save_to_file
    mock_from_task = unittest.mock.patch.object(
        DatasetSplit, "from_task", return_value=mock_dataset_split
    )
    mock_save = unittest.mock.patch.object(DatasetSplit, "save_to_file")
    mock_datetime = unittest.mock.patch(
        "app.desktop.studio_server.finetune_api.datetime"
    )

    with mock_from_task as from_task_mock, mock_save as save_mock, mock_datetime as dt:
        # Mock datetime to have a consistent test
        mock_now = datetime(2024, 1, 1, 12, 0, 0)
        dt.now.return_value = mock_now

        request_data = {"dataset_split_type": "train_test", "filter_type": "all"}

        response = client.post(
            "/api/projects/project1/tasks/task1/dataset_splits", json=request_data
        )

        assert response.status_code == 200

        # Verify auto-generated name format
        from_task_mock.assert_called_once()
        args = from_task_mock.call_args[0]
        assert args[0] == "2024-01-01 12-00-00 filter--all split--train_test"
        save_mock.assert_called_once()


def test_create_dataset_split_request_validation():
    # Test valid request
    request = CreateDatasetSplitRequest(
        dataset_split_type=DatasetSplitType.TRAIN_TEST,
        filter_type=DatasetFilterType.ALL,
        name="Test Split",
        description="Test description",
    )
    assert request.dataset_split_type == DatasetSplitType.TRAIN_TEST
    assert request.filter_type == DatasetFilterType.ALL
    assert request.name == "Test Split"
    assert request.description == "Test description"

    # Test optional fields
    request = CreateDatasetSplitRequest(
        dataset_split_type=DatasetSplitType.TRAIN_TEST,
        filter_type=DatasetFilterType.ALL,
    )
    assert request.name is None
    assert request.description is None

    # Test invalid dataset split type
    with pytest.raises(ValueError):
        CreateDatasetSplitRequest(
            dataset_split_type="invalid_type", filter_type=DatasetFilterType.ALL
        )

    # Test invalid filter type
    with pytest.raises(ValueError):
        CreateDatasetSplitRequest(
            dataset_split_type=DatasetSplitType.TRAIN_TEST, filter_type="invalid_type"
        )
