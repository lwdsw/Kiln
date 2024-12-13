from __future__ import annotations

import json
import math
import random
from enum import Enum, IntEnum
from typing import TYPE_CHECKING, Callable, Dict, List, Type, Union

import jsonschema
import jsonschema.exceptions
from pydantic import (
    BaseModel,
    Field,
    ValidationInfo,
    model_validator,
)
from typing_extensions import Self

from kiln_ai.datamodel.json_schema import JsonObjectSchema, schema_from_json_str

from .basemodel import (
    ID_FIELD,
    ID_TYPE,
    NAME_FIELD,
    SHORT_NAME_FIELD,
    KilnBaseModel,
    KilnParentedModel,
    KilnParentModel,
)
from .json_schema import validate_schema

if TYPE_CHECKING:
    from . import Task


__all__ = [
    "basemodel",
    "json_schema",
    "Task",
    "Project",
    "TaskRun",
    "TaskOutput",
    "TaskOutputRating",
    "Priority",
    "DataSource",
    "DataSourceType",
    "DataSourceProperty",
    "TaskOutputRatingType",
    "TaskRequirement",
    "TaskDeterminism",
    "strict_mode",
    "set_strict_mode",
]


# We want to be hard on ourselves for data completeness generated by the Kiln App, but don't want to make it hard for users to use the datamodel/library.
# Strict mode enables extra validations that we want to enforce in Kiln App (and any other client that wants best practices), but not in the library (unless they opt in)
_strict_mode = False


def strict_mode() -> bool:
    return _strict_mode


def set_strict_mode(value: bool) -> None:
    _strict_mode = value


class Priority(IntEnum):
    """Defines priority levels for tasks and requirements, where P0 is highest priority."""

    p0 = 0
    p1 = 1
    p2 = 2
    p3 = 3


# Only one rating type for now, but this allows for extensibility if we want to add more in the future
class TaskOutputRatingType(str, Enum):
    """Defines the types of rating systems available for task outputs."""

    five_star = "five_star"
    custom = "custom"


class TaskOutputRating(KilnBaseModel):
    """
    A rating for a task output, including an overall rating and ratings for each requirement.

    Only supports five star ratings for now, but extensible for custom values.
    """

    type: TaskOutputRatingType = Field(default=TaskOutputRatingType.five_star)
    value: float | None = Field(
        description="The overall rating value (typically 1-5 stars).",
        default=None,
    )
    requirement_ratings: Dict[ID_TYPE, float] = Field(
        default={},
        description="The ratings of the requirements of the task. The keys are the ids of the requirements. The values are the ratings (typically 1-5 stars).",
    )

    # Used to select high quality outputs for example selection (MultiShotPromptBuilder, etc)
    def is_high_quality(self) -> bool:
        if self.type == TaskOutputRatingType.five_star:
            return self.value is not None and self.value >= 4
        return False

    @model_validator(mode="after")
    def validate_rating(self) -> Self:
        if self.type not in TaskOutputRatingType:
            raise ValueError(f"Invalid rating type: {self.type}")

        if self.type == TaskOutputRatingType.five_star:
            if self.value is not None:
                self._validate_five_star(self.value, "overall rating")
            for req_id, req_rating in self.requirement_ratings.items():
                self._validate_five_star(req_rating, f"requirement rating for {req_id}")

        return self

    def _validate_five_star(self, rating: float, rating_name: str) -> None:
        if not isinstance(rating, float) or not rating.is_integer():
            raise ValueError(
                f"{rating_name.capitalize()} of type five_star must be an integer value (1.0, 2.0, 3.0, 4.0, or 5.0)"
            )
        if rating < 1 or rating > 5:
            raise ValueError(
                f"{rating_name.capitalize()} of type five_star must be between 1 and 5 stars"
            )


class TaskOutput(KilnBaseModel):
    """
    An output for a specific task run.

    Contains the actual output content, its source (human or synthetic),
    and optional rating information.
    """

    output: str = Field(
        description="The output of the task. JSON formatted for structured output, plaintext for unstructured output."
    )
    source: DataSource | None = Field(
        description="The source of the output: human or synthetic.",
        default=None,
    )
    rating: TaskOutputRating | None = Field(
        default=None, description="The rating of the output"
    )

    def validate_output_format(self, task: Task) -> Self:
        # validate output
        if task.output_json_schema is not None:
            try:
                validate_schema(json.loads(self.output), task.output_json_schema)
            except json.JSONDecodeError:
                raise ValueError("Output is not a valid JSON object")
            except jsonschema.exceptions.ValidationError as e:
                raise ValueError(f"Output does not match task output schema: {e}")
        return self

    @model_validator(mode="after")
    def validate_output_source(self, info: ValidationInfo) -> Self:
        # On strict mode and not loaded from file, we validate output_source is not None.
        # We want to be able to load any data, even if it's not perfect. But we want to create perfect data when adding new data.
        if not strict_mode():
            return self
        if self.loaded_from_file(info):
            return self
        if self.source is None:
            raise ValueError("Output source is required when strict mode is enabled")
        return self


class FineTuneStatusType(str, Enum):
    """
    The status type of a fine-tune (running, completed, failed, etc).
    """

    unknown = "unknown"  # server error
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class Finetune(KilnParentedModel):
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
        description="The ID of the fine-tune job on the provider's side. May not be the same as the fine_tune_model_id.",
    )
    fine_tune_model_id: str | None = Field(
        default=None,
        description="The ID of the fine-tuned model on the provider's side. May not be the same as the provider_id.",
    )
    dataset_split_id: str = Field(
        description="The ID of the dataset split to use for this fine-tune.",
    )
    train_split_name: str = Field(
        default="train",
        description="The name of the training split to use for this fine-tune.",
    )
    validation_split_name: str | None = Field(
        default=None,
        description="The name of the validation split to use for this fine-tune. Optional.",
    )
    parameters: dict[str, str | int | float | bool] = Field(
        default={},
        description="The parameters to use for this fine-tune. These are provider-specific.",
    )
    system_message: str = Field(
        description="The system message to use for this fine-tune.",
    )
    latest_status: FineTuneStatusType = Field(
        default=FineTuneStatusType.unknown,
        description="The latest known status of this fine-tune. Not updated in real time.",
    )
    properties: Dict[str, str | int | float] = Field(
        default={},
        description="Properties of the fine-tune. Different providers may use different properties.",
    )

    def parent_task(self) -> Task | None:
        if not isinstance(self.parent, Task):
            return None
        return self.parent


class DataSourceType(str, Enum):
    """
    The source type of a piece of data.

    Human: a human created the data
    Synthetic: a model created the data
    """

    human = "human"
    synthetic = "synthetic"


class DataSourceProperty(BaseModel):
    """
    Defines a property that can be associated with a data source.

    Includes validation rules for when properties are required or not allowed
    based on the data source type.
    """

    name: str
    type: Type[Union[str, int, float]]
    required_for: List[DataSourceType] = []
    not_allowed_for: List[DataSourceType] = []


class DataSource(BaseModel):
    """
    Represents the origin of data, either human or synthetic, with associated properties.

    Properties vary based on the source type - for synthetic sources this includes
    model information, for human sources this includes creator information.
    """

    type: DataSourceType
    properties: Dict[str, str | int | float] = Field(
        default={},
        description="Properties describing the data source. For synthetic things like model. For human, the human's name.",
    )

    _data_source_properties = [
        DataSourceProperty(
            name="created_by",
            type=str,
            required_for=[DataSourceType.human],
            not_allowed_for=[DataSourceType.synthetic],
        ),
        DataSourceProperty(
            name="model_name",
            type=str,
            required_for=[DataSourceType.synthetic],
            not_allowed_for=[DataSourceType.human],
        ),
        DataSourceProperty(
            name="model_provider",
            type=str,
            required_for=[DataSourceType.synthetic],
            not_allowed_for=[DataSourceType.human],
        ),
        DataSourceProperty(
            name="adapter_name",
            type=str,
            required_for=[DataSourceType.synthetic],
            not_allowed_for=[DataSourceType.human],
        ),
        DataSourceProperty(
            name="prompt_builder_name",
            type=str,
            not_allowed_for=[DataSourceType.human],
        ),
    ]

    @model_validator(mode="after")
    def validate_type(self) -> "DataSource":
        if self.type not in DataSourceType:
            raise ValueError(f"Invalid data source type: {self.type}")
        return self

    @model_validator(mode="after")
    def validate_properties(self) -> "DataSource":
        for prop in self._data_source_properties:
            # Check the property type is correct
            if prop.name in self.properties:
                if not isinstance(self.properties[prop.name], prop.type):
                    raise ValueError(
                        f"'{prop.name}' must be of type {prop.type.__name__} for {self.type} data source"
                    )
            # Check the property is required for the data source type
            if self.type in prop.required_for:
                if prop.name not in self.properties:
                    raise ValueError(
                        f"'{prop.name}' is required for {self.type} data source"
                    )
            # Check the property is not allowed for the data source type
            elif self.type in prop.not_allowed_for and prop.name in self.properties:
                raise ValueError(
                    f"'{prop.name}' is not allowed for {self.type} data source"
                )
        return self

    @model_validator(mode="after")
    def validate_no_empty_properties(self) -> Self:
        for prop, value in self.properties.items():
            if isinstance(value, str) and value == "":
                raise ValueError(
                    f"Property '{prop}' must be a non-empty string for {self.type} data source"
                )
        return self


class TaskRun(KilnParentedModel):
    """
    Represents a single execution of a Task.

    Contains the input used, its source, the output produced, and optional
    repair information if the output needed correction.
    """

    input: str = Field(
        description="The inputs to the task. JSON formatted for structured input, plaintext for unstructured input."
    )
    input_source: DataSource | None = Field(
        default=None, description="The source of the input: human or synthetic."
    )

    output: TaskOutput = Field(description="The output of the task run.")
    repair_instructions: str | None = Field(
        default=None,
        description="Instructions for fixing the output. Should define what is wrong, and how to fix it. Will be used by models for both generating a fixed output, and evaluating future models.",
    )
    repaired_output: TaskOutput | None = Field(
        default=None,
        description="An version of the output with issues fixed. This must be a 'fixed' version of the existing output, and not an entirely new output. If you wish to generate an ideal curatorial output for this task unrelated to this output, generate a new TaskOutput with type 'human' instead of using this field.",
    )
    intermediate_outputs: Dict[str, str] | None = Field(
        default=None,
        description="Intermediate outputs from the task run. Keys are the names of the intermediate output steps (cot=chain of thought, etc), values are the output data.",
    )

    def parent_task(self) -> Task | None:
        if not isinstance(self.parent, Task):
            return None
        return self.parent

    @model_validator(mode="after")
    def validate_input_format(self) -> Self:
        task = self.parent_task()
        if task is None:
            # don't validate this relationship until we have a path or parent. Give them time to build it (but will catch it before saving)
            return self

        # validate output
        if task.input_json_schema is not None:
            try:
                validate_schema(json.loads(self.input), task.input_json_schema)
            except json.JSONDecodeError:
                raise ValueError("Input is not a valid JSON object")
            except jsonschema.exceptions.ValidationError as e:
                raise ValueError(f"Input does not match task input schema: {e}")
        return self

    @model_validator(mode="after")
    def validate_output_format(self) -> Self:
        task = self.parent_task()
        if task is None:
            return self

        self.output.validate_output_format(task)
        return self

    @model_validator(mode="after")
    def validate_repaired_output(self) -> Self:
        if self.repaired_output is not None:
            if self.repaired_output.rating is not None:
                raise ValueError(
                    "Repaired output rating must be None. Repaired outputs are assumed to have a perfect rating, as they have been fixed."
                )
        if self.repair_instructions is None and self.repaired_output is not None:
            raise ValueError(
                "Repair instructions are required if providing a repaired output."
            )
        if self.repair_instructions is not None and self.repaired_output is None:
            raise ValueError(
                "A repaired output is required if providing repair instructions."
            )
        return self

    @model_validator(mode="after")
    def validate_input_source(self, info: ValidationInfo) -> Self:
        # On strict mode and not loaded from file, we validate input_source is not None.
        # We want to be able to load any data, even if it's not perfect. But we want to create perfect data when adding new data.
        if not strict_mode():
            return self
        if self.loaded_from_file(info):
            return self
        if self.input_source is None:
            raise ValueError("input_source is required when strict mode is enabled")
        return self


# Define the type alias for clarity
DatasetFilter = Callable[[TaskRun], bool]


def AllDatasetFilter(_: TaskRun) -> bool:
    return True


def HighRatingDatasetFilter(task_run: TaskRun) -> bool:
    if task_run.output is None or task_run.output.rating is None:
        return False
    return task_run.output.rating.is_high_quality()


class DatasetSplitDefinition(BaseModel):
    """
    A definition of a split in a dataset.

    Example: name="train", description="The training set", percentage=0.8 (80% of the dataset)
    """

    name: str = NAME_FIELD
    description: str | None = Field(
        default=None,
        description="A description of the dataset for you and your team. Not used in training.",
    )
    percentage: float = Field(
        ge=0.0,
        le=1.0,
        description="The percentage of the dataset that this split represents (between 0 and 1).",
    )


AllSplitDefinition: list[DatasetSplitDefinition] = [
    DatasetSplitDefinition(name="all", percentage=1.0)
]
Train80Test20SplitDefinition: list[DatasetSplitDefinition] = [
    DatasetSplitDefinition(name="train", percentage=0.8),
    DatasetSplitDefinition(name="test", percentage=0.2),
]
Train60Test20Val20SplitDefinition: list[DatasetSplitDefinition] = [
    DatasetSplitDefinition(name="train", percentage=0.6),
    DatasetSplitDefinition(name="test", percentage=0.2),
    DatasetSplitDefinition(name="val", percentage=0.2),
]


class DatasetSplit(KilnParentedModel):
    """
    A collection of task runs, with optional splits (train, test, validation).

    Used to freeze a dataset into train/test/validation splits for repeatable fine-tuning or other tasks.

    Maintains a list of IDs for each split, to avoid data duplication.
    """

    name: str = NAME_FIELD
    description: str | None = Field(
        default=None,
        description="A description of the dataset for you and your team. Not used in training.",
    )
    splits: list[DatasetSplitDefinition] = Field(
        default_factory=list,
        description="The splits in the dataset.",
    )
    split_contents: dict[str, list[str]] = Field(
        description="The contents of each split in the dataset. The key is the split name, and the value is a list of task run IDs.",
    )

    @model_validator(mode="after")
    def validate_split_percentages(self) -> "DatasetSplit":
        total = sum(split.percentage for split in self.splits)
        if not math.isclose(total, 1.0, rel_tol=1e-9):
            raise ValueError(f"The sum of split percentages must be 1.0 (got {total})")
        return self

    @classmethod
    def from_task(
        cls,
        name: str,
        task: "Task",
        splits: list[DatasetSplitDefinition],
        filter: DatasetFilter = AllDatasetFilter,
        description: str | None = None,
    ):
        """
        Build a dataset split from a task.
        """
        split_contents = cls.build_split_contents(task, splits, filter)
        return cls(
            parent=task,
            name=name,
            description=description,
            splits=splits,
            split_contents=split_contents,
        )

    @classmethod
    def build_split_contents(
        cls,
        task: "Task",
        splits: list[DatasetSplitDefinition],
        filter: DatasetFilter,
    ) -> dict[str, list[str]]:
        valid_ids = []
        for task_run in task.runs():
            if filter(task_run):
                valid_ids.append(task_run.id)

        # Shuffle and split by split percentage
        random.shuffle(valid_ids)
        split_contents = {}
        start_idx = 0
        remaining_items = len(valid_ids)

        # Handle all splits except the last one
        for split in splits[:-1]:
            split_size = round(len(valid_ids) * split.percentage)
            split_contents[split.name] = valid_ids[start_idx : start_idx + split_size]
            start_idx += split_size
            remaining_items -= split_size

        # Last split gets all remaining items (for rounding)
        if splits:
            split_contents[splits[-1].name] = valid_ids[start_idx:]

        return split_contents

    def parent_task(self) -> "Task | None":
        # inline import to avoid circular import
        from kiln_ai.datamodel import Task

        if not isinstance(self.parent, Task):
            return None
        return self.parent

    def missing_count(self) -> int:
        """
        Returns:
            int: the number of task runs that have an ID persisted in this dataset split, but no longer exist in the dataset
        """
        parent = self.parent_task()
        if parent is None:
            raise ValueError("DatasetSplit has no parent task")

        runs = parent.runs()
        all_ids = set(run.id for run in runs)
        all_ids_in_splits = set()
        for ids in self.split_contents.values():
            all_ids_in_splits.update(ids)
        missing = all_ids_in_splits - all_ids
        return len(missing)


class TaskRequirement(BaseModel):
    """
    Defines a specific requirement that should be met by task outputs.

    Includes an identifier, name, description, instruction for meeting the requirement,
    and priority level.
    """

    id: ID_TYPE = ID_FIELD
    name: str = SHORT_NAME_FIELD
    description: str | None = Field(default=None)
    instruction: str = Field(min_length=1)
    priority: Priority = Field(default=Priority.p2)


class TaskDeterminism(str, Enum):
    """
    Defines how strictly task outputs should match expected results.

    - deterministic: Requires exact matches
    - semantic_match: Allows different wording with same meaning
    - flexible: Allows variation in both wording and meaning within requirements
    """

    deterministic = "deterministic"  # Expect exact match
    semantic_match = "semantic_match"  # Expect same meaning, but flexible on expression of the meaning
    flexible = "flexible"  # Flexible on semantic output. Eval should be custom based on parsing requirements.


class Task(
    KilnParentedModel,
    KilnParentModel,
    parent_of={
        "runs": TaskRun,
        "dataset_splits": DatasetSplit,
        "finetunes": Finetune,
    },
):
    """
    Represents a specific task to be performed, with associated requirements and validation rules.

    Contains the task definition, requirements, input/output schemas, and maintains
    a collection of task runs.
    """

    name: str = NAME_FIELD
    description: str | None = Field(
        default=None,
        description="A description of the task for you and your team. Will not be used in prompts/training/validation.",
    )
    instruction: str = Field(
        min_length=1,
        description="The instructions for the task. Will be used in prompts/training/validation.",
    )
    requirements: List[TaskRequirement] = Field(default=[])
    output_json_schema: JsonObjectSchema | None = None
    input_json_schema: JsonObjectSchema | None = None
    thinking_instruction: str | None = Field(
        default=None,
        description="Instructions for the model 'thinking' about the requirement prior to answering. Used for chain of thought style prompting.",
    )

    def output_schema(self) -> Dict | None:
        if self.output_json_schema is None:
            return None
        return schema_from_json_str(self.output_json_schema)

    def input_schema(self) -> Dict | None:
        if self.input_json_schema is None:
            return None
        return schema_from_json_str(self.input_json_schema)

    # Needed for typechecking. TODO P2: fix this in KilnParentModel
    def runs(self) -> list[TaskRun]:
        return super().runs()  # type: ignore

    def dataset_splits(self) -> list[DatasetSplit]:
        return super().dataset_splits()  # type: ignore

    def finetunes(self) -> list[Finetune]:
        return super().finetunes()  # type: ignore


class Project(KilnParentModel, parent_of={"tasks": Task}):
    """
    A collection of related tasks.

    Projects organize tasks into logical groups and provide high-level descriptions
    of the overall goals.
    """

    name: str = NAME_FIELD
    description: str | None = Field(
        default=None,
        description="A description of the project for you and your team. Will not be used in prompts/training/validation.",
    )

    # Needed for typechecking. TODO P2: fix this in KilnParentModel
    def tasks(self) -> list[Task]:
        return super().tasks()  # type: ignore
