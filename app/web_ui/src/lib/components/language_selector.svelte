<script lang="ts">
  import { locale } from 'svelte-i18n'

  function setLocale(lang: string) {
    localStorage.setItem('lang', lang)
    locale.set(lang)
  }

  const languages = [
    { code: 'zh', name: '中文' },
    { code: 'en', name: 'English' }
  ]
</script>

<div class="dropdown dropdown-end">
  <div tabindex="0" role="button" class="btn btn-ghost">
    <span class="text-sm">{$locale === 'zh' ? '中文' : 'English'}</span>
  </div>
  <ul tabindex="0" class="dropdown-content z-[1] menu p-2 shadow bg-base-100 rounded-box w-32">
    {#each languages as lang}
      <li>
        <button
          class="text-sm {$locale === lang.code ? 'active' : ''}"
          on:click={() => setLocale(lang.code)}
        >
          {lang.name}
        </button>
      </li>
    {/each}
  </ul>
</div>

<style>
  .active {
    background-color: hsl(var(--p) / 0.1);
    color: hsl(var(--p));
  }
</style>