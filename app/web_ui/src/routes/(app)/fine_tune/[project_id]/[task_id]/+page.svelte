<script lang="ts">
  import AppPage from "../../../app_page.svelte"
  import EmptyFinetune from "./empty_finetune.svelte"
  import { client } from "$lib/api_client"
  import type { Finetune } from "$lib/types"
  import { KilnError, createKilnError } from "$lib/utils/error_handlers"
  import { onMount } from "svelte"
  import { goto } from "$app/navigation"
  import { page } from "$app/stores"
  import { formatDate } from "$lib/utils/formatters"

  $: project_id = $page.params.project_id
  $: task_id = $page.params.task_id

  let finetunes: Finetune[] | null = null
  let finetunes_error: KilnError | null = null
  let finetunes_loading = true

  onMount(async () => {
    get_finetunes()
  })

  async function get_finetunes() {
    try {
      finetunes_loading = true
      if (!project_id || !task_id) {
        throw new Error("Project or task ID not set.")
      }
      const { data: finetunes_response, error: get_error } = await client.GET(
        "/api/projects/{project_id}/tasks/{task_id}/finetunes",
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
      finetunes = finetunes_response
    } catch (e) {
      if (e instanceof Error && e.message.includes("Load failed")) {
        finetunes_error = new KilnError(
          "Could not load finetunes. This task may belong to a project you don't have access to.",
          null,
        )
      } else {
        finetunes_error = createKilnError(e)
      }
    } finally {
      finetunes_loading = false
    }
  }
</script>

<AppPage
  title="Fine-Tune"
  subtitle="Create fine-tuned models for this task."
  action_buttons={[
    {
      label: "Create Finetune",
      href: `/fine_tune/${project_id}/${task_id}/create_finetune`,
    },
  ]}
>
  {#if finetunes_loading}
    <div class="w-full min-h-[50vh] flex justify-center items-center">
      <div class="loading loading-spinner loading-lg"></div>
    </div>
  {:else if finetunes && finetunes.length == 0}
    <div class="flex flex-col items-center justify-center min-h-[60vh]">
      <EmptyFinetune {project_id} {task_id} />
    </div>
  {:else if finetunes}
    <div class="overflow-x-auto">
      <table class="table">
        <thead>
          <tr>
            <th> Name </th>
            <th> Description </th>
            <th> Splits </th>
            <th> Created At </th>
          </tr>
        </thead>
        <tbody>
          {#each finetunes as finetune}
            <tr
              class="hover cursor-pointer"
              on:click={() => {
                goto(
                  `/fine_tune/${project_id}/${task_id}/finetune/${finetune.id}`,
                )
              }}
            >
              <td> {finetune.name} </td>
              <td> {finetune.description} </td>
              <td> TODO </td>
              <td> {formatDate(finetune.created_at)} </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {:else if finetunes_error}
    <div
      class="w-full min-h-[50vh] flex flex-col justify-center items-center gap-2"
    >
      <div class="font-medium">Error Loading Fine Tunes</div>
      <div class="text-error text-sm">
        {finetunes_error.getMessage() || "An unknown error occurred"}
      </div>
    </div>
  {/if}
</AppPage>
