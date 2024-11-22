from kiln_ai.adapters.fine_tune.base_finetune import BaseFinetune, FineTuneParameter


class OpenAIFinetune(BaseFinetune):
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
