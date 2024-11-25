import time
from abc import ABC, abstractmethod
from enum import Enum
from typing import Literal

from pydantic import BaseModel

from kiln_ai.adapters.ml_model_list import KilnModelProvider
from kiln_ai.datamodel import DatasetSplit
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


# Add type mapping
TYPE_MAP = {
    "string": str,
    "int": int,
    "float": float,
    "bool": bool,
}


class BaseFinetuneAdapter(ABC):
    """
    A base class for fine-tuning adapters.
    """

    def __init__(
        self,
        datamodel: FinetuneModel,
    ):
        self.datamodel = datamodel

    @classmethod
    def create_and_start(
        cls,
        dataset: DatasetSplit,
        model: KilnModelProvider,
        train_split_name: str,
        parameters: dict[str, str | int | float | bool] = {},
        name: str | None = None,
        description: str | None = None,
        test_split_name: str | None = None,
    ) -> tuple["BaseFinetuneAdapter", FinetuneModel]:
        """
        Create and start a fine-tune.
        """

        # Default name
        if name is None:
            name = f"{model.provider_finetune_id} - {time.strftime('%Y-%m-%d %Hh %Mm %Ss')}"

        if not model.provider_finetune_id:
            raise ValueError(
                "Model must be fine-tuneable (have a provider_finetune_id)"
            )
        if not dataset.id:
            raise ValueError("Dataset must have an id")

        cls.validate_parameters(parameters)
        parent_task = dataset.parent_task()
        if parent_task is None or not parent_task.path:
            raise ValueError("Dataset must have a parent task with a path")

        datamodel = FinetuneModel(
            name=name,
            description=description,
            provider=model.name,
            base_model_id=model.provider_finetune_id,
            dataset_split_id=dataset.id,
            train_split_name=train_split_name,
            test_split_name=test_split_name,
            parameters=parameters,
            parent=parent_task,
        )

        adapter = cls(datamodel)
        adapter._start()

        datamodel.save_to_file()

        return adapter, datamodel

    @abstractmethod
    def _start(self) -> None:
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

    @classmethod
    def validate_parameters(
        cls, parameters: dict[str, str | int | float | bool]
    ) -> None:
        """
        Validate the parameters for this fine-tune.
        """
        # Check required parameters and parameter types
        available_parameters = cls.available_parameters()
        for parameter in available_parameters:
            if not parameter.optional and parameter.name not in parameters:
                raise ValueError(f"Parameter {parameter.name} is required")
            elif parameter.name in parameters:
                # check parameter is correct type
                expected_type = TYPE_MAP[parameter.type]
                value = parameters[parameter.name]

                # Strict type checking for numeric types
                if expected_type is float and not isinstance(value, float):
                    raise ValueError(
                        f"Parameter {parameter.name} must be a float, got {type(value)}"
                    )
                elif expected_type is int and not isinstance(value, int):
                    raise ValueError(
                        f"Parameter {parameter.name} must be an integer, got {type(value)}"
                    )
                elif not isinstance(value, expected_type):
                    raise ValueError(
                        f"Parameter {parameter.name} must be type {expected_type}, got {type(value)}"
                    )

        allowed_parameters = [p.name for p in available_parameters]
        for parameter_key in parameters:
            if parameter_key not in allowed_parameters:
                raise ValueError(f"Parameter {parameter_key} is not available")
