from fastapi import FastAPI
from kiln_ai.adapters.data_gen.data_gen_task import (
    DataGenCategoriesTask,
    DataGenCategoriesTaskInput,
    DataGenSampleTask,
    DataGenSampleTaskInput,
)
from kiln_ai.adapters.langchain_adapters import LangChainPromptAdapter
from kiln_ai.datamodel import TaskRun
from kiln_server.task_api import task_from_id
from pydantic import BaseModel, ConfigDict, Field


class DataGenCategoriesApiInput(BaseModel):
    node_path: list[str] = Field(
        description="Path to the node in the category tree", default=[]
    )
    num_subtopics: int = Field(description="Number of subtopics to generate", default=6)
    human_guidance: str | None = Field(
        description="Optional human guidance for generation",
        default=None,
    )
    model_name: str = Field(description="The name of the model to use")
    provider: str = Field(description="The provider of the model to use")

    # Allows use of the model_name field (usually pydantic will reserve model_*)
    model_config = ConfigDict(protected_namespaces=())


class DataGenSampleApiInput(BaseModel):
    topic: list[str] = Field(description="Topic path for sample generation", default=[])
    num_samples: int = Field(description="Number of samples to generate", default=8)
    human_guidance: str | None = Field(
        description="Optional human guidance for generation",
        default=None,
    )
    model_name: str = Field(description="The name of the model to use")
    provider: str = Field(description="The provider of the model to use")

    # Allows use of the model_name field (usually pydantic will reserve model_*)
    model_config = ConfigDict(protected_namespaces=())


def connect_data_gen_api(app: FastAPI):
    @app.post("/api/projects/{project_id}/tasks/{task_id}/generate_categories")
    async def generate_categories(
        project_id: str, task_id: str, input: DataGenCategoriesApiInput
    ) -> TaskRun:
        task = task_from_id(project_id, task_id)
        categories_task = DataGenCategoriesTask()

        task_input = DataGenCategoriesTaskInput.from_task(
            task=task,
            node_path=input.node_path,
            num_subtopics=input.num_subtopics,
            human_guidance=input.human_guidance,
        )

        adapter = LangChainPromptAdapter(
            categories_task,
            model_name=input.model_name,
            provider=input.provider,
        )

        categories_run = await adapter.invoke(task_input.model_dump())
        return categories_run

    @app.post("/api/projects/{project_id}/tasks/{task_id}/generate_samples")
    async def generate_samples(
        project_id: str, task_id: str, input: DataGenSampleApiInput
    ) -> TaskRun:
        task = task_from_id(project_id, task_id)
        sample_task = DataGenSampleTask(target_task=task, num_samples=input.num_samples)

        task_input = DataGenSampleTaskInput.from_task(
            task=task,
            topic=input.topic,
            num_samples=input.num_samples,
            human_guidance=input.human_guidance,
        )

        adapter = LangChainPromptAdapter(
            sample_task,
            model_name=input.model_name,
            provider=input.provider,
        )

        samples_run = await adapter.invoke(task_input.model_dump())
        return samples_run
