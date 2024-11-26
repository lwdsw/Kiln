<script lang="ts">
  export let project_id: string
  export let task_id: string
</script>

<div class="flex flex-col md:flex-row gap-32 justify-center items-center">
  <div class="max-w-[300px] font-light text-sm flex flex-col gap-4">
    <div class="font-medium">
      Finetuning uses your dataset to create custom models which can be faster,
      cheaper and more accurate than standard models.
    </div>
    <div>To get started, create a fine-tune.</div>
  </div>
  <div class="flex flex-row gap-6 justify-center flex-col">
    <a
      href={`/fine_tune/${project_id}/${task_id}/create_finetune`}
      class="btn btn-primary"
    >
      Create Fine-Tune
    </a>
  </div>
</div>
