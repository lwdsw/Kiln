<script lang="ts">
  import "../app.css"
  import "../i18n"
  import { waitLocale } from 'svelte-i18n'
  import { navigating } from "$app/stores"
  import { expoOut } from "svelte/easing"
  import { slide } from "svelte/transition"
  import { onMount } from "svelte"
  import { goto } from "$app/navigation"
  import {
    current_project,
    load_projects,
    projects,
    load_current_task,
    current_task,
  } from "$lib/stores"
  import { get } from "svelte/store"
  import { KilnError } from "$lib/utils/error_handlers"
  import { createKilnError } from "$lib/utils/error_handlers"
  import LanguageSelector from "$lib/components/language_selector.svelte"
  let loading = true
  let load_error: string | null = null
  import posthog from "posthog-js"
  import { browser } from "$app/environment"
  import { beforeNavigate, afterNavigate } from "$app/navigation"

  if (browser) {
    beforeNavigate(() => posthog.capture("$pageleave"))
    afterNavigate(() => posthog.capture("$pageview"))
  }

  // Our (app) routes expect a current project and task.
  // This function checks if we have them, and redirects to the setup flow if not.
  const check_needs_setup = async () => {
    try {
      await load_projects()
      const all_projects = get(projects)
      if (all_projects?.error) {
        throw new KilnError(all_projects.error, null)
      }
      // No projects, go to setup to get started
      if (all_projects?.projects?.length == 0) {
        goto("/setup")
        return
      }
      // We have projects, but no current project. Select screen allows creating tasks, or selecting existing ones.
      if (!$current_project || !$current_project.id) {
        goto("/setup/select_task")
        return
      }
      // we have a current project, but no current task.
      // Go to setup to create one (or select one)
      await load_current_task($current_project)
      if (!$current_task) {
        goto("/setup/select_task")
        return
      }
    } catch (e: unknown) {
      load_error = createKilnError(e).getMessage()
    } finally {
      loading = false
    }
  }

  onMount(() => {
    check_needs_setup()
  })
</script>

<div class="min-h-screen flex flex-col">
  <header class="p-4 flex justify-end">
    <LanguageSelector />
  </header>
  
  <main class="flex-1">
    {#if loading}
      <div class="flex items-center justify-center h-full">
        <span class="loading loading-spinner loading-lg"></span>
      </div>
    {:else if load_error}
      <div class="alert alert-error">
        <span>{load_error}</span>
      </div>
    {:else}
      <slot />
    {/if}
  </main>
</div>
