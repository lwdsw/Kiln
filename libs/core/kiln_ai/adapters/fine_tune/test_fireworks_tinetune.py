from unittest.mock import MagicMock, patch

import httpx
import pytest

from kiln_ai.adapters.fine_tune.base_finetune import FineTuneStatusType
from kiln_ai.adapters.fine_tune.fireworks_finetune import FireworksFinetune
from kiln_ai.datamodel import Finetune as FinetuneModel
from kiln_ai.utils.config import Config


@pytest.fixture
def fireworks_finetune(tmp_path):
    tmp_file = tmp_path / "test-finetune.kiln"
    finetune = FireworksFinetune(
        datamodel=FinetuneModel(
            name="test-finetune",
            provider="fireworks",
            provider_id="fw-123",
            base_model_id="llama-v2-7b",
            train_split_name="train",
            dataset_split_id="dataset-123",
            system_message="Test system message",
            fine_tune_model_id="ft-123",
            path=tmp_file,
        ),
    )
    return finetune


@pytest.fixture
def mock_response():
    response = MagicMock(spec=httpx.Response)
    response.status_code = 200
    response.json.return_value = {
        "state": "COMPLETED",
        "model": "llama-v2-7b",
    }
    return response


@pytest.fixture
def mock_client():
    client = MagicMock(spec=httpx.AsyncClient)
    return client


async def test_setup(fireworks_finetune):
    if (
        not Config.shared().fireworks_api_key
        or not Config.shared().fireworks_account_id
    ):
        pytest.skip("Fireworks API key or account ID not set")

    # Real API call, with fake ID
    status = await fireworks_finetune.status()
    assert status.status == FineTuneStatusType.unknown
    assert "Error retrieving fine-tuning job status" in status.message


async def test_status_missing_credentials(fireworks_finetune):
    with patch.object(Config, "shared") as mock_config:
        mock_config.return_value.fireworks_api_key = None
        mock_config.return_value.fireworks_account_id = None

        status = await fireworks_finetune.status()
        assert status.status == FineTuneStatusType.unknown
        assert "Fireworks API key or account ID not set" == status.message


async def test_status_missing_provider_id(fireworks_finetune):
    fireworks_finetune.datamodel.provider_id = None

    status = await fireworks_finetune.status()
    assert status.status == FineTuneStatusType.unknown
    assert "Fine-tuning job ID not set" in status.message


@pytest.mark.parametrize(
    "status_code,expected_status,expected_message",
    [
        (
            401,
            FineTuneStatusType.unknown,
            "Error retrieving fine-tuning job status: [401]",
        ),
        (
            404,
            FineTuneStatusType.unknown,
            "Error retrieving fine-tuning job status: [404]",
        ),
        (
            500,
            FineTuneStatusType.unknown,
            "Error retrieving fine-tuning job status: [500]",
        ),
    ],
)
async def test_status_api_errors(
    fireworks_finetune,
    mock_response,
    mock_client,
    status_code,
    expected_status,
    expected_message,
):
    mock_response.status_code = status_code
    mock_response.text = "Error message"
    mock_client.get.return_value = mock_response

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client_class.return_value.__aenter__.return_value = mock_client
        status = await fireworks_finetune.status()
        assert status.status == expected_status
        assert expected_message in status.message


@pytest.mark.parametrize(
    "state,expected_status,message",
    [
        ("FAILED", FineTuneStatusType.failed, "Fine-tuning job failed"),
        ("DELETING", FineTuneStatusType.failed, "Fine-tuning job failed"),
        ("COMPLETED", FineTuneStatusType.completed, "Fine-tuning job completed"),
        (
            "CREATING",
            FineTuneStatusType.running,
            "Fine-tuning job is running [CREATING]",
        ),
        ("PENDING", FineTuneStatusType.running, "Fine-tuning job is running [PENDING]"),
        ("RUNNING", FineTuneStatusType.running, "Fine-tuning job is running [RUNNING]"),
        (
            "UNKNOWN_STATE",
            FineTuneStatusType.unknown,
            "Unknown fine-tuning job status [UNKNOWN_STATE]",
        ),
        (
            "UNSPECIFIED_STATE",
            FineTuneStatusType.unknown,
            "Unknown fine-tuning job status [UNSPECIFIED_STATE]",
        ),
    ],
)
async def test_status_job_states(
    fireworks_finetune,
    mock_response,
    mock_client,
    state,
    expected_status,
    message,
):
    mock_response.json.return_value = {"state": state}
    mock_client.get.return_value = mock_response

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client_class.return_value.__aenter__.return_value = mock_client
        status = await fireworks_finetune.status()
        assert status.status == expected_status
        assert message == status.message


async def test_status_invalid_response(fireworks_finetune, mock_response, mock_client):
    mock_response.json.return_value = {"no_state_field": "value"}
    mock_client.get.return_value = mock_response

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client_class.return_value.__aenter__.return_value = mock_client
        status = await fireworks_finetune.status()
        assert status.status == FineTuneStatusType.unknown
        assert "Invalid response from Fireworks" in status.message


async def test_status_request_exception(fireworks_finetune, mock_client):
    mock_client.get.side_effect = Exception("Connection error")

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client_class.return_value.__aenter__.return_value = mock_client
        status = await fireworks_finetune.status()
        assert status.status == FineTuneStatusType.unknown
        assert (
            "Error retrieving fine-tuning job status: Connection error"
            == status.message
        )
