<script lang="ts">
  // Placeholder for U2. Replace this file (and keep the default export) to build the Sessions page.
  import Button from '../../lib/components/Button.svelte';
  import Card from '../../lib/components/Card.svelte';
  import EmptyState from '../../lib/components/EmptyState.svelte';
  import PageHeader from '../../lib/components/PageHeader.svelte';
</script>

<PageHeader title="Sessions" description="Past runs of the detector, with their totals and exports." />

<Card variant="panel">
  <EmptyState
    icon="sessions"
    title="Sessions are coming next"
    description="Review past runs, replay them and export results."
  >
    {#snippet actions()}
      <Button variant="secondary" href="#/detect">Start a session on Detect</Button>
    {/snippet}
  </EmptyState>
</Card>
