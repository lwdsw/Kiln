import time

import openai
from openai.types.fine_tuning import FineTuningJob

from kiln_ai.adapters.fine_tune.base_finetune import (
    BaseFinetune,
    FineTuneParameter,
    FineTuneStatus,
    FineTuneStatusType,
)
from kiln_ai.utils.config import Config

oai_client = openai.OpenAI(
    api_key=Config.shared().open_ai_api_key,
)


class OpenAIFinetune(BaseFinetune):
    def status(self) -> FineTuneStatus:
        if not self.provider_id:
            return FineTuneStatus(
                status=FineTuneStatusType.pending,
                message="This fine-tune has not been started or has not been assigned a provider ID.",
            )

        try:
            # Will raise an error if the job is not found, or for other issues
            response = oai_client.fine_tuning.jobs.retrieve(self.provider_id)
        except openai.APIConnectionError:
            return FineTuneStatus(
                status=FineTuneStatusType.unknown, message="Server connection error"
            )
        except openai.RateLimitError:
            return FineTuneStatus(
                status=FineTuneStatusType.unknown,
                message="Rate limit exceeded. Could not fetch fine-tune status.",
            )
        except openai.APIStatusError as e:
            if e.status_code == 404:
                return FineTuneStatus(
                    status=FineTuneStatusType.failed,
                    message="Job with this ID not found. It may have been deleted.",
                )
            return FineTuneStatus(
                status=FineTuneStatusType.unknown,
                message=f"Unknown error: [{str(e)}]",
            )

        if not response or not isinstance(response, FineTuningJob):
            return FineTuneStatus(
                status=FineTuneStatusType.unknown,
                message="Invalid response from OpenAI",
            )
        if response.error is not None:
            return FineTuneStatus(
                status=FineTuneStatusType.failed,
                message=response.error.message,
            )
        status = response.status
        if status == "failed":
            return FineTuneStatus(
                status=FineTuneStatusType.failed,
                message="Job failed - unknown reason",
            )
        if status == "cancelled":
            return FineTuneStatus(
                status=FineTuneStatusType.failed, message="Job cancelled"
            )
        if (
            status in ["validating_files", "running", "queued"]
            or response.finished_at is None
            or response.estimated_finish is not None
        ):
            time_to_finish_msg: str | None = None
            if response.estimated_finish is not None:
                time_to_finish_msg = f"Estimated finish time: {int(response.estimated_finish - time.time())} seconds."
            return FineTuneStatus(
                status=FineTuneStatusType.running,
                message=f"Job is still running [{status}]. {time_to_finish_msg or ''}",
            )
        if status == "succeeded":
            return FineTuneStatus(
                status=FineTuneStatusType.completed, message="Job completed"
            )
        return FineTuneStatus(
            status=FineTuneStatusType.unknown,
            message=f"Unknown status: [{status}]",
        )

    def start(self) -> None:
        # TODO: Implement this
        return None

    @classmethod
    def available_parameters(cls) -> list[FineTuneParameter]:
        return [
            FineTuneParameter(
                name="batch_size",
                type="int",
                description="Number of examples in each batch. A larger batch size means that model parameters are updated less frequently, but with lower variance. Defaults to 'auto'",
            ),
            FineTuneParameter(
                name="learning_rate_multiplier",
                type="float",
                description="Scaling factor for the learning rate. A smaller learning rate may be useful to avoid overfitting. Defaults to 'auto'",
                optional=True,
            ),
            FineTuneParameter(
                name="n_epochs",
                type="int",
                description="The number of epochs to train the model for. An epoch refers to one full cycle through the training dataset. Defaults to 'auto'",
                optional=True,
            ),
            FineTuneParameter(
                name="seed",
                type="int",
                description="The seed controls the reproducibility of the job. Passing in the same seed and job parameters should produce the same results, but may differ in rare cases. If a seed is not specified, one will be generated for you.",
                optional=True,
            ),
        ]
