<script lang="ts">
  import AppPage from "../../../../app_page.svelte"
  import EditTask from "../../../../../(fullscreen)/setup/(setup)/create_task/edit_task.svelte"
  import { onMount } from "svelte"
  import { createKilnError, KilnError } from "$lib/utils/error_handlers"
  import { page } from "$app/stores"
  import type { Task } from "$lib/types"
  import { client } from "$lib/api_client"
  import { goto } from "$app/navigation"

  export let clone_mode: boolean = false

  $: project_id = $page.params.project_id
  $: task_id = $page.params.task_id

  let task: Task | null = null
  let loading = false
  let error: KilnError | null = null

  onMount(async () => {
    get_task()
  })

  async function get_task() {
    try {
      loading = true
      if (!project_id || !task_id) {
        throw new Error("Project or task ID not set.")
      }
      // Always load the task from the server, even if it's the current task. We want the freshest data.
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
      if (clone_mode) {
        // Clone mode means we're creating a new task with the same content as the existing one.
        // We don't want to pass the ID to the edit task component, so we set it to null.
        task_response.id = null
        task_response.name = `Copy of ${task_response.name}`
      }
      task = task_response
    } catch (e) {
      if (e instanceof Error && e.message.includes("Load failed")) {
        error = new KilnError(
          "Could not load task. It may belong to a project you don't have access to.",
          null,
        )
      } else {
        error = createKilnError(e)
      }
    } finally {
      loading = false
    }
  }
</script>

<div class="max-w-[900px]">
  <AppPage
    title={clone_mode ? "Clone Task" : "Edit Task"}
    subtitle={task?.id
      ? `Task ID: ${task.id}`
      : clone_mode
        ? "Create a new task, using an existing task as a template"
        : undefined}
    sub_subtitle={clone_mode
      ? "The cloned task will not contain any data from the original task."
      : undefined}
    action_buttons={!clone_mode
      ? [
          {
            label: "Clone Task",
            primary: true,
            handler: () => {
              goto(`/settings/clone_task/${project_id}/${task_id}`)
            },
          },
        ]
      : undefined}
  >
    {#if loading}
      <div class="w-full min-h-[50vh] flex justify-center items-center">
        <div class="loading loading-spinner loading-lg"></div>
      </div>
    {:else if error}
      <div class="text-red-500">Error loading task: {error.getMessage()}</div>
    {:else if task}
      <EditTask {task} redirect_on_created={null} hide_example_task={true} />
    {/if}
  </AppPage>
</div>
