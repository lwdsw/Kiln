from fastapi import FastAPI
from kiln_ai.datamodel import DatasetSplit, Finetune
from kiln_server.task_api import task_from_id


def connect_fine_tune_api(app: FastAPI):
    @app.get("/api/projects/{project_id}/tasks/{task_id}/dataset_splits")
    async def dataset_splits(project_id: str, task_id: str) -> list[DatasetSplit]:
        task = task_from_id(project_id, task_id)
        return task.dataset_splits()

    @app.get("/api/projects/{project_id}/tasks/{task_id}/finetunes")
    async def finetunes(project_id: str, task_id: str) -> list[Finetune]:
        task = task_from_id(project_id, task_id)
        return task.finetunes()
