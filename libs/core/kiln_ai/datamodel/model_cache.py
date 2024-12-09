"""
A simple cache for our basemodel.

Works at the file level, caching the pydantic model based on the file path.
"""

from pathlib import Path
from typing import Dict, Optional, Tuple, Type, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class ModelCache:
    _shared_instance = None

    def __init__(self):
        # Store both the model and the modified time of the cached file contents
        self.model_cache: Dict[Path, Tuple[BaseModel, float]] = {}

    @classmethod
    def shared(cls):
        if cls._shared_instance is None:
            cls._shared_instance = cls()
        return cls._shared_instance

    def _is_cache_valid(self, path: Path, cached_mtime: float) -> bool:
        try:
            current_mtime = path.stat().st_mtime
        except Exception:
            return False
        return cached_mtime == current_mtime

    def get_model(self, path: Path, model_type: Type[T]) -> Optional[T]:
        if path not in self.model_cache:
            return None
        model, cached_mtime = self.model_cache[path]
        if not self._is_cache_valid(path, cached_mtime):
            self.invalidate(path)
            return None

        if not isinstance(model, model_type):
            self.invalidate(path)
            raise ValueError(f"Model at {path} is not of type {model_type.__name__}")
        return model

    def set_model(self, path: Path, model: BaseModel, mtime: float):
        self.model_cache[path] = (model, mtime)

    def invalidate(self, path: Path):
        if path in self.model_cache:
            del self.model_cache[path]

    def clear(self):
        self.model_cache.clear()
