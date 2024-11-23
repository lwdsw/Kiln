from abc import ABC, abstractmethod
from enum import Enum
from typing import Literal

from pydantic import BaseModel

from kiln_ai.datamodel import Finetune as FinetuneModel


class FineTuneStatusType(str, Enum):
    """
    The status of a fine-tune.
    """

    unknown = "unknown"  # server error
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class FineTuneStatus(BaseModel):
    status: FineTuneStatusType
    message: str | None = None


class FineTuneParameter(BaseModel):
    name: str
    type: Literal["string", "int", "float", "bool"]
    description: str
    optional: bool = True


class BaseFinetuneAdapter(ABC):
    def __init__(self, model: FinetuneModel):
        self.model = model

    @abstractmethod
    def start(self) -> None:
        pass

    @abstractmethod
    def status(self) -> FineTuneStatus:
        pass

    @classmethod
    def available_parameters(cls) -> list[FineTuneParameter]:
        """
        Returns a list of parameters that can be provided for this fine-tune.
        """
        return []
