from abc import ABC, abstractmethod
from enum import Enum
from typing import Literal

from pydantic import BaseModel

from kiln_ai.datamodel import Finetune as FinetuneModel


class FineTuneStatusType(str, Enum):
    """
    The status type of a fine-tune (running, completed, failed, etc).
    """

    unknown = "unknown"  # server error
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class FineTuneStatus(BaseModel):
    """
    The status of a fine-tune, including a user friendly message.
    """

    status: FineTuneStatusType
    message: str | None = None


class FineTuneParameter(BaseModel):
    """
    A parameter for a fine-tune. Hyperparameters, etc.
    """

    name: str
    type: Literal["string", "int", "float", "bool"]
    description: str
    optional: bool = True


class BaseFinetuneAdapter(ABC):
    """
    A base class for fine-tuning adapters.
    """

    def __init__(
        self,
        datamodel: FinetuneModel,
        train_split_name: str,
        test_split_name: str | None = None,
    ):
        self.datamodel = datamodel
        self.train_split_name = train_split_name
        self.test_split_name = test_split_name

    @abstractmethod
    def start(self) -> None:
        """
        Start the fine-tune.
        """
        pass

    @abstractmethod
    def status(self) -> FineTuneStatus:
        """
        Get the status of the fine-tune.
        """
        pass

    @classmethod
    def available_parameters(cls) -> list[FineTuneParameter]:
        """
        Returns a list of parameters that can be provided for this fine-tune.
        """
        return []
