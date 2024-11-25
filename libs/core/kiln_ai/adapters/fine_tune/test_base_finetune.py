import pytest

from kiln_ai.adapters.fine_tune.base_finetune import (
    BaseFinetuneAdapter,
    FineTuneParameter,
    FineTuneStatus,
    FineTuneStatusType,
)
from kiln_ai.datamodel import Finetune as FinetuneModel
from kiln_ai.datamodel import Task


class MockFinetune(BaseFinetuneAdapter):
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
        datamodel=FinetuneModel(
            parent=sample_task,
            name="test_finetune",
            provider="test_provider",
            provider_id="model_1234",
            base_model_id="test_model",
            train_split_name="train",
            dataset_split_id="dataset-123",
        ),
    )


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
