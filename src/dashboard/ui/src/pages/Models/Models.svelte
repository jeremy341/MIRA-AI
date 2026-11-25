<script lang="ts">
  // Placeholder for U2. Replace this file (and keep the default export) to build the Models page.
  import Button from '../../lib/components/Button.svelte';
  import Card from '../../lib/components/Card.svelte';
  import EmptyState from '../../lib/components/EmptyState.svelte';
  import PageHeader from '../../lib/components/PageHeader.svelte';
</script>

<PageHeader title="Models" description="Available detection models, side by side on the same image, and benchmark runs." />

<Card variant="panel">
  <EmptyState
    icon="models"
    title="Models are coming next"
    description="Compare models on the same image and benchmark them on a dataset."
  >
    {#snippet actions()}
      <Button variant="secondary" href="#/settings">Choose a model in Settings</Button>
    {/snippet}
  </EmptyState>
</Card>
