<script lang="ts">
  import AppPage from "../../../app_page.svelte"
  import EmptyInto from "./empty_into.svelte"
  import { client } from "$lib/api_client"
  import type { RunSummary } from "$lib/types"
  import { KilnError, createKilnError } from "$lib/utils/error_handlers"
  import { onMount } from "svelte"
  import { model_info, load_model_info, model_name } from "$lib/stores"
  import { goto } from "$app/navigation"
  import { page } from "$app/stores"
  import { formatDate } from "$lib/utils/formatters"
  import { replaceState } from "$app/navigation"

  let runs: RunSummary[] | null = null
  let error: KilnError | null = null
  let loading = true
  let sortColumn = ($page.url.searchParams.get("sort") || "created_at") as
    | keyof RunSummary
    | "rating"
    | "inputPreview"
    | "source"
    | "outputPreview"
    | "model"
    | "repairState"
    | "created_at"
  let sortDirection = ($page.url.searchParams.get("order") || "desc") as
    | "asc"
    | "desc"
  let filter_tags = ($page.url.searchParams.getAll("tags") || []) as string[]
  $: {
    // Update based on live URL
    const url = new URL(window.location.href)
    sortColumn = (url.searchParams.get("sort") ||
      "created_at") as typeof sortColumn
    sortDirection = (url.searchParams.get("order") ||
      "desc") as typeof sortDirection
    filter_tags = url.searchParams.getAll("tags") as string[]
    sortRuns()
  }

  $: project_id = $page.params.project_id
  $: task_id = $page.params.task_id

  const columns = [
    { key: "rating", label: "Rating" },
    { key: "repairState", label: "Repair State" },
    { key: "source", label: "Source" },
    { key: "model", label: "Model" },
    { key: "created_at", label: "Created At" },
    { key: "inputPreview", label: "Input Preview" },
    { key: "outputPreview", label: "Output Preview" },
  ]

  onMount(async () => {
    get_runs()
  })

  async function get_runs() {
    try {
      load_model_info()
      loading = true
      if (!project_id || !task_id) {
        throw new Error("Project or task ID not set.")
      }
      const { data: runs_response, error: get_error } = await client.GET(
        "/api/projects/{project_id}/tasks/{task_id}/runs_summaries",
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
      runs = runs_response
      sortRuns()
    } catch (e) {
      if (e instanceof Error && e.message.includes("Load failed")) {
        error = new KilnError(
          "Could not load dataset. It may belong to a project you don't have access to.",
          null,
        )
      } else {
        error = createKilnError(e)
      }
    } finally {
      loading = false
    }
  }

  function sortFunction(a: RunSummary, b: RunSummary) {
    let aValue: string | number | Date | null | undefined
    let bValue: string | number | Date | null | undefined

    switch (sortColumn) {
      case "id":
        aValue = a.id
        bValue = b.id
        break
      case "created_at":
        aValue = a[sortColumn]
        bValue = b[sortColumn]
        break
      case "rating":
        aValue = a.rating?.value ?? -1
        bValue = b.rating?.value ?? -1
        break
      case "source":
        aValue = a.input_source ?? ""
        bValue = b.input_source ?? ""
        break
      case "inputPreview":
        aValue = (a.input_preview ?? "").toLowerCase()
        bValue = (b.input_preview ?? "").toLowerCase()
        break
      case "outputPreview":
        aValue = (a.output_preview ?? "").toLowerCase()
        bValue = (b.output_preview ?? "").toLowerCase()
        break
      case "repairState":
        aValue = a.repair_state
        bValue = b.repair_state
        break
      case "model":
        aValue = model_name(a.model_name || undefined, $model_info)
        bValue = model_name(b.model_name || undefined, $model_info)
        break
      default:
        return 0
    }

    if (!aValue) return sortDirection === "asc" ? 1 : -1
    if (!bValue) return sortDirection === "asc" ? -1 : 1

    if (aValue < bValue) return sortDirection === "asc" ? -1 : 1
    if (aValue > bValue) return sortDirection === "asc" ? 1 : -1
    return 0
  }

  function handleSort(columnString: string) {
    const new_column = columnString as typeof sortColumn
    let new_direction = "desc"
    if (sortColumn === new_column) {
      new_direction = sortDirection === "asc" ? "desc" : "asc"
    } else {
      new_direction = "desc"
    }
    updateURL({
      sort: new_column,
      order: new_direction,
      tags: filter_tags,
    })
  }

  function sortRuns() {
    if (!runs) return
    runs = runs ? [...runs].sort(sortFunction) : null
  }

  function remove_filter_tag(tag: string) {
    const newTags = filter_tags.filter((t) => t !== tag)
    updateURL({
      sort: sortColumn,
      order: sortDirection,
      tags: newTags,
    })
  }

  function add_filter_tag(tag: string) {
    const newTags = [...new Set([...filter_tags, tag])]
    updateURL({
      sort: sortColumn,
      order: sortDirection,
      tags: newTags,
    })
  }

  $: available_filter_tags = get_available_filter_tags(runs, filter_tags)
  function get_available_filter_tags(
    runs: RunSummary[] | null,
    filter_tags: string[],
  ): Record<string, number> {
    if (!runs) return {}

    const filtered_runs = runs.filter((run) =>
      filter_tags.every((tag) => run.tags?.includes(tag)),
    )

    const remaining_tags: Record<string, number> = {}
    filtered_runs.forEach((run) => {
      run.tags?.forEach((tag) => {
        if (filter_tags.includes(tag)) return
        if (typeof tag === "string") {
          remaining_tags[tag] = (remaining_tags[tag] || 0) + 1
        }
      })
    })
    return remaining_tags
  }

  function updateURL(params: Record<string, string | string[]>) {
    // update the URL so you can share links
    const url = new URL(window.location.href)

    // Clear existing params we manage
    url.searchParams.delete("sort")
    url.searchParams.delete("order")
    url.searchParams.delete("tags")

    // Add new params
    Object.entries(params).forEach(([key, value]) => {
      if (Array.isArray(value)) {
        value.forEach((v) => url.searchParams.append(key, v))
      } else {
        url.searchParams.set(key, value)
      }
    })

    // Use replaceState to avoid adding new entries to history
    replaceState(url, {})
    sortRuns()
  }
</script>

<AppPage
  title="Dataset"
  subtitle="Explore sample and ratings for this task."
  action_buttons={[
    {
      label: "Filter by Tag",
      handler() {
        // @ts-expect-error showModal is not a method on HTMLElement
        document.getElementById("tags_modal")?.showModal()
      },
      notice: filter_tags.length > 0,
    },
    {
      label: "Add Data",
      handler() {
        // @ts-expect-error showModal is not a method on HTMLElement
        document.getElementById("add_data_modal")?.showModal()
      },
    },
  ]}
>
  {#if loading}
    <div class="w-full min-h-[50vh] flex justify-center items-center">
      <div class="loading loading-spinner loading-lg"></div>
    </div>
  {:else if runs && runs.length == 0}
    <div class="flex flex-col items-center justify-center min-h-[60vh]">
      <EmptyInto {project_id} {task_id} />
    </div>
  {:else if runs}
    <div class="overflow-x-auto">
      <table class="table">
        <thead>
          <tr>
            {#each columns as { key, label }}
              <th
                on:click={() => handleSort(key)}
                class="hover:bg-base-200 cursor-pointer"
              >
                {label}
                {sortColumn === key
                  ? sortDirection === "asc"
                    ? "▲"
                    : "▼"
                  : ""}
              </th>
            {/each}
          </tr>
        </thead>
        <tbody>
          {#each runs as run}
            {#if filter_tags.every((tag) => run.tags?.includes(tag))}
              <tr
                class="hover cursor-pointer"
                on:click={() => {
                  goto(`/dataset/${project_id}/${task_id}/${run.id}/run`)
                }}
              >
                <td>
                  {run.rating && run.rating.value
                    ? run.rating.type === "five_star"
                      ? "★".repeat(run.rating.value)
                      : run.rating.value + "(custom score)"
                    : "Unrated"}
                </td>
                <td>{run.repair_state}</td>
                <td>{run.input_source}</td>
                <td class="break-words max-w-36">
                  {model_name(run.model_name || undefined, $model_info)}
                </td>
                <td>{formatDate(run.created_at)}</td>
                <td class="break-words max-w-48">
                  {run.input_preview || "No input"}
                </td>
                <td class="break-words max-w-48">
                  {run.output_preview || "No output"}
                </td>
              </tr>
            {/if}
          {/each}
        </tbody>
      </table>
    </div>
  {:else if error}
    <div
      class="w-full min-h-[50vh] flex flex-col justify-center items-center gap-2"
    >
      <div class="font-medium">Error Loading Dataset</div>
      <div class="text-error text-sm">
        {error.getMessage() || "An unknown error occurred"}
      </div>
    </div>
  {/if}
</AppPage>

<dialog id="add_data_modal" class="modal">
  <div class="modal-box">
    <form method="dialog">
      <button
        class="btn btn-sm text-xl btn-circle btn-ghost absolute right-2 top-2 focus:outline-none"
        >✕</button
      >
    </form>
    <h3 class="text-lg font-bold mb-8">Add Data</h3>
    <div class="flex flex-row gap-6 justify-center flex-col">
      <a href={`/generate/${project_id}/${task_id}`} class="btn btn-primary">
        Generate Synthetic Data
      </a>
      <a href="/run" class="btn btn-primary"> Manually Add Data </a>
    </div>
  </div>
  <form method="dialog" class="modal-backdrop">
    <button>close</button>
  </form>
</dialog>

<dialog id="tags_modal" class="modal">
  <div class="modal-box">
    <form method="dialog">
      <button
        class="btn btn-sm text-xl btn-circle btn-ghost absolute right-2 top-2 focus:outline-none"
        >✕</button
      >
    </form>
    <h3 class="text-lg font-bold mb-4">Filter Tags</h3>
    <div class="text-sm mb-2 font-medium">
      Current Filters:
      {#if filter_tags.length == 0}
        None
      {/if}
    </div>
    <div class="flex flex-row gap-2 flex-wrap">
      {#each filter_tags as tag}
        <div class="badge bg-gray-200 text-gray-500 py-3 px-3 max-w-full">
          <span class="truncate">{tag}</span>
          <button
            class="pl-3 font-medium shrink-0"
            on:click={() => remove_filter_tag(tag)}>✕</button
          >
        </div>
      {/each}
    </div>

    <div class="text-sm mt-4 mb-2 font-medium">Add a filter:</div>
    {#if Object.keys(available_filter_tags).length == 0}
      <p class="text-sm text-gray-500">
        Any further filters would show zero results.
      </p>
    {/if}
    <div class="flex flex-row gap-2 flex-wrap">
      {#each Object.entries(available_filter_tags).sort((a, b) => b[1] - a[1]) as [tag, count]}
        <button
          class="badge bg-gray-200 text-gray-500 py-3 px-3 max-w-full"
          on:click={() => add_filter_tag(tag)}>{tag} ({count})</button
        >
      {/each}
    </div>
  </div>
  <form method="dialog" class="modal-backdrop">
    <button>close</button>
  </form>
</dialog>
