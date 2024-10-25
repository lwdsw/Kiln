<script lang="ts">
  import hljs from "highlight.js/lib/core"
  import json from "highlight.js/lib/languages/json"
  hljs.registerLanguage("json", json)

  export let raw_output: string
  let formatted_json_html: string | null = null
  $: {
    try {
      const json_output = JSON.parse(raw_output)
      // Strings are JSON, but not really
      if (typeof json_output !== "string") {
        formatted_json_html = JSON.stringify(json_output, null, 2)
        formatted_json_html = hljs.highlight(formatted_json_html, {
          language: "json",
        }).value
      }
    } catch (e) {
      formatted_json_html = null
    }
  }
</script>

<head>
  <link rel="stylesheet" href="/styles/highlightjs.min.css" />
</head>

<!-- eslint-disable svelte/no-at-html-tags -->
<pre
  class="bg-base-200 p-4 rounded-lg whitespace-pre-wrap break-words {raw_output.length >
  400
    ? 'text-xs'
    : ''}">{#if formatted_json_html}{@html formatted_json_html}{:else}{raw_output}{/if}
</pre>
<!-- eslint-enable svelte/no-at-html-tags -->
