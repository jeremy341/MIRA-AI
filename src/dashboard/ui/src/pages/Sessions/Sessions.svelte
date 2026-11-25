<script lang="ts">
  import PageHeader from '../../lib/components/PageHeader.svelte';
  import { router } from '../../lib/stores/router.svelte';
  import ImportPanel from './ImportPanel.svelte';
  import SessionList from './SessionList.svelte';
  import SessionView from './SessionView.svelte';

  /** Bumped when an import finishes, so the list reloads and shows the new session at once. */
  let listVersion = $state(0);
</script>

{#if router.id}
  {#key router.id}
    <SessionView id={router.id} />
  {/key}
{:else}
  <PageHeader
    title="Sessions"
    description="Past runs of the detector. Open one to replay it, rename it, export it or delete it. Videos and images you import become sessions too."
  />
  <div class="stack">
    <ImportPanel onfinished={() => (listVersion += 1)} />
    {#key listVersion}
      <SessionList />
    {/key}
  </div>
{/if}

<style>
  .stack {
    display: grid;
    gap: var(--space-6);
    min-width: 0;
  }
</style>
