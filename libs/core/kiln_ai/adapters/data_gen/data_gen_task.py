import json

from kiln_ai.adapters.prompt_builders import SimplePromptBuilder
from kiln_ai.datamodel import Project, Task
from pydantic import BaseModel

from .data_gen_prompts import TREE_GENERATION_PROMPT


class DataGenCategoriesTaskInput(BaseModel):
    node_path: list[str]
    system_prompt: str
    num_subtopics: int
    human_guidance: str | None = None

    @classmethod
    def from_task(
        cls,
        task: Task,
        node_path: list[str] = [],
        num_subtopics: int = 6,
        human_guidance: str | None = None,
    ) -> "DataGenCategoriesTaskInput":
        prompt_builder = SimplePromptBuilder(task=task)
        return cls(
            node_path=node_path,
            num_subtopics=num_subtopics,
            human_guidance=human_guidance,
            system_prompt=prompt_builder.build_prompt(),
        )


class DataGenCategoriesTaskOutput(BaseModel):
    categories: list[str]


class DataGenCategoriesTask(Task, parent_of={}):
    def __init__(self):
        # Keep the typechecker happy. TODO: shouldn't need this or parent_of above.
        tmp_project = Project(name="DataGen")
        super().__init__(
            name="DataGen",
            parent=tmp_project,
            description="A task which generates synthetic data categories, which in turn are used to generate training data for a model to learn from.",
            instruction=TREE_GENERATION_PROMPT,
            requirements=[],
            input_json_schema=json.dumps(
                DataGenCategoriesTaskInput.model_json_schema()
            ),
            output_json_schema=json.dumps(
                DataGenCategoriesTaskOutput.model_json_schema()
            ),
        )
