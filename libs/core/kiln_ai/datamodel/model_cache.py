"""
A simple cache for our basemodel.

Works at the file level, caching the pydantic model based on the file path.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional, Type

from pydantic import BaseModel


class ModelCache:
    _shared_instance = None

    def __init__(self):
        self.model_cache: Dict[Path, BaseModel] = {}

    @classmethod
    def shared(cls):
        if cls._shared_instance is None:
            cls._shared_instance = cls()
        return cls._shared_instance

    def get_model(self, path: Path, model_type: Type[BaseModel]) -> BaseModel:
        if path not in self.model_cache:
            return None
        model = self.model_cache[path]
        if not isinstance(model, model_type):
            raise ValueError(f"Model at {path} is not of type {model_type.__name__}")
        return model

    def set_model(self, path: Path, model: BaseModel):
        self.model_cache[path] = model

    def invalidate(self, path: Path):
        if path in self.model_cache:
            del self.model_cache[path]

    def clear(self):
        self.model_cache.clear()
