<script lang="ts">
  import AppPage from "../../../app_page.svelte"
  import { client } from "$lib/api_client"
  import { current_task } from "$lib/stores"
  import type { Task } from "$lib/types"
  import { KilnError, createKilnError } from "$lib/utils/error_handlers"
  import { onMount } from "svelte"
  import { page } from "$app/stores"
  import type { SampleDataNode } from "./gen_model"
  import GeneratedDataNode from "./generated_data_node.svelte"
  import { beforeNavigate } from "$app/navigation"

  let guidance_enabled = false
  let human_guidance = ""

  let task: Task | null = null
  let task_error: KilnError | null = null
  let task_loading = true

  $: project_id = $page.params.project_id
  $: task_id = $page.params.task_id
  $: action_buttons = guidance_enabled
    ? [
        {
          label: "Remove Guidance",
          handler: () => {
            guidance_enabled = false
            human_guidance = ""
          },
        },
      ]
    : [
        {
          label: "Add Guidance",
          handler: () => (guidance_enabled = true),
        },
      ]

  let root_node: SampleDataNode = {
    topic: "",
    samples: [],
    sub_topics: [],
  }

  onMount(() => {
    get_task()

    // Handle browser reload/close: warn if there are unsaved changes
    window.addEventListener("beforeunload", handleBeforeUnload)
    return () => {
      window.removeEventListener("beforeunload", handleBeforeUnload)
    }
  })

  async function get_task() {
    try {
      task_loading = true
      if (!project_id || !task_id) {
        throw new Error("Project or task ID not set.")
      }
      if ($current_task?.id === task_id) {
        task = $current_task
        return
      }
      const { data: task_response, error: get_error } = await client.GET(
        "/api/projects/{project_id}/tasks/{task_id}",
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
      task = task_response
    } catch (e) {
      if (e instanceof Error && e.message.includes("Load failed")) {
        task_error = new KilnError(
          "Could not load task. It may belong to a project you don't have access to.",
          null,
        )
      } else {
        task_error = createKilnError(e)
      }
    } finally {
      task_loading = false
    }
  }

  function has_unsaved_changes(): boolean {
    return root_node.samples.length != 0 || root_node.sub_topics.length != 0
  }

  // Handle browser reload/close: warn if there are unsaved changes
  function handleBeforeUnload(event: BeforeUnloadEvent) {
    if (has_unsaved_changes()) {
      event.preventDefault()
    }
  }

  // Handle Svelte navigation: warn if there are unsaved changes
  beforeNavigate((navigation) => {
    if (has_unsaved_changes()) {
      if (
        !confirm(
          "You have unsaved changes which will be lost if you leave.\n\n" +
            "Press Cancel to stay, OK to leave.",
        )
      ) {
        navigation.cancel()
      }
    }
  })
</script>

<div class="max-w-[1400px]">
  <AppPage
    title="Generate Synthetic Data"
    subtitle={`Grow your dataset by generating new sample inputs`}
    {action_buttons}
  >
    <div
      class="flex flex-row mb-4 justify-center {guidance_enabled
        ? ''
        : 'hidden'}"
    >
      <div class="flex flex-col gap-2 w-full md:w-[500px]">
        <label for="human_guidance" class="label font-medium p-0 text-sm"
          >Guidance to help the model generate relevant data:</label
        >
        <textarea
          id="human_guidance"
          bind:value={human_guidance}
          class="input input-bordered"
        />
      </div>
    </div>

    {#if task_loading}
      <div class="w-full min-h-[50vh] flex justify-center items-center">
        <div class="loading loading-spinner loading-lg"></div>
      </div>
    {:else if task}
      <div class="flex flex-col">
        <GeneratedDataNode
          data={root_node}
          path={[]}
          {project_id}
          {task_id}
          {human_guidance}
        />
      </div>
    {:else if task_error}
      <div
        class="w-full min-h-[50vh] flex flex-col justify-center items-center gap-2"
      >
        <div class="font-medium">Error Loading Task</div>
        <div class="text-error text-sm">
          {task_error.getMessage() || "An unknown error occurred"}
        </div>
      </div>
    {/if}
  </AppPage>
</div>
