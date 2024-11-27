<script lang="ts">
  import AppPage from "../../../../app_page.svelte"
  import FormContainer from "$lib/utils/form_container.svelte"
  import FormElement from "$lib/utils/form_element.svelte"
  import { page } from "$app/stores"
  import { client } from "$lib/api_client"
  import { KilnError, createKilnError } from "$lib/utils/error_handlers"
  import { onMount } from "svelte"
  import type {
    FinetuneProvider,
    DatasetSplit,
    FineTuneParameter,
  } from "$lib/types"

  let description = ""
  const disabled_header = "disabled_header"
  let model_provider = disabled_header
  let dataset_id = disabled_header
  let new_dataset_split = disabled_header
  let new_dataset_filter = disabled_header
  let automatic_validation = disabled_header

  // TODO
  model_provider = "openai/gpt-4o"
  //dataset_id = "new"

  $: project_id = $page.params.project_id
  $: task_id = $page.params.task_id

  let available_models: FinetuneProvider[] | null = null
  let available_model_select: [string, string][] = []
  let available_models_error: KilnError | null = null
  let available_models_loading = true

  $: selected_dataset = datasets?.find((d) => d.id === dataset_id)
  $: selected_dataset_has_val = selected_dataset?.splits?.find(
    (s) => s.name === "val",
  )
  $: selected_dataset_training_set_name = selected_dataset?.split_contents[
    "train"
  ]
    ? "train"
    : selected_dataset?.split_contents["all"]
      ? "all"
      : null
  $: step_3_visible =
    model_provider !== disabled_header &&
    !!selected_dataset &&
    (!selected_dataset_has_val || automatic_validation !== disabled_header)
  $: step_3_run_visible =
    !!step_3_visible && !model_provider.startsWith("download_")
  $: step_3_download_visible =
    step_3_visible && model_provider.startsWith("download_")

  $: submit_visible = step_3_run_visible

  onMount(async () => {
    get_available_models()
    get_datasets()
  })

  async function get_available_models() {
    try {
      available_models_loading = true
      if (!project_id || !task_id) {
        throw new Error("Project or task ID not set.")
      }
      const { data: available_models_response, error: get_error } =
        await client.GET("/api/finetune_providers", {})
      if (get_error) {
        throw get_error
      }
      if (!available_models_response) {
        throw new Error("Invalid response from server")
      }
      available_models = available_models_response
      build_available_model_select(available_models)
    } catch (e) {
      if (e instanceof Error && e.message.includes("Load failed")) {
        available_models_error = new KilnError(
          "Could not load available models for fine-tuning.",
          null,
        )
      } else {
        available_models_error = createKilnError(e)
      }
    } finally {
      available_models_loading = false
    }
  }

  function build_available_model_select(models: FinetuneProvider[]) {
    available_model_select = []
    available_model_select.push([
      disabled_header,
      "Select a model to fine-tune",
    ])
    for (const provider of models) {
      for (const model of provider.models) {
        available_model_select.push([
          (provider.enabled ? "" : "disabled_") + provider.id + "/" + model.id,
          provider.name +
            ": " +
            model.name +
            (provider.enabled ? "" : " --- Requires API Key in Settings"),
        ])
      }
    }
    available_model_select.push([
      "download_jsonl_msg",
      "Download: Chat format with message (JSONL)",
    ])
    available_model_select.push([
      "download_jsonl_toolcall",
      "Download: Chat format with tool calls (JSONL)",
    ])
  }

  let datasets: DatasetSplit[] | null = null
  let datasets_error: KilnError | null = null
  let datasets_loading = true
  let dataset_select: [string, string][] = []
  async function get_datasets() {
    try {
      datasets_loading = true
      datasets = null
      if (!project_id || !task_id) {
        throw new Error("Project or task ID not set.")
      }
      const { data: datasets_response, error: get_error } = await client.GET(
        "/api/projects/{project_id}/tasks/{task_id}/dataset_splits",
        {
          params: {
            path: {
              project_id,
              task_id,
            },
          },
        },
      )
      if (get_error) {
        throw get_error
      }
      if (!datasets_response) {
        throw new Error("Invalid response from server")
      }
      datasets = datasets_response
      build_available_dataset_select(datasets)
    } catch (e) {
      if (e instanceof Error && e.message.includes("Load failed")) {
        datasets_error = new KilnError(
          "Could not load datasets for fine-tuning.",
          null,
        )
      } else {
        datasets_error = createKilnError(e)
      }
    } finally {
      datasets_loading = false
    }
  }
  function build_available_dataset_select(datasets: DatasetSplit[]) {
    dataset_select = []
    dataset_select.push([disabled_header, "Select a dataset to fine-tune with"])
    for (const dataset of datasets) {
      dataset_select.push([
        "" + dataset.id,
        "[ID:" + dataset.id + "] " + dataset.name,
      ])
    }
    dataset_select.push(["new", "New Dataset"])
  }

  $: if (model_provider !== disabled_header) {
    get_hyperparameters(model_provider.split("/")[0])
  }

  let hyperparameters: FineTuneParameter[] | null = null
  let hyperparameters_error: KilnError | null = null
  let hyperparameters_loading = true
  let hyperparameter_values: Record<string, string> = {}
  async function get_hyperparameters(provider_id: string) {
    try {
      hyperparameters_loading = true
      hyperparameters = null
      hyperparameter_values = {}
      if (provider_id.startsWith("download_")) {
        // No hyperparameters for download options
        return
      }
      const { data: hyperparameters_response, error: get_error } =
        await client.GET("/api/finetune/hyperparameters/{provider_id}", {
          params: {
            path: {
              provider_id,
            },
          },
        })
      if (get_error) {
        throw get_error
      }
      if (!hyperparameters_response) {
        throw new Error("Invalid response from server")
      }
      hyperparameters = hyperparameters_response
      // build_available_hyperparameter_select(hyperparameters)
    } catch (e) {
      if (e instanceof Error && e.message.includes("Load failed")) {
        hyperparameters_error = new KilnError(
          "Could not load hyperparameters for fine-tuning.",
          null,
        )
      } else {
        hyperparameters_error = createKilnError(e)
      }
    } finally {
      hyperparameters_loading = false
    }
  }

  const type_strings: Record<FineTuneParameter["type"], string> = {
    int: "Integer",
    float: "Float",
    bool: "Boolean - 'true' or 'false'",
    string: "String",
  }

  $: handle_dataset_select(dataset_id)

  function handle_dataset_select(dataset_id_new: string) {
    if (dataset_id_new === "new") {
      dataset_id = disabled_header
      const modal = document.getElementById("create_dataset_modal")
      if (modal) {
        // @ts-expect-error daisyui functions not typed
        modal.showModal()
      }
    }
  }

  let create_dataset_split_error: KilnError | null = null
  let create_dataset_split_loading = false
  async function create_dataset() {
    try {
      create_dataset_split_loading = true
      const { data: create_dataset_split_response, error: get_error } =
        await client.POST(
          "/api/projects/{project_id}/tasks/{task_id}/dataset_splits",
          {
            params: {
              path: {
                project_id,
                task_id,
              },
            },
            body: {
              // @ts-expect-error types are validated by the server
              dataset_split_type: new_dataset_split,
              // @ts-expect-error types are validated by the server
              filter_type: new_dataset_filter,
            },
          },
        )
      if (get_error) {
        throw get_error
      }
      if (!create_dataset_split_response || !create_dataset_split_response.id) {
        throw new Error("Invalid response from server")
      }
      if (!datasets) {
        datasets = []
      }
      datasets.push(create_dataset_split_response)
      build_available_dataset_select(datasets)
      dataset_id = create_dataset_split_response.id
      const modal = document.getElementById("create_dataset_modal")
      if (modal) {
        // @ts-expect-error daisyui functions not typed
        modal.close()
      }
    } catch (e) {
      if (e instanceof Error && e.message.includes("Load failed")) {
        create_dataset_split_error = new KilnError(
          "Could not create a dataset split for fine-tuning.",
          null,
        )
      } else {
        create_dataset_split_error = createKilnError(e)
      }
    } finally {
      create_dataset_split_loading = false
    }
  }
</script>

<AppPage
  title="Create a New Fine Tune"
  subtitle="Fine-tuned models learn on your dataset."
>
  {#if available_models_loading || datasets_loading}
    <div class="w-full min-h-[50vh] flex justify-center items-center">
      <div class="loading loading-spinner loading-lg"></div>
    </div>
  {:else if available_models_error || datasets_error}
    <div
      class="w-full min-h-[50vh] flex flex-col justify-center items-center gap-2"
    >
      <div class="font-medium">Error Loading Available Models and Datasets</div>
      <div class="text-error text-sm">
        {available_models_error?.getMessage() ||
          datasets_error?.getMessage() ||
          "An unknown error occurred"}
      </div>
    </div>
  {:else}
    <FormContainer {submit_visible} submit_label="Start Fine-Tune Job">
      <div class="text-xl font-bold">Step 1: Select Model</div>
      <FormElement
        label="Model & Provider"
        description="Select which model to fine-tune, and which provider to use. Optionally, download a JSONL file to fine-tune using any infrastructure."
        info_description="Fine-tuning requires a lot of compute. Generally we suggest you use a hosted cloud option, but if you have enough compute and expertise you can fine-tune on your own using tools like Unsloth, Axolotl, and others."
        inputType="select"
        id="provider"
        select_options={available_model_select}
        bind:value={model_provider}
      />
      {#if model_provider !== disabled_header}
        <div class="text-xl font-bold">Step 2: Select a Dataset</div>
        <FormElement
          label="Dataset"
          description="Select a dataset to fine-tune with."
          info_description="These datasets are subsets of the current task's data. We freeze a copy when you create a fine-tune so that you can create multiple fine-tunes from the same dataset for consistent evaluation."
          inputType="select"
          id="dataset"
          select_options={dataset_select}
          bind:value={dataset_id}
        />
        {#if selected_dataset}
          {#if selected_dataset_training_set_name && selected_dataset.split_contents[selected_dataset_training_set_name]?.length < 100}
            <div class="text-error text-sm mt-2">
              Warning: Your selected dataset has less than 100 examples for
              training. We strongly recommend creating a larger dataset before
              fine-tuning. Try our
              <a href={`/generate/${project_id}/${task_id}`} class="link">
                generation tool
              </a>
              to expand your dataset.
            </div>
          {/if}
          <div class="text-sm">
            The selected dataset has {selected_dataset.splits?.length}
            {selected_dataset.splits?.length === 1 ? "split" : "splits"}:
            <ul class="list-disc list-inside pt-2">
              {#each Object.entries(selected_dataset.split_contents) as [split_name, split_contents]}
                <li>
                  {split_name.charAt(0).toUpperCase() +
                    split_name.slice(1)}:{" "}
                  {split_contents.length} examples
                  <span class="text-xs text-gray-500 pl-2">
                    {#if split_name === "val" && automatic_validation === disabled_header}
                      May be used for validation during fine-tuning
                    {:else if split_name === "val" && automatic_validation === "yes"}
                      Will be used for validation during fine-tuning
                    {:else if split_name === "test"}
                      Will not be used, reserved for later evaluation
                    {:else if split_name === selected_dataset_training_set_name}
                      Will be used for training
                    {/if}
                  </span>
                </li>
              {/each}
            </ul>
          </div>
        {/if}
        {#if selected_dataset && selected_dataset_has_val}
          <FormElement
            label="Automatic Validation"
            description="The selected dataset has a validation set. Should we use this for validation during fine-tuning? Select 'Yes' if your task is completely deterministic (classification), and 'No' if the task is not deterministic (e.g. generation)."
            inputType="select"
            id="automatic_validation"
            select_options={[
              [disabled_header, "Select if your task is deterministic"],
              ["yes", "Yes - My task is deterministic (classification)"],
              ["no", "No - My task is not deterministic (generation)"],
            ]}
            bind:value={automatic_validation}
          />
        {/if}
      {/if}
      {#if step_3_download_visible}
        <div class="text-xl font-bold">Step 3: Download JSONL</div>
        <div>Download JSONL files to fine-tune using any infrastructure.</div>
        <!-- TODO: download options -->
      {:else if step_3_run_visible}
        <div class="text-xl font-bold">Step 3: Options</div>
        <FormElement
          label="Description"
          description="An optional description for you and your team to help identify this fine-tune."
          optional={true}
          inputType="textarea"
          id="description"
          bind:value={description}
        />
        {#if hyperparameters_loading}
          <div class="w-full min-h-[50vh] flex justify-center items-center">
            <div class="loading loading-spinner loading-lg"></div>
          </div>
        {:else if hyperparameters_error || !hyperparameters}
          <div class="text-error text-sm">
            {hyperparameters_error?.getMessage() || "An unknown error occurred"}
          </div>
        {:else}
          {#each hyperparameters as hyperparameter}
            <FormElement
              label={hyperparameter.name +
                " (" +
                type_strings[hyperparameter.type] +
                ")"}
              description={hyperparameter.description}
              info_description="If you aren't sure, leave blank for default/recommended value. Ensure your value is valid for the type (e.g. an integer can't have decimals)."
              inputType="input"
              optional={hyperparameter.optional}
              id={hyperparameter.name}
              bind:value={hyperparameter_values[hyperparameter.name]}
            />
          {/each}
        {/if}
      {/if}
    </FormContainer>
  {/if}
</AppPage>

<dialog id="create_dataset_modal" class="modal">
  <div class="modal-box">
    <form method="dialog">
      <button
        class="btn btn-sm text-xl btn-circle btn-ghost absolute right-2 top-2 focus:outline-none"
        >✕</button
      >
    </form>
    <h3 class="text-lg font-bold mb-2">Create a New Dataset Split</h3>
    <div class="font-light text-sm mb-6">
      A dataset split is a collection of examples from the current task. We
      freeze a copy when you create a fine-tune so that you can create multiple
      fine-tunes from the exactly same dataset.
    </div>
    <div class="flex flex-row gap-6 justify-center flex-col">
      <FormContainer
        submit_label="Create Dataset"
        on:submit={create_dataset}
        bind:error={create_dataset_split_error}
        bind:submitting={create_dataset_split_loading}
      >
        <FormElement
          label="Dataset Filter"
          description="Select a filter for your dataset. Typically you want to filter out examples that are not rated 4+ stars."
          info_description="A 'High Rating' filter will include only examples that are rated 4+ stars. The 'All' filter will include all examples."
          inputType="select"
          optional={false}
          id="dataset_filter"
          select_options={[
            [disabled_header, "Select a dataset filter"],
            ["high_rating", "High Rating (4+ stars)"],
            ["all", "All (no filter)"],
          ]}
          bind:value={new_dataset_filter}
        />
        <FormElement
          label="Dataset Splits"
          description="Select a splitting strategy for your dataset."
          info_description="You can split your dataset into training and evaluation sets, or use the entire dataset for training. If in doubt, select 'Train/Test' and we will split 80/20."
          inputType="select"
          optional={false}
          id="dataset_split"
          select_options={[
            [disabled_header, "Select a split strategy"],
            ["train_test", "Train/Test -- 80/20"],
            ["train_test_val", "Train/Test/Val -- 60/20/20"],
            ["all", "Entire Dataset -- 100"],
          ]}
          bind:value={new_dataset_split}
        />
      </FormContainer>
    </div>
  </div>
  <form method="dialog" class="modal-backdrop">
    <button>close</button>
  </form>
</dialog>
