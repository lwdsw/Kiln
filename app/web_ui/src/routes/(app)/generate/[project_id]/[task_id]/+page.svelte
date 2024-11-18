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

  onMount(async () => {
    get_task()
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
</script>

<div class="max-w-[1400px]">
  <AppPage
    title="Generate Synthetic Data"
    subtitle={`Grow your dataset by generating new sample inputs`}
    {action_buttons}
  >
    <div class=" {guidance_enabled ? '' : 'hidden'}">
      <label for="human_guidance" class="label font-medium"
        >Guidance to help generate relevant data:</label
      >
      <textarea
        id="human_guidance"
        bind:value={human_guidance}
        class="input input-bordered w-full md:w-[500px]"
      />
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
