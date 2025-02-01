from unittest.mock import patch

import pytest

from kiln_ai.adapters.ml_model_list import KilnModelProvider
from kiln_ai.adapters.model_adapters.base_adapter import AdapterInfo, BaseAdapter
from kiln_ai.datamodel import Task


class TestAdapter(BaseAdapter):
    """Concrete implementation of BaseAdapter for testing"""

    async def _run(self, input):
        return None

    def adapter_info(self) -> AdapterInfo:
        return AdapterInfo(
            adapter_name="test",
            model_name=self.model_name,
            model_provider=self.model_provider_name,
            prompt_builder_name="test",
        )


@pytest.fixture
def mock_provider():
    return KilnModelProvider(
        name="openai",
    )


@pytest.fixture
def base_task():
    return Task(name="test_task", instruction="test_instruction")


@pytest.fixture
def adapter(base_task):
    return TestAdapter(
        kiln_task=base_task,
        model_name="test_model",
        model_provider_name="test_provider",
    )


async def test_model_provider_uses_cache(adapter, mock_provider):
    """Test that cached provider is returned if it exists"""
    # Set up cached provider
    adapter._model_provider = mock_provider

    # Mock the provider loader to ensure it's not called
    with patch(
        "kiln_ai.adapters.model_adapters.base_adapter.kiln_model_provider_from"
    ) as mock_loader:
        provider = await adapter.model_provider()

        assert provider == mock_provider
        mock_loader.assert_not_called()


async def test_model_provider_loads_and_caches(adapter, mock_provider):
    """Test that provider is loaded and cached if not present"""
    # Ensure no cached provider
    adapter._model_provider = None

    # Mock the provider loader
    with patch(
        "kiln_ai.adapters.model_adapters.base_adapter.kiln_model_provider_from"
    ) as mock_loader:
        mock_loader.return_value = mock_provider

        # First call should load and cache
        provider1 = await adapter.model_provider()
        assert provider1 == mock_provider
        mock_loader.assert_called_once_with("test_model", "test_provider")

        # Second call should use cache
        mock_loader.reset_mock()
        provider2 = await adapter.model_provider()
        assert provider2 == mock_provider
        mock_loader.assert_not_called()


async def test_model_provider_missing_names(base_task):
    """Test error when model or provider name is missing"""
    # Test with missing model name
    adapter = TestAdapter(
        kiln_task=base_task, model_name="", model_provider_name="test_provider"
    )
    with pytest.raises(
        ValueError, match="model_name and model_provider_name must be provided"
    ):
        await adapter.model_provider()

    # Test with missing provider name
    adapter = TestAdapter(
        kiln_task=base_task, model_name="test_model", model_provider_name=""
    )
    with pytest.raises(
        ValueError, match="model_name and model_provider_name must be provided"
    ):
        await adapter.model_provider()


async def test_model_provider_not_found(adapter):
    """Test error when provider loader returns None"""
    # Mock the provider loader to return None
    with patch(
        "kiln_ai.adapters.model_adapters.base_adapter.kiln_model_provider_from"
    ) as mock_loader:
        mock_loader.return_value = None

        with pytest.raises(
            ValueError,
            match="model_provider_name test_provider not found for model test_model",
        ):
            await adapter.model_provider()
