<script lang="ts">
  // Self-hosted fonts (no request to Google): Plus Jakarta Sans for text and display, Space Mono for numbers
  // and commands. The browser downloads only the latin subsets a page needs.
  import '@fontsource-variable/plus-jakarta-sans';
  import '@fontsource/space-mono/400.css';
  import '../app.css';

  let { children } = $props();
</script>

{@render children()}
