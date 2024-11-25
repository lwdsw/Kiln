import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import openai
import pytest
from openai.types.fine_tuning import FineTuningJob

from kiln_ai.adapters.fine_tune.base_finetune import FineTuneStatusType
from kiln_ai.adapters.fine_tune.dataset_formatter import DatasetFormat, DatasetFormatter
from kiln_ai.adapters.fine_tune.openai_finetune import OpenAIFinetune
from kiln_ai.datamodel import DatasetSplit, Task, Train80Test20SplitDefinition
from kiln_ai.datamodel import Finetune as FinetuneModel
from kiln_ai.utils.config import Config


@pytest.fixture
def openai_finetune():
    finetune = OpenAIFinetune(
        datamodel=FinetuneModel(
            name="test-finetune",
            provider="openai",
            provider_id="openai-123",
            base_model_id="gpt-4o",
            train_split_name="train",
            dataset_split_id="dataset-123",
            system_message="Test system message",
        ),
    )
    return finetune


@pytest.fixture
def mock_response():
    response = MagicMock(spec=FineTuningJob)
    response.error = None
    response.status = "succeeded"
    response.finished_at = time.time()
    response.estimated_finish = None
    return response


@pytest.fixture
def mock_dataset():
    return DatasetSplit(
        id="test-dataset-123",
        name="Test Dataset",
        splits=Train80Test20SplitDefinition,
        split_contents={"train": [], "test": []},
    )


@pytest.fixture
def mock_task():
    return Task(
        id="test-task-123",
        name="Test Task",
        output_json_schema=None,  # Can be modified in specific tests
        instruction="Test instruction",
    )


def test_setup(openai_finetune):
    if not Config.shared().open_ai_api_key:
        pytest.skip("OpenAI API key not set")
    openai_finetune.provider_id = "openai-123"
    openai_finetune.provider = "openai"

    # Real API call, with fake ID
    status = openai_finetune.status()
    # fake id fails
    assert status.status == FineTuneStatusType.unknown
    assert "Job with this ID not found. It may have been deleted." == status.message


@pytest.mark.parametrize(
    "exception,expected_status,expected_message",
    [
        (
            openai.APIConnectionError(request=MagicMock()),
            FineTuneStatusType.unknown,
            "Server connection error",
        ),
        (
            openai.RateLimitError(
                message="Rate limit exceeded", body={}, response=MagicMock()
            ),
            FineTuneStatusType.unknown,
            "Rate limit exceeded",
        ),
        (
            openai.APIStatusError(
                "Not found",
                response=MagicMock(status_code=404),
                body={},
            ),
            FineTuneStatusType.unknown,
            "Job with this ID not found",
        ),
        (
            openai.APIStatusError(
                "Server error",
                response=MagicMock(status_code=500),
                body={},
            ),
            FineTuneStatusType.unknown,
            "Unknown error",
        ),
    ],
)
def test_status_api_errors(
    openai_finetune, exception, expected_status, expected_message
):
    with patch(
        "kiln_ai.adapters.fine_tune.openai_finetune.oai_client.fine_tuning.jobs.retrieve",
        side_effect=exception,
    ):
        status = openai_finetune.status()
        assert status.status == expected_status
        assert expected_message in status.message


@pytest.mark.parametrize(
    "job_status,expected_status,message_contains",
    [
        ("failed", FineTuneStatusType.failed, "Job failed"),
        ("cancelled", FineTuneStatusType.failed, "Job cancelled"),
        ("succeeded", FineTuneStatusType.completed, "Job completed"),
        ("running", FineTuneStatusType.running, "Job is still running"),
        ("queued", FineTuneStatusType.running, "Job is still running"),
        (
            "validating_files",
            FineTuneStatusType.running,
            "Job is still running",
        ),
        ("unknown_status", FineTuneStatusType.unknown, "Unknown status"),
    ],
)
def test_status_job_states(
    openai_finetune,
    mock_response,
    job_status,
    expected_status,
    message_contains,
):
    mock_response.status = job_status

    with patch(
        "kiln_ai.adapters.fine_tune.openai_finetune.oai_client.fine_tuning.jobs.retrieve",
        return_value=mock_response,
    ):
        status = openai_finetune.status()
        assert status.status == expected_status
        assert message_contains in status.message


def test_status_with_error_response(openai_finetune, mock_response):
    mock_response.error = MagicMock()
    mock_response.error.message = "Something went wrong"

    with patch(
        "kiln_ai.adapters.fine_tune.openai_finetune.oai_client.fine_tuning.jobs.retrieve",
        return_value=mock_response,
    ):
        status = openai_finetune.status()
        assert status.status == FineTuneStatusType.failed
        assert status.message == "Something went wrong"


def test_status_with_estimated_finish_time(openai_finetune, mock_response):
    current_time = time.time()
    mock_response.status = "running"
    mock_response.estimated_finish = current_time + 300  # 5 minutes from now

    with patch(
        "kiln_ai.adapters.fine_tune.openai_finetune.oai_client.fine_tuning.jobs.retrieve",
        return_value=mock_response,
    ):
        status = openai_finetune.status()
        assert status.status == FineTuneStatusType.running
        assert (
            "Estimated finish time: 299 seconds" in status.message
        )  # non zero time passes


def test_status_empty_response(openai_finetune):
    with patch(
        "kiln_ai.adapters.fine_tune.openai_finetune.oai_client.fine_tuning.jobs.retrieve",
        return_value=mock_response,
    ):
        status = openai_finetune.status()
        assert status.status == FineTuneStatusType.unknown
        assert "Invalid response from OpenAI" in status.message


def test_generate_and_upload_jsonl_success(openai_finetune, mock_dataset, mock_task):
    mock_path = Path("mock_path.jsonl")
    mock_file_id = "file-123"

    # Mock the formatter
    mock_formatter = MagicMock(spec=DatasetFormatter)
    mock_formatter.dump_to_file.return_value = mock_path

    # Mock the file response
    mock_file_response = MagicMock()
    mock_file_response.id = mock_file_id

    with (
        patch(
            "kiln_ai.adapters.fine_tune.openai_finetune.DatasetFormatter",
            return_value=mock_formatter,
        ) as mock_formatter_class,
        patch(
            "kiln_ai.adapters.fine_tune.openai_finetune.oai_client.files.create",
            return_value=mock_file_response,
        ) as mock_create,
        patch("builtins.open") as mock_open,
    ):
        result = openai_finetune.generate_and_upload_jsonl(
            mock_dataset, "train", mock_task
        )

        # Verify formatter was created with correct parameters
        mock_formatter_class.assert_called_once_with(
            mock_dataset, openai_finetune.datamodel.system_message
        )

        # Verify correct format was used
        mock_formatter.dump_to_file.assert_called_once_with(
            "train", DatasetFormat.CHAT_MESSAGE_RESPONSE_JSONL
        )

        # Verify file was opened and uploaded
        mock_open.assert_called_once_with(mock_path, "rb")
        mock_create.assert_called_once()

        assert result == mock_file_id


def test_generate_and_upload_jsonl_toolcall_success(
    openai_finetune, mock_dataset, mock_task
):
    mock_path = Path("mock_path.jsonl")
    mock_file_id = "file-123"
    mock_task.output_json_schema = '{"type": "object", "properties": {"key": {"type": "string"}}}'  # Add JSON schema

    # Mock the formatter
    mock_formatter = MagicMock(spec=DatasetFormatter)
    mock_formatter.dump_to_file.return_value = mock_path

    # Mock the file response
    mock_file_response = MagicMock()
    mock_file_response.id = mock_file_id

    with (
        patch(
            "kiln_ai.adapters.fine_tune.openai_finetune.DatasetFormatter",
            return_value=mock_formatter,
        ) as mock_formatter_class,
        patch(
            "kiln_ai.adapters.fine_tune.openai_finetune.oai_client.files.create",
            return_value=mock_file_response,
        ) as mock_create,
        patch("builtins.open") as mock_open,
    ):
        result = openai_finetune.generate_and_upload_jsonl(
            mock_dataset, "train", mock_task
        )

        # Verify formatter was created with correct parameters
        mock_formatter_class.assert_called_once_with(
            mock_dataset, openai_finetune.datamodel.system_message
        )

        # Verify correct format was used
        mock_formatter.dump_to_file.assert_called_once_with(
            "train", DatasetFormat.CHAT_MESSAGE_TOOLCALL_JSONL
        )

        # Verify file was opened and uploaded
        mock_open.assert_called_once_with(mock_path, "rb")
        mock_create.assert_called_once()

        assert result == mock_file_id


def test_generate_and_upload_jsonl_upload_failure(
    openai_finetune, mock_dataset, mock_task
):
    mock_path = Path("mock_path.jsonl")

    mock_formatter = MagicMock(spec=DatasetFormatter)
    mock_formatter.dump_to_file.return_value = mock_path

    # Mock response with no ID
    mock_file_response = MagicMock()
    mock_file_response.id = None

    with (
        patch(
            "kiln_ai.adapters.fine_tune.openai_finetune.DatasetFormatter",
            return_value=mock_formatter,
        ),
        patch(
            "kiln_ai.adapters.fine_tune.openai_finetune.oai_client.files.create",
            return_value=mock_file_response,
        ),
        patch("builtins.open"),
    ):
        with pytest.raises(ValueError, match="Failed to upload file to OpenAI"):
            openai_finetune.generate_and_upload_jsonl(mock_dataset, "train", mock_task)


def test_generate_and_upload_jsonl_api_error(openai_finetune, mock_dataset, mock_task):
    mock_path = Path("mock_path.jsonl")

    mock_formatter = MagicMock(spec=DatasetFormatter)
    mock_formatter.dump_to_file.return_value = mock_path

    with (
        patch(
            "kiln_ai.adapters.fine_tune.openai_finetune.DatasetFormatter",
            return_value=mock_formatter,
        ),
        patch(
            "kiln_ai.adapters.fine_tune.openai_finetune.oai_client.files.create",
            side_effect=openai.APIError(
                message="API error", request=MagicMock(), body={}
            ),
        ),
        patch("builtins.open"),
    ):
        with pytest.raises(openai.APIError):
            openai_finetune.generate_and_upload_jsonl(mock_dataset, "train", mock_task)
