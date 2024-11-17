<script>
  export let data
  export let depth
</script>

<tr class="bg-base-200">
  <td
    style="padding-left: {depth * 25 + 20}px"
    class="font-medium flex flex-row py-2"
  >
    <div class="flex-1">
      {#if depth > 0}
        <!-- Uploaded to: SVG Repo, www.svgrepo.com, Generator: SVG Repo Mixer Tools -->
        <svg
          class="w-4 h-4 inline"
          viewBox="0 0 24 24"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          ><path
            d="M6 5a1 1 0 0 0-2 0v5.6A5.4 5.4 0 0 0 9.4 16h7.186l-2.293 2.293a1 1 0 0 0 1.414 1.414l4-4a1 1 0 0 0 0-1.414l-4-4a1 1 0 1 0-1.414 1.414L16.586 14H9.4A3.4 3.4 0 0 1 6 10.6V5Z"
            fill="currentColor"
          /></svg
        >
      {/if}
      {data.topic}
    </div>
    <div class="hover-action flex flex-row gap-4 text-gray-500 font-light">
      <button class="link">Remove topic</button>
      <button class="link">Add subtopics</button>
      <button class="link">Add samples</button>
    </div>
  </td>
</tr>
{#each data.samples as sample}
  <tr>
    <td style="padding-left: {(depth + 1) * 25 + 20}px" class="flex flex-row">
      <div class="flex-1 font-mono text-sm">
        {sample.input}
      </div>
      <div class="hover-action flex flex-row gap-4 text-gray-500 font-light">
        <button class="link">Remove sample</button>
      </div>
    </td>
  </tr>
{/each}
{#if data.sub_topics}
  {#each data.sub_topics as sub_node}
    <svelte:self data={sub_node} depth={depth + 1} />
  {/each}
{/if}

<style>
  .hover-action {
    visibility: hidden;
  }
  tr:hover td .hover-action {
    visibility: visible;
  }
</style>
