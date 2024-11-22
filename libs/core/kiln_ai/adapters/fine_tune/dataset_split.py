import math
import random
from typing import TYPE_CHECKING, Callable

from pydantic import BaseModel, Field, model_validator

from kiln_ai.datamodel.basemodel import NAME_FIELD, KilnParentedModel

if TYPE_CHECKING:
    from kiln_ai.datamodel import Task, TaskRun
# Define the type alias for clarity
DatasetFilter = Callable[["TaskRun"], bool]


def AllDatasetFilter(_: "TaskRun") -> bool:
    return True


def HighRatingDatasetFilter(task_run: "TaskRun") -> bool:
    if task_run.output is None or task_run.output.rating is None:
        return False
    return task_run.output.rating.is_high_quality()


class DatasetSplitDefinition(BaseModel):
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


class DatasetSplit(KilnParentedModel):
    """
    A collection of task runs, with optional splits (train, test, validation)

    You probably want to use DatasetSplit class from the datamodel module, which is has relationships to the Task and TaskRun models.
    """

    # TODO: NAME_FIELD
    name: str
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
        task: "Task",
        splits: list[DatasetSplitDefinition],
        filter: DatasetFilter = AllDatasetFilter,
    ):
        split_contents = cls.build_split_contents(task, splits, filter)
        return cls(parent=task, splits=splits, split_contents=split_contents)

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
