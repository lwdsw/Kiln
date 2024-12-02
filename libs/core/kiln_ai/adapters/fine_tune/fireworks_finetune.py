import httpx

from kiln_ai.adapters.fine_tune.base_finetune import (
    BaseFinetuneAdapter,
    FineTuneStatus,
    FineTuneStatusType,
)
from kiln_ai.datamodel import DatasetSplit
from kiln_ai.utils.config import Config


class FireworksFinetune(BaseFinetuneAdapter):
    """
    A fine-tuning adapter for Fireworks.
    """

    async def status(self) -> FineTuneStatus:
        status = await self._status()
        # update the datamodel if the status has changed
        if self.datamodel.latest_status != status.status:
            self.datamodel.latest_status = status.status
            if self.datamodel.path:
                await self.datamodel.save_to_path(self.datamodel.path)
        return status

    async def _status(self) -> FineTuneStatus:
        try:
            api_key = Config.shared().fireworks_api_key
            account_id = Config.shared().fireworks_account_id
            if not api_key or not account_id:
                return FineTuneStatus(
                    status=FineTuneStatusType.unknown,
                    message="Fireworks API key or account ID not set",
                )
            fine_tuning_job_id = self.datamodel.provider_id
            if not fine_tuning_job_id:
                return FineTuneStatus(
                    status=FineTuneStatusType.unknown,
                    message="Fine-tuning job ID not set. Can not retrieve status.",
                )
            url = f"https://api.fireworks.ai/v1/accounts/{account_id}/fineTuningJobs/{fine_tuning_job_id}"
            headers = {"Authorization": f"Bearer {api_key}"}

            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, timeout=15.0)

            if response.status_code != 200:
                return FineTuneStatus(
                    status=FineTuneStatusType.unknown,
                    message=f"Error retrieving fine-tuning job status: [{response.status_code}] {response.text}",
                )
            data = response.json()

            if "state" not in data:
                return FineTuneStatus(
                    status=FineTuneStatusType.unknown,
                    message="Invalid response from Fireworks (no state).",
                )

            state = data["state"]
            if state in ["FAILED", "DELETING"]:
                return FineTuneStatus(
                    status=FineTuneStatusType.failed,
                    message="Fine-tuning job failed",
                )
            elif state in ["CREATING", "PENDING", "RUNNING"]:
                return FineTuneStatus(
                    status=FineTuneStatusType.running,
                    message=f"Fine-tuning job is running [{state}]",
                )
            elif state == "COMPLETED":
                return FineTuneStatus(
                    status=FineTuneStatusType.completed,
                    message="Fine-tuning job completed",
                )
            else:
                return FineTuneStatus(
                    status=FineTuneStatusType.unknown,
                    message=f"Unknown fine-tuning job status [{state}]",
                )
        except Exception as e:
            return FineTuneStatus(
                status=FineTuneStatusType.unknown,
                message=f"Error retrieving fine-tuning job status: {e}",
            )

    async def _start(self, dataset: DatasetSplit) -> None:
        # TODO: Implement
        pass
