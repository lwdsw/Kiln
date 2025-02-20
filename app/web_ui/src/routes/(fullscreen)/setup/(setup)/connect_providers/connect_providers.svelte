<script lang="ts">
  import { fade } from "svelte/transition"
  import { onMount } from "svelte"
  import type { OllamaConnection } from "$lib/types"
  import FormElement from "$lib/utils/form_element.svelte"
  import FormContainer from "$lib/utils/form_container.svelte"
  import { KilnError, createKilnError } from "$lib/utils/error_handlers"
  import { client } from "$lib/api_client"

  type Provider = {
    name: string
    id: string
    description: string
    image: string
    featured: boolean
    api_key_steps?: string[]
    api_key_warning?: string
    api_key_fields?: string[]
  }
  import { _ } from "svelte-i18n"

  const providers: Provider[] = [
    {
      name: $_('providers.openrouter.name'),
      id: "openrouter",
      description: $_('providers.openrouter.description'),
      image: "/images/openrouter.svg",
      featured: true,
      api_key_steps: [
        $_('providers.openrouter.steps.1'),
        $_('providers.openrouter.steps.2'),
        $_('providers.openrouter.steps.3')
      ],
    },
    {
      name: $_('providers.openai.name'),
      id: "openai",
      description: $_('providers.openai.description'),
      image: "/images/openai.svg",
      featured: false,
      api_key_steps: [
        $_('providers.openai.steps.1'),
        $_('providers.openai.steps.2'),
        $_('providers.openai.steps.3')
      ],
    },
    {
      name: $_('providers.ollama.name'),
      id: "ollama",
      description: $_('providers.ollama.description'),
      image: "/images/ollama.svg",
      featured: false,
    },
    {
      name: $_('providers.groq.name'),
      id: "groq",
      description: $_('providers.groq.description'),
      image: "/images/groq.svg",
      featured: false,
      api_key_steps: [
        $_('providers.groq.steps.1'),
        $_('providers.groq.steps.2'),
        $_('providers.groq.steps.3')
      ],
    },
    {
      name: $_('providers.fireworks.name'),
      id: "fireworks_ai",
      description: $_('providers.fireworks.description'),
      image: "/images/fireworks.svg",
      api_key_steps: [
        $_('providers.fireworks.steps.1'),
        $_('providers.fireworks.steps.2'),
        $_('providers.fireworks.steps.3'),
        $_('providers.fireworks.steps.4')
      ],
      featured: false,
      api_key_fields: ["API Key", "Account ID"],
    },
    {
      name: $_('providers.amazon_bedrock.name'),
      id: "amazon_bedrock",
      description: $_('providers.amazon_bedrock.description'),
      image: "/images/aws.svg",
      featured: false,
      api_key_steps: [
        $_('providers.amazon_bedrock.steps.1'),
        $_('providers.amazon_bedrock.steps.2'), 
        $_('providers.amazon_bedrock.steps.3'),
        $_('providers.amazon_bedrock.steps.4')
      ],
      api_key_warning: $_('providers.amazon_bedrock.warning'),
      api_key_fields: ["Access Key", "Secret Key"],
    },
    {
      name: $_('providers.openai_compatible.name'),
      id: "openai_compatible",
      description: $_('providers.openai_compatible.description'),
      image: "/images/api.svg",
      featured: false,
    },
  ]

  type ProviderStatus = {
    connected: boolean
    error: string | null
    custom_description: string | null
    connecting: boolean
  }
  let status: { [key: string]: ProviderStatus } = {
    ollama: {
      connected: false,
      connecting: false,
      error: null,
      custom_description: null,
    },
    openai: {
      connected: false,
      connecting: false,
      error: null,
      custom_description: null,
    },
    openrouter: {
      connected: false,
      connecting: false,
      error: null,
      custom_description: null,
    },
    groq: {
      connected: false,
      connecting: false,
      error: null,
      custom_description: null,
    },
    amazon_bedrock: {
      connected: false,
      connecting: false,
      error: null,
      custom_description: null,
    },
    fireworks_ai: {
      connected: false,
      connecting: false,
      error: null,
      custom_description: null,
    },
    openai_compatible: {
      connected: false,
      connecting: false,
      error: null,
      custom_description: null,
    },
  }

  export let has_connected_providers = false
  $: has_connected_providers = Object.values(status).some(
    (provider) => provider.connected,
  )
  export let intermediate_step = false
  let api_key_provider: Provider | null = null
  $: {
    intermediate_step = api_key_provider != null
  }

  const disconnect_provider = async (provider: Provider) => {
    if (provider.id === "ollama") {
      alert(
        $_('providers.ollama.disconnectAlert')
      )
      return
    }
    if (
      !confirm(
        $_('providers.ollama.disconnectConfirm')
      )
    ) {
      return
    }
    try {
      const { error: disconnect_error } = await client.POST(
        "/api/provider/disconnect_api_key",
        {
          params: {
            query: {
              provider_id: provider.id,
            },
          },
        },
      )
      if (disconnect_error) {
        throw disconnect_error
      }

      status[provider.id].connected = false
    } catch (e) {
      console.error("disconnect_provider error", e)
      alert($_('errors.failed_disconnect'))
      return
    }
  }

  const connect_provider = (provider: Provider) => {
    if (status[provider.id].connected) {
      return
    }
    if (provider.id === "ollama") {
      connect_ollama()
    }
    if (provider.id === "openai_compatible") {
      show_custom_api_dialog()
    }

    if (provider.api_key_steps) {
      api_key_provider = provider
    }
  }

  let custom_ollama_url: string | null = null

  const connect_ollama = async (user_initated: boolean = true) => {
    status.ollama.connected = false
    status.ollama.connecting = user_initated

    let data: OllamaConnection | null = null
    try {
      const { data: req_data, error: req_error } = await client.GET(
        "/api/provider/ollama/connect",
        {
          params: {
            query: {
              custom_ollama_url: custom_ollama_url || undefined,
            },
          },
        },
      )
      if (req_error) {
        throw req_error
      }
      data = req_data
    } catch (e) {
      if (
        e &&
        typeof e === "object" &&
        "message" in e &&
        typeof e.message === "string"
      ) {
        status.ollama.error = e.message
      } else {
        status.ollama.error = $_('errors.ollama_connect')
      }
      status.ollama.connected = false
      return
    } finally {
      status.ollama.connecting = false
    }
    if (
      data.supported_models.length === 0 &&
      (!data.untested_models || data.untested_models.length === 0)
    ) {
      status.ollama.error = $_('providers.ollama.error')
      return
    }
    status.ollama.error = null
    status.ollama.connected = true
    const supported_models_str =
      data.supported_models.length > 0
        ? $_('providers.ollama.supportedModels')  + data.supported_models.join(", ") + ". "
        : $_('providers.ollama.supportedModelsNone')
    const untested_models_str =
      data.untested_models && data.untested_models.length > 0
        ? $_('providers.ollama.untestedModels') + data.untested_models.join(", ") + ". "
        : ""
    const custom_url_str =
      custom_ollama_url && custom_ollama_url == "http://localhost:11434"
        ? ""
        : $_('providers.ollama.customUrl') + custom_ollama_url
    status.ollama.custom_description =
      $_('providers.ollama.connected') +
      supported_models_str +
      untested_models_str +
      custom_url_str
  }

  let api_key_issue = false
  let api_key_submitting = false
  let api_key_message: string | null = null
  const submit_api_key = async () => {
    const apiKeyFields = document.getElementById(
      "api-key-fields",
    ) as HTMLDivElement
    const inputs = apiKeyFields.querySelectorAll("input")
    const apiKeyData: Record<string, string> = {}
    for (const input of inputs) {
      apiKeyData[input.id] = input.value
      if (!input.value) {
        api_key_issue = true
        return
      }
    }

    api_key_issue = false
    api_key_message = null
    api_key_submitting = true
    try {
      const provider_id = api_key_provider ? api_key_provider.id : ""
      let res = await fetch(
        "http://localhost:8757/api/provider/connect_api_key",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            provider: provider_id,
            key_data: apiKeyData,
          }),
        },
      )
      let data = await res.json()

      if (res.status !== 200) {
        api_key_message =
          data.message || $_('errors.failed_connect')
        return
      }

      api_key_issue = false
      api_key_message = null
      status[provider_id].connected = true
      api_key_provider = null
    } catch (e) {
      console.error("submit_api_key error", e)
      api_key_message = $_('errors.failed_connect_exception', { error: e })
      api_key_issue = true
      return
    } finally {
      api_key_submitting = false
    }
  }

  let loading_initial_providers = true
  let initial_load_failure = false
  type CustomOpenAICompatibleProvider = {
    name: string
    base_url: string
    api_key: string
  }
  let custom_openai_compatible_providers: CustomOpenAICompatibleProvider[] = []
  const check_existing_providers = async () => {
    try {
      let res = await fetch("http://localhost:8757/api/settings")
      let data = await res.json()
      if (data["open_ai_api_key"]) {
        status.openai.connected = true
      }
      if (data["groq_api_key"]) {
        status.groq.connected = true
      }
      if (data["bedrock_access_key"] && data["bedrock_secret_key"]) {
        status.amazon_bedrock.connected = true
      }
      if (data["open_router_api_key"]) {
        status.openrouter.connected = true
      }
      if (data["fireworks_api_key"] && data["fireworks_account_id"]) {
        status.fireworks_ai.connected = true
      }
      if (data["ollama_base_url"]) {
        custom_ollama_url = data["ollama_base_url"]
      }
      if (
        data["openai_compatible_providers"] &&
        data["openai_compatible_providers"].length > 0
      ) {
        status.openai_compatible.connected = true
        custom_openai_compatible_providers = data["openai_compatible_providers"]
      }
    } catch (e) {
      console.error("check_existing_providers error", e)
      initial_load_failure = true
    } finally {
      loading_initial_providers = false
    }
  }

  onMount(async () => {
    await check_existing_providers()
    // Check Ollama every load, as it can be closed. More epmemerial (and local/cheap/fast)
    connect_ollama(false).then(() => {
      // Clear the error as the user didn't initiate this run
      status["ollama"].error = null
    })
  })

  function show_custom_ollama_url_dialog() {
    // @ts-expect-error showModal is not a method on HTMLElement
    document.getElementById("ollama_dialog")?.showModal()
  }

  function show_custom_api_dialog() {
    // @ts-expect-error showModal is not a method on HTMLElement
    document.getElementById("openai_compatible_dialog")?.showModal()
  }

  let new_provider_name = ""
  let new_provider_base_url = ""
  let new_provider_api_key = ""
  let adding_new_provider = false
  let new_provider_error: KilnError | null = null
  async function add_new_provider() {
    try {
      adding_new_provider = true
      if (!new_provider_base_url.startsWith("http")) {
        throw new Error($_('errors.base_url_http'))
      }

      const { error: save_error } = await client.POST(
        "/api/provider/openai_compatible",
        {
          params: {
            query: {
              name: new_provider_name,
              base_url: new_provider_base_url,
              api_key: new_provider_api_key,
            },
          },
        },
      )
      if (save_error) {
        throw save_error
      }

      // Refresh to trigger the UI update
      custom_openai_compatible_providers = [
        ...custom_openai_compatible_providers,
        {
          name: new_provider_name,
          base_url: new_provider_base_url,
          api_key: new_provider_api_key,
        },
      ]

      // Reset the form
      new_provider_name = ""
      new_provider_base_url = ""
      new_provider_api_key = ""
      new_provider_error = null

      status.openai_compatible.connected = true
      // @ts-expect-error daisyui does not add types
      document.getElementById("openai_compatible_dialog")?.close()
    } catch (e) {
      new_provider_error = createKilnError(e)
    } finally {
      adding_new_provider = false
    }
  }

  async function remove_openai_compatible_provider_at_index(index: number) {
    if (index < 0 || index >= custom_openai_compatible_providers.length) {
      return
    }
    try {
      let provider = custom_openai_compatible_providers[index]

      const { error: delete_error } = await client.DELETE(
        "/api/provider/openai_compatible",
        {
          params: {
            query: {
              name: provider.name,
            },
          },
        },
      )
      if (delete_error) {
        throw delete_error
      }

      // Update UI
      custom_openai_compatible_providers =
        custom_openai_compatible_providers.filter(
          (v, _) => v.name !== provider.name,
        )
      if (custom_openai_compatible_providers.length === 0) {
        status.openai_compatible.connected = false
      }
    } catch (e) {
      alert($_('errors.failed_connect') + e)
    }
  }
</script>

<div class="w-full">
  {#if api_key_provider}
    <div class="grow h-full max-w-[400px] flex flex-col place-content-center">
      <div class="grow"></div>
      {#if api_key_provider.api_key_warning}
        <div role="alert" class="alert alert-warning my-4">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="h-6 w-6 shrink-0 stroke-current"
            fill="none"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
          <span>
            <!-- eslint-disable-next-line svelte/no-at-html-tags -->
            {@html api_key_provider.api_key_warning.replace(/\n/g, "<br>")}
          </span>
        </div>
      {/if}

      <h1 class="text-xl font-medium flex-none text-center">
        {$_('common.connect')} {api_key_provider.name}
      </h1>

      <ol class="flex-none my-2 text-gray-700">
        {#each api_key_provider.api_key_steps || [] as step}
          <li class="list-decimal pl-1 mx-8 my-4">
            <!-- eslint-disable-next-line svelte/no-at-html-tags -->
            {@html step.replace(
              /https?:\/\/\S+/g,
              '<a href="$&" class="link underline" target="_blank">$&</a>',
            )}
          </li>
        {/each}
      </ol>
      {#if api_key_message}
        <p class="text-error text-center pb-4">{api_key_message}</p>
      {/if}
      <div class="flex flex-row gap-4 items-center">
        <div class="grow flex flex-col gap-2" id="api-key-fields">
          {#each api_key_provider.api_key_fields || ["API Key"] as field}
            <input
              type="text"
              id={field}
              placeholder={field}
              class="input input-bordered w-full max-w-[300px] {api_key_issue
                ? 'input-error'
                : ''}"
            />
          {/each}
        </div>
        <button
          class="btn min-w-[130px]"
          on:click={submit_api_key}
          disabled={api_key_submitting}
        >
          {#if api_key_submitting}
            <div class="loading loading-spinner loading-md"></div>
          {:else}
            {$_('common.connect')}
          {/if}
        </button>
      </div>
      <button
        class="link text-center text-sm mt-8"
        on:click={() => (api_key_provider = null)}
      >
        {$_('common.cancel')} {api_key_provider.name}
      </button>
      <div class="grow-[1.5]"></div>
    </div>
  {:else}
    <div class="w-full flex flex-col gap-6 max-w-lg">
      {#each providers as provider}
        {@const is_connected =
          status[provider.id] && status[provider.id].connected}
        <div class="flex flex-row gap-4 items-center">
          <img
            src={provider.image}
            alt={provider.name}
            class="flex-none p-1 {provider.featured
              ? 'size-12'
              : 'size-10 mx-1'}"
          />
          <div class="flex flex-col grow pr-4">
            <h3
              class={provider.featured
                ? "text-large font-bold"
                : "text-base font-medium"}
            >
              {provider.name}
              {#if provider.featured}
                <div class="badge ml-2 badge-secondary text-xs font-medium">
                  {$_('common.recommended')}
                </div>
              {/if}
            </h3>
            {#if status[provider.id] && status[provider.id].error}
              <p class="text-sm text-error" in:fade>
                {status[provider.id].error}
              </p>
            {:else}
              <p class="text-sm text-gray-500">
                {status[provider.id].custom_description || provider.description}
              </p>
            {/if}
            {#if provider.id === "ollama" && status[provider.id] && status[provider.id].error}
              <button
                class="link text-left text-sm text-gray-500"
                on:click={show_custom_ollama_url_dialog}
              >
                {$_('providers.ollama.dialog.setCustomUrl')}
              </button>
            {/if}
          </div>

          {#if loading_initial_providers}
            <!-- Light loading state-->
            <div class="btn md:min-w-[100px] skeleton bg-base-200"></div>
            &nbsp;
          {:else if is_connected && provider.id === "openai_compatible"}
            <button
              class="btn md:min-w-[100px]"
              on:click={() => show_custom_api_dialog()}
            >
              {$_('common.manage')}
            </button>
          {:else if is_connected}
            <button
              class="btn md:min-w-[100px] hover:btn-error group"
              on:click={() => disconnect_provider(provider)}
            >
              <img
                src="/images/circle-check.svg"
                class="size-6 group-hover:hidden"
                alt="Connected"
              />
              <span class="text-xs hidden group-hover:inline">{$_('common.disconnect')}</span>
            </button>
          {:else if status[provider.id].connecting}
            <div class="btn md:min-w-[100px]">
              <div class=" loading loading-spinner loading-md"></div>
            </div>
          {:else if initial_load_failure}
            <div>
              <div class="btn md:min-w-[100px] btn-error text-xs">{$_('common.error')}</div>
              <div class="text-xs text-gray-500 text-center pt-1">
                {$_('common.reload_page')}
              </div>
            </div>
          {:else}
            <button
              class="btn md:min-w-[100px]"
              on:click={() => connect_provider(provider)}
            >
              {$_('common.connect')}
            </button>
          {/if}
        </div>
      {/each}
    </div>
  {/if}
</div>

<dialog id="ollama_dialog" class="modal">
  <div class="modal-box">
    <form method="dialog">
      <button
        class="btn btn-sm text-xl btn-circle btn-ghost absolute right-2 top-2 focus:outline-none"
        >✕</button
      >
    </form>

    <h3 class="text-lg font-bold">{$_('providers.ollama.dialog.title')}</h3>
    <p class="text-sm font-light mb-8">
      {$_('providers.ollama.dialog.description')}
    </p>
    <FormElement
      id="ollama_url"
      label={$_('providers.ollama.dialog.urlLabel')}
      info_description={$_('providers.ollama.dialog.urlInfo')}
      bind:value={custom_ollama_url}
      placeholder={$_('providers.ollama.dialog.urlPlaceholder')}
    />
    <div class="flex flex-row gap-4 items-center mt-4 justify-end">
      <form method="dialog">
        <button class="btn">{$_('common.cancel')}</button>
      </form>
      <button
        class="btn btn-primary"
        disabled={!custom_ollama_url}
        on:click={() => {
          connect_ollama(true)
          // @ts-expect-error showModal is not a method on HTMLElement
          document.getElementById("ollama_dialog")?.close()
        }}
      >
        {$_('common.connect')}
      </button>
    </div>
  </div>
  <form method="dialog" class="modal-backdrop">
    <button>close</button>
  </form>
</dialog>

<dialog id="openai_compatible_dialog" class="modal">
  <div class="modal-box">
    <form method="dialog">
      <button
        class="btn btn-sm text-xl btn-circle btn-ghost absolute right-2 top-2 focus:outline-none"
        >✕</button
      >
    </form>

    <h3 class="text-lg font-bold flex flex-row gap-4">{$_('providers.openai_compatible.dialog.title')}</h3>
    <p class="text-sm font-light mb-8">
      {$_('providers.openai_compatible.dialog.description')}
    </p>
    {#if custom_openai_compatible_providers.length > 0}
      <div class="flex flex-col gap-2">
        <div class="font-medium">{$_('providers.openai_compatible.dialog.existing_apis')}</div>
        {#each custom_openai_compatible_providers as provider, index}
          <div class="flex flex-row gap-3 card bg-base-200 px-4 items-center">
            <div class="text-sm">{provider.name}</div>
            <div class="text-sm text-gray-500 grow truncate">
              {provider.base_url}
            </div>
            <button
              class="btn btn-sm btn-ghost"
              on:click={() => remove_openai_compatible_provider_at_index(index)}
            >
              {$_('common.remove')}
            </button>
          </div>
        {/each}
      </div>
    {/if}
    <div class="flex flex-col gap-2 mt-8">
      <div class="font-medium">{$_('providers.openai_compatible.dialog.add_new_api')}</div>
      <FormContainer
        submit_label={$_('common.add')}
        on:submit={add_new_provider}
        gap={2}
        submitting={adding_new_provider}
        error={new_provider_error}
      >
        <FormElement
          id="name"
          label={$_('providers.openai_compatible.dialog.name_label')}
          bind:value={new_provider_name}
          placeholder={$_('providers.openai_compatible.dialog.name_placeholder')}
          info_description={$_('providers.openai_compatible.dialog.name_info')}
        />
        <FormElement
          id="base_url"
          label={$_('providers.openai_compatible.dialog.base_url_label')}
          bind:value={new_provider_base_url}
          placeholder={$_('providers.openai_compatible.dialog.base_url_placeholder')}
          info_description={$_('providers.openai_compatible.dialog.base_url_info')}
        />
        <FormElement
          id="api_key"
          label={$_('providers.openai_compatible.dialog.api_key_label')}
          optional={true}
          bind:value={new_provider_api_key}
          placeholder={$_('providers.openai_compatible.dialog.api_key_placeholder')}
          info_description={$_('providers.openai_compatible.dialog.api_key_info')}
        />
      </FormContainer>
    </div>

    <form method="dialog" class="modal-backdrop">
      <button>close</button>
    </form>
  </div>
</dialog>
