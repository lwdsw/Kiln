from pathlib import Path

import pytest
from pydantic import BaseModel

from libs.core.kiln_ai.datamodel.model_cache import ModelCache


# Define a simple Pydantic model for testing
class TestModel(BaseModel):
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
    model = TestModel(name="test", value=123)
    mtime = test_path.stat().st_mtime

    model_cache.set_model(test_path, model, mtime)
    cached_model = model_cache.get_model(test_path, TestModel)

    assert cached_model is not None
    assert cached_model.name == "test"
    assert cached_model.value == 123


def test_invalidate_model(model_cache, test_path):
    model = TestModel(name="test", value=123)
    mtime = test_path.stat().st_mtime

    model_cache.set_model(test_path, model, mtime)
    model_cache.invalidate(test_path)
    cached_model = model_cache.get_model(test_path, TestModel)

    assert cached_model is None


def test_clear_cache(model_cache, test_path):
    model = TestModel(name="test", value=123)
    mtime = test_path.stat().st_mtime

    model_cache.set_model(test_path, model, mtime)
    model_cache.clear()
    cached_model = model_cache.get_model(test_path, TestModel)

    assert cached_model is None


def test_cache_invalid_due_to_mtime_change(model_cache, test_path):
    model = TestModel(name="test", value=123)
    mtime = test_path.stat().st_mtime

    model_cache.set_model(test_path, model, mtime)

    # Simulate a file modification by updating the mtime
    test_path.touch()
    cached_model = model_cache.get_model(test_path, TestModel)

    assert cached_model is None


def test_get_model_wrong_type(model_cache, test_path):
    class AnotherModel(BaseModel):
        other_field: str

    model = TestModel(name="test", value=123)
    mtime = test_path.stat().st_mtime

    model_cache.set_model(test_path, model, mtime)

    with pytest.raises(ValueError):
        model_cache.get_model(test_path, AnotherModel)

    # Test that the cache invalidates
    cached_model = model_cache.get_model(test_path, TestModel)
    assert cached_model is None


def test_is_cache_valid_true(model_cache, test_path):
    mtime = test_path.stat().st_mtime
    assert model_cache._is_cache_valid(test_path, mtime) is True


def test_is_cache_valid_false_due_to_mtime_change(model_cache, test_path):
    mtime = test_path.stat().st_mtime
    # Simulate a file modification by updating the mtime
    test_path.touch()
    assert model_cache._is_cache_valid(test_path, mtime) is False


def test_is_cache_valid_false_due_to_missing_file(model_cache):
    non_existent_path = Path("/non/existent/path")
    assert model_cache._is_cache_valid(non_existent_path, 0) is False
