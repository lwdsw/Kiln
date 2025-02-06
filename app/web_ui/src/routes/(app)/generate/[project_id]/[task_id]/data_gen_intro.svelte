<script lang="ts">
  export let generate_subtopics: () => void
  export let generate_samples: () => void
</script>

<div class="flex flex-col md:flex-row gap-32 justify-center items-center">
  <div class="max-w-[300px] font-light text-sm flex flex-col gap-4">
    <div class="font-medium text-lg">Build your dataset with AI.</div>
    <div>Generate data for training and evaluations.</div>
    <div>
      Building a topic tree can help you generate data across diverse subjects:
    </div>
    <img
      src="/images/data_gen_tree.png"
      alt="data gen intro"
      class="w-[150px] mx-auto border rounded-lg pl-2 pr-3 py-2 shadow-md mb-2"
    />
    <button class="btn btn-primary" on:click={() => generate_subtopics()}>
      Add Top Level Topics
    </button>
    <button class="btn" on:click={() => generate_samples()}>
      Add Top Level Data
    </button>
  </div>
</div>
