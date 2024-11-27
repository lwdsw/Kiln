import json
import tempfile
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Protocol

from kiln_ai.datamodel import DatasetSplit, TaskRun


class DatasetFormat(str, Enum):
    """Format types for dataset generation"""

    CHAT_MESSAGE_RESPONSE_JSONL = "chat_message_response_jsonl"
    CHAT_MESSAGE_TOOLCALL_JSONL = "chat_message_toolcall_jsonl"


class FormatGenerator(Protocol):
    """Protocol for format generators"""

    def __call__(self, task_run: TaskRun, system_message: str) -> Dict[str, Any]: ...


def generate_chat_message_response(
    task_run: TaskRun, system_message: str
) -> Dict[str, Any]:
    """Generate OpenAI chat format with plaintext response"""
    return {
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": task_run.input},
            {"role": "assistant", "content": task_run.output.output},
        ]
    }


def generate_chat_message_toolcall(
    task_run: TaskRun, system_message: str
) -> Dict[str, Any]:
    """Generate OpenAI chat format with tool call response"""
    try:
        arguments = json.loads(task_run.output.output)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in task run output: {e}") from e

    return {
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": task_run.input},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_1",
                        "type": "function",
                        "function": {
                            "name": "task_response",
                            "arguments": json.dumps(arguments),
                        },
                    }
                ],
            },
        ]
    }


FORMAT_GENERATORS: Dict[DatasetFormat, FormatGenerator] = {
    DatasetFormat.CHAT_MESSAGE_RESPONSE_JSONL: generate_chat_message_response,
    DatasetFormat.CHAT_MESSAGE_TOOLCALL_JSONL: generate_chat_message_toolcall,
}


class DatasetFormatter:
    """Handles formatting of datasets into various output formats"""

    def __init__(self, dataset: DatasetSplit, system_message: str):
        self.dataset = dataset
        self.system_message = system_message

        task = dataset.parent_task()
        if task is None:
            raise ValueError("Dataset has no parent task")
        self.task = task

    def dump_to_file(
        self, split_name: str, format_type: DatasetFormat, path: Path | None = None
    ) -> Path:
        """
        Format the dataset into the specified format.

        Args:
            split_name: Name of the split to dump
            format_type: Format to generate the dataset in
            path: Optional path to write to. If None, writes to temp directory

        Returns:
            Path to the generated file
        """
        if format_type not in FORMAT_GENERATORS:
            raise ValueError(f"Unsupported format: {format_type}")
        if split_name not in self.dataset.split_contents:
            raise ValueError(f"Split {split_name} not found in dataset")

        generator = FORMAT_GENERATORS[format_type]

        # Write to a temp file if no path is provided
        output_path = (
            path
            or Path(tempfile.gettempdir())
            / f"{self.dataset.name}_{split_name}_{format_type}.jsonl"
        )

        runs = self.task.runs()
        runs_by_id = {run.id: run for run in runs}

        # Generate formatted output with UTF-8 encoding
        with open(output_path, "w", encoding="utf-8") as f:
            for run_id in self.dataset.split_contents[split_name]:
                task_run = runs_by_id[run_id]
                if task_run is None:
                    raise ValueError(
                        f"Task run {run_id} not found. This is required by this dataset."
                    )

                example = generator(task_run, self.system_message)
                f.write(json.dumps(example) + "\n")

        return output_path
