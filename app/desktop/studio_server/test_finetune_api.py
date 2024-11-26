from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
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
