<script lang="ts">
  import AppPage from "../../../app_page.svelte"
  import { client } from "$lib/api_client"
  import { current_task } from "$lib/stores"
  import type { Task } from "$lib/types"
  import { KilnError, createKilnError } from "$lib/utils/error_handlers"
  import { onMount } from "svelte"
  import { page } from "$app/stores"
  import GeneratedDataNode from "./GeneratedDataNode.svelte"

  let task: Task | null = null
  let task_error: KilnError | null = null
  let task_loading = true

  $: project_id = $page.params.project_id
  $: task_id = $page.params.task_id

  type SampleData = {
    input: string
  }

  type SampleDataNode = {
    topic: string
    sub_topics: SampleDataNode[]
    samples: SampleData[]
  }

  let data_tree: SampleDataNode[] = [
    {
      topic: "Food",
      samples: [
        { input: "Takeout" },
        { input: "Restaurant" },
        { input: "Delivery" },
      ],
      sub_topics: [
        {
          topic: "Pizza",
          sub_topics: [],
          samples: [
            {
              input: "Pepperoni Pizza",
            },
            {
              input: "Cheese Pizza",
            },
            {
              input: "Vegetarian Pizza",
            },
          ],
        },
        {
          topic: "Burger",
          sub_topics: [],
          samples: [
            {
              input: "Cheeseburger",
            },
            {
              input: "Hamburger",
            },
            {
              input: "Veggie Burger",
            },
          ],
        },
      ],
    },
    {
      topic: "Places",
      samples: [],
      sub_topics: [
        {
          topic: "Beach",
          sub_topics: [],
          samples: [
            {
              input: "Tropical Beach",
            },
            {
              input: "Rocky Beach",
            },
            {
              input: "Sandy Beach",
            },
          ],
        },
        {
          topic: "Mountain",
          sub_topics: [],
          samples: [
            {
              input: "Snowy Peak",
            },
            {
              input: "Forest Mountain",
            },
            {
              input: "Rocky Mountain",
            },
          ],
        },
      ],
    },
  ]

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
    subtitle={`AI tools to help you grow your dataset for "${task?.name}"`}
  >
    {#if task_loading}
      <div class="w-full min-h-[50vh] flex justify-center items-center">
        <div class="loading loading-spinner loading-lg"></div>
      </div>
    {:else if task}
      <div class="overflow-x-auto">
        <table class="table">
          <tbody>
            {#each data_tree as node}
              <GeneratedDataNode data={node} depth={0} />
            {/each}
          </tbody>
        </table>
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
