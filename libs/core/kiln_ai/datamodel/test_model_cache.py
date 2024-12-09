from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import BaseModel

from libs.core.kiln_ai.datamodel.model_cache import ModelCache


# Define a simple Pydantic model for testing
class ModelTest(BaseModel):
    name: str
    value: int


@pytest.fixture
def model_cache():
    return ModelCache()


@pytest.fixture
def test_path(tmp_path):
    # Create a temporary file path for testing
    test_file = tmp_path / "test_model.kiln"
    test_file.touch()  # Create the file
    return test_file


def test_set_and_get_model(model_cache, test_path):
    model = ModelTest(name="test", value=123)
    mtime_ns = test_path.stat().st_mtime_ns

    model_cache.set_model(test_path, model, mtime_ns)
    cached_model = model_cache.get_model(test_path, ModelTest)

    assert cached_model is not None
    assert cached_model.name == "test"
    assert cached_model.value == 123


def test_invalidate_model(model_cache, test_path):
    model = ModelTest(name="test", value=123)
    mtime = test_path.stat().st_mtime

    model_cache.set_model(test_path, model, mtime)
    model_cache.invalidate(test_path)
    cached_model = model_cache.get_model(test_path, ModelTest)

    assert cached_model is None


def test_clear_cache(model_cache, test_path):
    model = ModelTest(name="test", value=123)
    mtime = test_path.stat().st_mtime

    model_cache.set_model(test_path, model, mtime)
    model_cache.clear()
    cached_model = model_cache.get_model(test_path, ModelTest)

    assert cached_model is None


def test_cache_invalid_due_to_mtime_change(model_cache, test_path):
    model = ModelTest(name="test", value=123)
    mtime = test_path.stat().st_mtime

    model_cache.set_model(test_path, model, mtime)

    # Simulate a file modification by updating the mtime
    test_path.touch()
    cached_model = model_cache.get_model(test_path, ModelTest)

    assert cached_model is None


def test_get_model_wrong_type(model_cache, test_path):
    class AnotherModel(BaseModel):
        other_field: str

    model = ModelTest(name="test", value=123)
    mtime_ns = test_path.stat().st_mtime_ns

    model_cache.set_model(test_path, model, mtime_ns)

    with pytest.raises(ValueError):
        model_cache.get_model(test_path, AnotherModel)

    # Test that the cache invalidates
    cached_model = model_cache.get_model(test_path, ModelTest)
    assert cached_model is None


def test_is_cache_valid_true(model_cache, test_path):
    mtime_ns = test_path.stat().st_mtime_ns
    assert model_cache._is_cache_valid(test_path, mtime_ns) is True


def test_is_cache_valid_false_due_to_mtime_change(model_cache, test_path):
    mtime_ns = test_path.stat().st_mtime_ns
    # Simulate a file modification by updating the mtime
    test_path.touch()
    assert model_cache._is_cache_valid(test_path, mtime_ns) is False


def test_is_cache_valid_false_due_to_missing_file(model_cache):
    non_existent_path = Path("/non/existent/path")
    assert model_cache._is_cache_valid(non_existent_path, 0) is False


def test_benchmark_get_model(benchmark, model_cache, test_path):
    model = ModelTest(name="test", value=123)
    mtime = test_path.stat().st_mtime

    # Set the model in the cache
    model_cache.set_model(test_path, model, mtime)

    # Benchmark the get_model method
    def get_model():
        return model_cache.get_model(test_path, ModelTest)

    benchmark(get_model)
    stats = benchmark.stats.stats

    # 25k ops per second is the target. Getting 250k on Macbook, but CI will be slower
    target = 1 / 25000
    if stats.mean > target:
        pytest.fail(
            f"Average time per iteration: {stats.mean}, expected less than {target}"
        )


def test_get_model_returns_copy(model_cache, test_path):
    model = ModelTest(name="test", value=123)
    mtime_ns = test_path.stat().st_mtime_ns

    # Set the model in the cache
    model_cache.set_model(test_path, model, mtime_ns)

    # Get a copy of the model from the cache
    cached_model = model_cache.get_model(test_path, ModelTest)

    # Different instance (is), same data (==)
    assert cached_model is not model
    assert cached_model == model

    # Mutate the cached model
    cached_model.name = "mutated"

    # Get the model again from the cache
    new_cached_model = model_cache.get_model(test_path, ModelTest)

    # Assert that the new cached model has the original values
    assert new_cached_model == model
    assert new_cached_model.name == "test"

    # Save the mutated model back to the cache
    model_cache.set_model(test_path, cached_model, mtime_ns)

    # Get the model again from the cache
    updated_cached_model = model_cache.get_model(test_path, ModelTest)

    # Assert that the updated cached model has the mutated values
    assert updated_cached_model.name == "mutated"
    assert updated_cached_model.value == 123


def test_no_cache_when_no_fine_granularity(model_cache, test_path):
    model = ModelTest(name="test", value=123)
    mtime_ns = test_path.stat().st_mtime_ns

    model_cache._has_fine_granularity = False
    model_cache.set_model(test_path, model, mtime_ns)
    cached_model = model_cache.get_model(test_path, ModelTest)

    # Assert that the model is not cached
    assert cached_model is None
    assert model_cache.model_cache == {}
