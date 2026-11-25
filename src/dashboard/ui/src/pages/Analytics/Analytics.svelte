<script lang="ts">
  // Placeholder for U2. Replace this file (and keep the default export) to build the Analytics page.
  import Button from '../../lib/components/Button.svelte';
  import Card from '../../lib/components/Card.svelte';
  import EmptyState from '../../lib/components/EmptyState.svelte';
  import PageHeader from '../../lib/components/PageHeader.svelte';
</script>

<PageHeader title="Analytics" description="Charts for session results, hardware history and sorting-arm events." />

<Card variant="panel">
  <EmptyState
    icon="analytics"
    title="Analytics are coming next"
    description="Charts for session results, hardware history and the sorting-arm event log."
  >
    {#snippet actions()}
      <Button variant="secondary" href="#/detect">Back to Detect</Button>
    {/snippet}
  </EmptyState>
</Card>
