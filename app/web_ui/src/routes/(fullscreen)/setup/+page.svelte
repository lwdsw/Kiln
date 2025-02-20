<script lang="ts">
  import { _ } from "svelte-i18n";
</script>

<div class="min-h-screen p-4 flex flex-col items-center">
  <div class="grow"></div>
  <img
    src="/images/animated_logo.svg"
    alt="logo"
    class="flex-none w-24 h-24 lg:w-24 lg:h-24"
  />

  <h1 class="text-2xl lg:text-4xl font-bold mt-6 flex-none">
    {$_('welcome.title')}
  </h1>
  <h2 class="text-lg lg:text-xl font-light mt-2 flex-none">
    {$_('welcome.subtitle')}
  </h2>
  <a href="/setup/intro" class="btn btn-primary btn-wide mt-12 flex-none"
    >{$_('welcome.getStarted')}</a
  >
  <div class="text-sm font-light mt-4">
    
    {$_('welcome.viewOur')} <a
      href="https://github.com/Kiln-AI/Kiln/blob/main/app/EULA.md"
      class="link"
      target="_blank">{$_('welcome.licenseAgreement')}</a
    >
  </div>
  <div class="grow-[1.5]"></div>
</div>
