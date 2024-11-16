import pytest
from kiln_ai.adapters.data_gen.data_gen_task import (
    DataGenCategoriesTask,
    DataGenCategoriesTaskInput,
    DataGenCategoriesTaskOutput,
)
from kiln_ai.datamodel import Project, Task


@pytest.fixture
def base_task():
    project = Project(name="TestProject")
    return Task(
        name="TestTask",
        parent=project,
        description="Test description",
        instruction="Test instruction",
        requirements=[],
    )


def test_data_gen_categories_task_input_initialization(base_task):
    # Arrange
    node_path = ["root", "branch", "leaf"]
    num_subtopics = 4
    human_guidance = "Test guidance"

    # Act
    input_model = DataGenCategoriesTaskInput.from_task(
        task=base_task,
        node_path=node_path,
        num_subtopics=num_subtopics,
        human_guidance=human_guidance,
    )

    # Assert
    assert input_model.node_path == node_path
    assert input_model.num_subtopics == num_subtopics
    assert input_model.human_guidance == human_guidance
    assert isinstance(input_model.system_prompt, str)
    assert "Test instruction" in input_model.system_prompt


def test_data_gen_categories_task_input_default_values(base_task):
    # Act
    input_model = DataGenCategoriesTaskInput.from_task(task=base_task)

    # Assert
    assert input_model.num_subtopics == 6
    assert input_model.human_guidance is None
    assert input_model.node_path == []


def test_data_gen_categories_task_output_validation():
    # Arrange & Act
    output = DataGenCategoriesTaskOutput(categories=["cat1", "cat2", "cat3"])

    # Assert
    assert len(output.categories) == 3
    assert all(isinstance(cat, str) for cat in output.categories)


def test_data_gen_categories_task_initialization():
    # Act
    task = DataGenCategoriesTask()

    # Assert
    assert task.name == "DataGen"
    assert isinstance(task.parent, Project)
    assert task.description is not None
    assert task.instruction is not None
    assert isinstance(task.input_json_schema, str)
    assert isinstance(task.output_json_schema, str)


def test_data_gen_categories_task_schemas():
    # Act
    task = DataGenCategoriesTask()

    # Assert
    # Verify that the schemas are valid JSON
    import json

    input_schema = json.loads(task.input_json_schema)
    output_schema = json.loads(task.output_json_schema)

    assert isinstance(input_schema, dict)
    assert isinstance(output_schema, dict)
    assert output_schema["type"] == "object"
    assert output_schema["properties"]["categories"]["type"] == "array"
    assert input_schema["properties"]["node_path"]["type"] == "array"
    assert input_schema["properties"]["num_subtopics"]["type"] == "integer"
    assert set(input_schema["required"]) == {
        "node_path",
        "num_subtopics",
        "system_prompt",
    }
