<script lang="ts">
  export let title: string
  const id: string = "dialog-" + Math.random().toString(36)
  type ActionButton = {
    label: string
    action?: () => void
    isCancel?: boolean
  }
  export let action_buttons: ActionButton[] = []

  export function show() {
    // @ts-expect-error showModal is not a method on HTMLElement
    document.getElementById(id)?.showModal()
  }

  export function close() {
    // @ts-expect-error close is not a method on HTMLElement
    document.getElementById(id)?.close()
  }
</script>

<dialog {id} class="modal">
  <div class="modal-box">
    <form method="dialog">
      <button
        class="btn btn-sm text-xl btn-circle btn-ghost absolute right-2 top-2 focus:outline-none"
        >✕</button
      >
    </form>
    <h3 class="text-lg font-medium mb-1">
      {title}
    </h3>
    <slot />

    {#if action_buttons.length > 0}
      <div class="flex flex-row gap-2 justify-end mt-6">
        {#each action_buttons as button}
          {#if button.isCancel}
            <form method="dialog">
              <button class="btn btn-sm h-10 btn-outline min-w-24"
                >{button.label || "Cancel"}</button
              >
            </form>
          {:else}
            <button
              class="btn btn-sm h-10 min-w-24 btn-secondary"
              on:click={button.action}
            >
              {button.label || "Confirm"}
            </button>
          {/if}
        {/each}
      </div>
    {/if}
  </div>
  <form method="dialog" class="modal-backdrop">
    <button>close</button>
  </form>
</dialog>
