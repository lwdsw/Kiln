from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Literal

from pydantic import Field

from kiln_ai.datamodel.basemodel import NAME_FIELD, KilnParentedModel

if TYPE_CHECKING:
    from kiln_ai.datamodel import Task


class FineTuneStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


@dataclass
class FineTuneParameter:
    name: str
    type: Literal["string", "int", "float", "bool"]
    description: str
    optional: bool = True


class BaseFinetune(KilnParentedModel, ABC):
    name: str = NAME_FIELD
    description: str | None = Field(
        default=None,
        description="A description of the fine-tune for you and your team. Not used in training.",
    )
    provider: str = Field(
        description="The provider to use for the fine-tune (e.g. 'openai')."
    )
    base_model_id: str = Field(
        description="The id of the base model to use for the fine-tune. This string relates to the provider's IDs for their own models, not Kiln IDs."
    )
    provider_id: str | None = Field(
        default=None,
        description="The ID of the fine-tuned model on the provider's side.",
    )
    parameters: dict[str, str | int | float | bool] = Field(
        default_factory=dict,
        description="The parameters to use for this fine-tune. These are provider-specific.",
    )

    def parent_task(self) -> "Task | None":
        # inline import to avoid circular import
        from kiln_ai.datamodel import Task

        if not isinstance(self.parent, Task):
            return None
        return self.parent

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
