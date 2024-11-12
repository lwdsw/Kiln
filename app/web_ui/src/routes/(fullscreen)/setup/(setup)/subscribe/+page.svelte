<script lang="ts">
  import FormContainer from "$lib/utils/form_container.svelte"
  import FormElement from "$lib/utils/form_element.svelte"
  import { type KilnError, createKilnError } from "$lib/utils/error_handlers"

  let email = ""
  let subscribed = false
  let loading = false
  let error: KilnError | null = null

  async function subscribe() {
    subscribed = true
    loading = true
    try {
      // Critical Moments is another project of mine by the same company (same privacy policy)
      // Using it's domain until we have a dedicated kiln server
      const res = await fetch(
        "https://criticalmoments.io/account/api/kiln_subscribe",
        {
          method: "POST",
          body: JSON.stringify({ email }),
          headers: {
            "Content-Type": "application/json",
          },
        },
      )
      if (res.status !== 200) {
        throw new Error("Failed to subscribe")
      }
      subscribed = true
    } catch (e) {
      error = createKilnError(e)
    } finally {
      loading = false
    }
  }
</script>

<div class="grow"></div>
<div class="flex-none flex flex-row items-center justify-center">
  <img src="/logo.svg" alt="logo" class="size-8 mb-3" />
</div>
<h1 class="text-2xl lg:text-4xl flex-none font-bold text-center">Newsletter</h1>
<h3 class="text-base font-medium text-center mt-3 max-w-[600px] mx-auto">
  Zero spam, unsubscribe any time, totally optional.
</h3>

<div
  class="flex-none min-h-[50vh] py-8 h-full flex flex-col py-18 w-full mx-auto items-center justify-center"
>
  {#if !subscribed}
    <h3
      class="text-base mb-5 font-light text-center mt-3 max-w-[420px] mx-auto"
    >
      Subscribe to our newsletter to learn about new features, updates, new
      models, and other Kiln AI news.
    </h3>
    <div class="max-w-[280px] mx-auto">
      <FormContainer
        on:submit={subscribe}
        submit_label="Subscribe"
        keyboard_submit={false}
        submitting={loading}
        {error}
      >
        <FormElement
          id="email"
          inputType="input"
          label="Email"
          bind:value={email}
        />
      </FormContainer>
    </div>
  {:else}
    <p class="text-center text-lg font-medium text-success">Subscribed!</p>
    <p class="text-center">Thanks for subscribing!</p>
  {/if}
</div>

<div class="flex-none flex flex-col place-content-center md:flex-row gap-4">
  <a href="/setup/intro">
    <button class="btn {subscribed ? 'btn-primary' : ''} w-full min-w-[130px]">
      Continue {subscribed ? "" : " Without Subscribing"}
    </button></a
  >
</div>
