from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from kiln_ai.datamodel import (
    DataSource,
    DataSourceType,
    Project,
    Task,
    TaskOutput,
    TaskRun,
)

from app.desktop.studio_server.data_gen_api import (
    DataGenCategoriesApiInput,
    DataGenSampleApiInput,
    connect_data_gen_api,
)


@pytest.fixture
def app():
    app = FastAPI()
    connect_data_gen_api(app)
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def data_source():
    return DataSource(
        type=DataSourceType.synthetic,
        properties={
            "model_name": "gpt-4",
            "model_provider": "openai",
            "adapter_name": "langchain_adapter",
        },
    )


@pytest.fixture
def test_task(tmp_path) -> Task:
    project_path = tmp_path / "test_project" / "project.kiln"
    project_path.parent.mkdir()

    project = Project(name="Test Project", path=str(project_path))
    project.save_to_file()

    task = Task(name="Test Task", instruction="Test Instruction", parent=project)
    task.save_to_file()
    return task


@pytest.fixture
def mock_task_run(data_source, test_task):
    return TaskRun(
        output=TaskOutput(
            output="Test Output",
            source=data_source,
        ),
        input="Test Input",
        input_source=data_source,
        parent=test_task,
    )


@pytest.fixture
def mock_langchain_adapter(mock_task_run):
    with patch("app.desktop.studio_server.data_gen_api.LangChainPromptAdapter") as mock:
        mock_adapter = AsyncMock()
        mock_adapter.invoke = AsyncMock()
        mock.return_value = mock_adapter

        mock_adapter.invoke.return_value = mock_task_run

        yield mock_adapter


@pytest.fixture
def mock_task_from_id(test_task):
    with patch("app.desktop.studio_server.data_gen_api.task_from_id") as mock:
        mock.return_value = test_task
        yield mock


def test_generate_categories_success(
    mock_task_from_id,
    mock_langchain_adapter,
    client,
    mock_task_run,
):
    # Arrange
    input_data = DataGenCategoriesApiInput(
        node_path=["parent", "child"],
        num_subtopics=4,
        human_guidance="Generate tech categories",
        model_name="gpt-4",
        provider="openai",
    )

    # Act
    response = client.post(
        "/api/projects/proj-ID/tasks/task-ID/generate_categories",
        json=input_data.model_dump(),
    )

    # Assert
    assert response.status_code == 200
    res = response.json()
    assert TaskOutput.model_validate(res["output"]) == mock_task_run.output
    mock_langchain_adapter.invoke.assert_awaited_once()


def test_generate_samples_success(
    mock_task_from_id,
    mock_langchain_adapter,
    client,
    mock_task_run,
):
    # Arrange
    input_data = DataGenSampleApiInput(
        topic=["technology", "AI"],
        num_samples=5,
        human_guidance="Make long samples",
        model_name="gpt-4",
        provider="openai",
    )

    # Act
    response = client.post(
        "/api/projects/proj-ID/tasks/task-ID/generate_samples",
        json=input_data.model_dump(),
    )

    # Assert
    assert response.status_code == 200
    res = response.json()
    assert TaskOutput.model_validate(res["output"]) == mock_task_run.output
    mock_langchain_adapter.invoke.assert_awaited_once()
