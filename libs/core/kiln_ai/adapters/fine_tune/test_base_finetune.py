import time
from unittest.mock import Mock

import pytest

from kiln_ai.adapters.fine_tune.base_finetune import (
    BaseFinetuneAdapter,
    FineTuneParameter,
    FineTuneStatus,
    FineTuneStatusType,
)
from kiln_ai.adapters.ml_model_list import KilnModelProvider
from kiln_ai.datamodel import DatasetSplit, Task
from kiln_ai.datamodel import Finetune as FinetuneModel


class MockFinetune(BaseFinetuneAdapter):
    """Mock implementation of BaseFinetune for testing"""

    def _start(self, dataset: DatasetSplit) -> None:
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
            system_message="Test system message",
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


def test_validate_parameters_valid():
    # Test valid parameters
    valid_params = {
        "learning_rate": 0.001,
        "epochs": 10,
    }
    MockFinetune.validate_parameters(valid_params)  # Should not raise


def test_validate_parameters_missing_required():
    # Test missing required parameter
    invalid_params = {
        "learning_rate": 0.001,
        # missing required 'epochs'
    }
    with pytest.raises(ValueError, match="Parameter epochs is required"):
        MockFinetune.validate_parameters(invalid_params)


def test_validate_parameters_wrong_type():
    # Test wrong parameter types
    invalid_params = {
        "learning_rate": "0.001",  # string instead of float
        "epochs": 10,
    }
    with pytest.raises(ValueError, match="Parameter learning_rate must be a float"):
        MockFinetune.validate_parameters(invalid_params)

    invalid_params = {
        "learning_rate": 0.001,
        "epochs": 10.5,  # float instead of int
    }
    with pytest.raises(ValueError, match="Parameter epochs must be an integer"):
        MockFinetune.validate_parameters(invalid_params)


def test_validate_parameters_unknown_parameter():
    # Test unknown parameter
    invalid_params = {
        "learning_rate": 0.001,
        "epochs": 10,
        "unknown_param": "value",
    }
    with pytest.raises(ValueError, match="Parameter unknown_param is not available"):
        MockFinetune.validate_parameters(invalid_params)


@pytest.fixture
def mock_model():
    return KilnModelProvider(
        name="openai",
        friendly_name="OpenAI Mock Model",
        provider_finetune_id="base_model_123",
    )


@pytest.fixture
def mock_dataset(sample_task):
    dataset = Mock(spec=DatasetSplit)
    dataset.id = "dataset_123"
    dataset.parent_task.return_value = sample_task
    return dataset


def test_create_and_start_success(mock_dataset, mock_model):
    # Test successful creation with minimal parameters
    adapter, datamodel = MockFinetune.create_and_start(
        dataset=mock_dataset,
        model=mock_model,
        train_split_name="train",
        parameters={"epochs": 10},  # Required parameter
        system_message="Test system message",
    )

    assert isinstance(adapter, MockFinetune)
    assert isinstance(datamodel, FinetuneModel)
    assert datamodel.name.startswith(
        f"{mock_model.provider_finetune_id} - "
    )  # Default name format
    assert datamodel.provider == mock_model.name
    assert datamodel.base_model_id == mock_model.provider_finetune_id
    assert datamodel.dataset_split_id == mock_dataset.id
    assert datamodel.train_split_name == "train"
    assert datamodel.parameters == {"epochs": 10}
    assert datamodel.system_message == "Test system message"
    assert datamodel.path.exists()


def test_create_and_start_with_all_params(mock_dataset, mock_model):
    # Test creation with all optional parameters
    adapter, datamodel = MockFinetune.create_and_start(
        dataset=mock_dataset,
        model=mock_model,
        train_split_name="train",
        parameters={"epochs": 10, "learning_rate": 0.001},
        name="Custom Name",
        description="Custom Description",
        validation_split_name="test",
        system_message="Test system message",
    )

    assert datamodel.name == "Custom Name"
    assert datamodel.description == "Custom Description"
    assert datamodel.validation_split_name == "test"
    assert datamodel.parameters == {"epochs": 10, "learning_rate": 0.001}
    assert datamodel.system_message == "Test system message"
    assert adapter.datamodel == datamodel

    # load the datamodel from the file, confirm it's saved
    loaded_datamodel = FinetuneModel.load_from_file(datamodel.path)
    assert loaded_datamodel.model_dump_json() == datamodel.model_dump_json()


def test_create_and_start_invalid_parameters(mock_dataset, mock_model):
    # Test with invalid parameters
    with pytest.raises(ValueError, match="Parameter epochs is required"):
        MockFinetune.create_and_start(
            dataset=mock_dataset,
            model=mock_model,
            train_split_name="train",
            parameters={"learning_rate": 0.001},  # Missing required 'epochs'
            system_message="Test system message",
        )


def test_create_and_start_no_parent_task(mock_model):
    # Test with dataset that has no parent task
    dataset = Mock(spec=DatasetSplit)
    dataset.id = "dataset_123"
    dataset.parent_task.return_value = None

    with pytest.raises(ValueError, match="Dataset must have a parent task with a path"):
        MockFinetune.create_and_start(
            dataset=dataset,
            model=mock_model,
            train_split_name="train",
            parameters={"epochs": 10},
            system_message="Test system message",
        )


def test_create_and_start_no_parent_task_path(mock_model):
    # Test with dataset that has parent task but no path
    task = Mock(spec=Task)
    task.path = None

    dataset = Mock(spec=DatasetSplit)
    dataset.id = "dataset_123"
    dataset.parent_task.return_value = task

    with pytest.raises(ValueError, match="Dataset must have a parent task with a path"):
        MockFinetune.create_and_start(
            dataset=dataset,
            model=mock_model,
            train_split_name="train",
            parameters={"epochs": 10},
            system_message="Test system message",
        )
