# ruff: noqa: I001 - Import order matters here. Need datamodel before finetune

import pytest
from pydantic import ValidationError

from kiln_ai.datamodel import Task
from kiln_ai.adapters.fine_tune.base_finetune import (
    BaseFinetune,
    FineTuneParameter,
    FineTuneStatus,
    FineTuneStatusType,
)


class MockFinetune(BaseFinetune):
    """Mock implementation of BaseFinetune for testing"""

    def start(self) -> None:
        pass

    def status(self) -> FineTuneStatus:
        return FineTuneStatus(status=FineTuneStatusType.pending, message="loading...")

    @classmethod
    def available_parameters(cls) -> list[FineTuneParameter]:
        return [
            FineTuneParameter(
                name="learning_rate",
                type="float",
                description="Learning rate for training",
            ),
            FineTuneParameter(
                name="epochs",
                type="int",
                description="Number of training epochs",
                optional=False,
            ),
        ]


@pytest.fixture
def sample_task(tmp_path):
    task_path = tmp_path / "task.kiln"
    task = Task(
        name="Test Task",
        path=task_path,
        description="Test task for fine-tuning",
        instruction="Test instruction",
    )
    task.save_to_file()
    return task


@pytest.fixture
def basic_finetune(sample_task):
    return MockFinetune(
        name="test_finetune",
        parent=sample_task,
        provider="test_provider",
        base_model_id="test_model",
        provider_id="model_1234",
    )


def test_finetune_basic_properties(basic_finetune):
    assert basic_finetune.name == "test_finetune"
    assert basic_finetune.provider == "test_provider"
    assert basic_finetune.base_model_id == "test_model"
    assert basic_finetune.provider_id == "model_1234"
    assert basic_finetune.parameters == {}
    assert basic_finetune.description is None


def test_finetune_parameters_validation():
    with pytest.raises(ValidationError):
        MockFinetune(
            name="test",
            provider="test_provider",
            base_model_provider_id="test_model",
            parameters="invalid",  # Should be a dict
        )


def test_finetune_parent_task(sample_task, basic_finetune):
    assert basic_finetune.parent_task() == sample_task

    # Test with no parent
    orphan_finetune = MockFinetune(
        name="orphan",
        provider="test_provider",
        base_model_id="test_model",
    )
    assert orphan_finetune.parent_task() is None


def test_finetune_status(basic_finetune):
    assert basic_finetune.status().status == FineTuneStatusType.pending
    assert basic_finetune.status().message == "loading..."
    assert isinstance(basic_finetune.status(), FineTuneStatus)


def test_available_parameters():
    params = MockFinetune.available_parameters()
    assert len(params) == 2

    learning_rate_param = params[0]
    assert learning_rate_param.name == "learning_rate"
    assert learning_rate_param.type == "float"
    assert learning_rate_param.optional is True

    epochs_param = params[1]
    assert epochs_param.name == "epochs"
    assert epochs_param.type == "int"
    assert epochs_param.optional is False


def test_finetune_with_parameters(sample_task):
    finetune = MockFinetune(
        name="test_with_params",
        parent=sample_task,
        provider="test_provider",
        base_model_id="test_model",
        parameters={
            "learning_rate": 0.001,
            "epochs": 10,
            "batch_size": 32,
            "fast": True,
            "prefix": "test_prefix",
        },
    )

    assert finetune.parameters["learning_rate"] == 0.001
    assert finetune.parameters["epochs"] == 10
    assert finetune.parameters["batch_size"] == 32
    assert finetune.parameters["fast"] is True
    assert finetune.parameters["prefix"] == "test_prefix"
