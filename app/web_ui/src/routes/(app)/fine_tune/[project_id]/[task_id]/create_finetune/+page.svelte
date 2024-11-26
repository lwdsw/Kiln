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

  $: project_id = $page.params.project_id
  $: task_id = $page.params.task_id

  let available_models: FinetuneProvider[] | null = null
  let available_model_select: [string, string][] = []
  let available_models_error: KilnError | null = null
  let available_models_loading = true

  // TODO: existing data
  $: step_3_visible =
    model_provider !== disabled_header &&
    dataset_id != disabled_header &&
    ((dataset_id === "new" && new_dataset_split != disabled_header) ||
      dataset_id === "TODO")
  $: step_3_run_visible =
    step_3_visible && !model_provider.startsWith("download_")
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
      dataset_select.push(["" + dataset.id, dataset.name])
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
          description="Select which dataset to fine-tune with."
          info_description="These datasets are subsets of the current task's data. We freeze a copy when you create a fine-tune so that you can create multiple fine-tunes from the same dataset for consistent evaluation."
          inputType="select"
          id="dataset"
          select_options={dataset_select}
          bind:value={dataset_id}
        />
        {#if dataset_id === "new"}
          <FormElement
            label="Dataset Splits"
            description="Select a splitting strategy for your dataset."
            info_description="You can split your dataset into training and evaluation sets, or use the entire dataset for training. If in doubt, select 'Train/Test' and we will split 80/20."
            inputType="select"
            id="dataset_split"
            select_options={[
              [disabled_header, "Select a split strategy"],
              ["train_test", "Train/Test -- 80/20"],
              ["train_test_val", "Train/Test/Val -- 60/20/20"],
              ["full", "Entire Dataset"],
            ]}
            bind:value={new_dataset_split}
          />
        {:else}
          TODO: select train and val splits
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
              id={hyperparameter.name}
              bind:value={hyperparameter_values[hyperparameter.name]}
            />
          {/each}
        {/if}
      {/if}
    </FormContainer>
  {/if}
</AppPage>
