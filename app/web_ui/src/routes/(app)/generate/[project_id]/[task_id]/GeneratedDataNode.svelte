<script lang="ts">
  import type { SampleDataNode, SampleData } from "./gen_model"
  import AvailableModelsDropdown from "../../../run/available_models_dropdown.svelte"
  import { tick } from "svelte"

  export let data: SampleDataNode
  export let depth: number
  export let path: string[]

  let expandedSamples: boolean[] = new Array(data.samples.length).fill(false)

  function toggleExpand(index: number) {
    expandedSamples[index] = !expandedSamples[index]
  }

  function formatExpandedSample(sample: SampleData): string {
    // If JSON, pretty format it
    try {
      const json = JSON.parse(sample.input)
      return JSON.stringify(json, null, 2)
    } catch (e) {
      // Not JSON
    }

    return sample.input
  }

  const modal_id = crypto.randomUUID()
  let generate_subtopics: boolean = false
  let num_subtopics_to_generate: number = 6
  let custom_topics_string: string = ""
  async function open_generate_subtopics_modal() {
    // Avoid having a trillion of these hidden in the DOM
    generate_subtopics = true
    await tick()
    const modal = document.getElementById(modal_id)
    // @ts-expect-error dialog is not a standard element
    modal?.showModal()
  }
</script>

{#if path.length == 0}
  ROOT CONTROLS TODO
{/if}

<div
  class="data-row bg-base-200 font-medium flex flex-row py-2"
  style="padding-left: {depth * 25 + 20}px"
>
  <div class="flex-1">
    {#if depth > 0}
      <span class="text-xs relative" style="top: -3px">⮑</span>
    {/if}
    {data.topic}
  </div>
  <div class="hover-action flex flex-row gap-4 text-gray-500 font-light">
    <button class="link">Remove topic</button>
    <button class="link" on:click={() => open_generate_subtopics_modal()}>
      Add subtopics
    </button>
    <button class="link">Add samples</button>
  </div>
</div>
{#each data.samples as sample, index}
  <div
    style="padding-left: {(depth + 1) * 25 + 20}px"
    class="data-row flex flex-row items-center border-b-2 border-base-200"
  >
    <div class="flex-1 font-mono text-sm overflow-hidden py-2">
      {#if expandedSamples[index]}
        <pre class="whitespace-pre-wrap">{formatExpandedSample(sample)}</pre>
      {:else}
        <div class="truncate w-0 min-w-full">{sample.input}</div>
      {/if}
    </div>
    <div
      class="hover-action flex
        flex-row gap-x-4 gap-y-1 text-gray-500 font-light px-4"
      style={expandedSamples[index] ? "display: flex" : ""}
    >
      <button class="link flex" on:click={() => toggleExpand(index)}>
        {expandedSamples[index] ? "Collapse" : "Expand"}
      </button>
      <button class="link flex">Delete</button>
    </div>
  </div>
{/each}
{#if data.sub_topics}
  {#each data.sub_topics as sub_node}
    <svelte:self
      data={sub_node}
      depth={depth + 1}
      path={[...path, data.topic]}
    />
  {/each}
{/if}

{#if generate_subtopics}
  <dialog id={modal_id} class="modal">
    <div class="modal-box">
      <form method="dialog">
        <button
          class="btn btn-sm text-xl btn-circle btn-ghost absolute right-2 top-2 focus:outline-none"
          >✕</button
        >
      </form>
      <h3 class="text-lg font-bold">Add Subtopics</h3>
      <p class="text-sm font-light mb-8">
        Add a list of subtopics for "{[...path, data.topic].join(" → ")}"
      </p>
      <div class="flex flex-col gap-2">
        <div class="flex-grow font-medium">Generate topics</div>

        <div class="flex flex-row items-center gap-4 mt-4 mb-2">
          <div class="flex-grow font-medium text-sm">Topic Count</div>
          <div class="flex flex-row gap-2">
            <button
              class="btn btn-sm"
              on:click={() =>
                (num_subtopics_to_generate = Math.max(
                  1,
                  num_subtopics_to_generate - 1,
                ))}
            >
              -
            </button>
            <span class="text-lg font-medium w-8 text-center"
              >{num_subtopics_to_generate}</span
            >
            <button
              class="btn btn-sm"
              on:click={() =>
                (num_subtopics_to_generate = Math.min(
                  20,
                  num_subtopics_to_generate + 1,
                ))}
            >
              +
            </button>
          </div>
        </div>
        <AvailableModelsDropdown requires_data_gen={true} />
        <button class="btn btn-sm {custom_topics_string ? '' : 'btn-primary'}"
          >Generate {num_subtopics_to_generate} Topics</button
        >
        <div class="divider">OR</div>
        <div class="flex flex-col">
          <div class="flex-grow font-medium">Custom topics</div>
          <div class="text-xs text-gray-500">Comma separated list</div>
        </div>
        <input
          type="text"
          bind:value={custom_topics_string}
          class="input input-bordered input-sm"
        />
        <button class="btn btn-sm {custom_topics_string ? 'btn-primary' : ''}"
          >Add Custom Topics</button
        >
      </div>
    </div>
    <form method="dialog" class="modal-backdrop">
      <button>close</button>
    </form>
  </dialog>
{/if}

<style>
  .data-row .hover-action {
    display: none;
    visibility: hidden;
  }
  .data-row:hover .hover-action {
    display: flex;
    visibility: visible;
  }

  .divider {
    display: flex;
    align-items: center;
    text-align: center;
    color: #666;
    font-size: 0.875rem;
    margin: 0.5rem 0;
    padding: 2.5rem 0 1.5rem 0;
  }

  .divider::before,
  .divider::after {
    content: "";
    flex: 1;
    border-bottom: 1px solid #ddd;
    margin: 0 0.75rem;
  }
</style>
