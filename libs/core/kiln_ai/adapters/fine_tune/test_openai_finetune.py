import time
from unittest.mock import MagicMock, patch

import openai
import pytest
from openai.types.fine_tuning import FineTuningJob

from kiln_ai.adapters.fine_tune.base_finetune import FineTuneStatusType
from kiln_ai.adapters.fine_tune.openai_finetune import OpenAIFinetune
from kiln_ai.datamodel import Finetune as FinetuneModel
from kiln_ai.utils.config import Config


@pytest.fixture
def openai_finetune():
    finetune = OpenAIFinetune(
        model=FinetuneModel(
            name="test-finetune",
            provider="openai",
            provider_id="openai-123",
            base_model_id="gpt-4o",
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


def test_setup(openai_finetune):
    if not Config.shared().open_ai_api_key:
        pytest.skip("OpenAI API key not set")
    openai_finetune.provider_id = "openai-123"
    openai_finetune.provider = "openai"

    # Real API call, with fake ID
    status = openai_finetune.status()
    # fake id fails
    assert status.status == FineTuneStatusType.failed
    assert "Job with this ID not found. It may have been deleted." == status.message


@pytest.mark.parametrize(
    "exception,expected_status,expected_message",
    [
        (
            openai.APIConnectionError(request=MagicMock()),
            FineTuneStatusType.unknown,
            "Server connection error",
        ),
        # (
        #    openai.RateLimitError(message="Rate limit exceeded", body={}),
        #    FineTuneStatusType.unknown,
        #    "Rate limit exceeded",
        # ),
        (
            openai.APIStatusError(
                "Not found",
                response=MagicMock(status_code=404),
                body={},
            ),
            FineTuneStatusType.failed,
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
    "job_status,finished_at,estimated_finish,expected_status,message_contains",
    [
        ("failed", None, None, FineTuneStatusType.failed, "Job failed"),
        ("cancelled", None, None, FineTuneStatusType.failed, "Job cancelled"),
        ("succeeded", time.time(), None, FineTuneStatusType.completed, "Job completed"),
        ("running", None, None, FineTuneStatusType.running, "Job is still running"),
        ("queued", None, None, FineTuneStatusType.running, "Job is still running"),
        (
            "validating_files",
            None,
            None,
            FineTuneStatusType.running,
            "Job is still running",
        ),
        ("unknown_status", None, None, FineTuneStatusType.unknown, "Unknown status"),
    ],
)
def test_status_job_states(
    openai_finetune,
    mock_response,
    job_status,
    finished_at,
    estimated_finish,
    expected_status,
    message_contains,
):
    mock_response.status = job_status
    mock_response.finished_at = finished_at
    mock_response.estimated_finish = estimated_finish

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
