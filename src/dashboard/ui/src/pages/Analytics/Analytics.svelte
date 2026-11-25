<script lang="ts">
  import PageHeader from '../../lib/components/PageHeader.svelte';
  import ArmPanel from './ArmPanel.svelte';
  import HardwarePanel from './HardwarePanel.svelte';
  import SessionAnalytics from './SessionAnalytics.svelte';
</script>

<PageHeader
  title="Analytics"
  description="Session results, the health of the machine that runs the detector, and the sorting arm's event log."
/>

<div class="sections">
  <section aria-label="Session results">
    <SessionAnalytics />
  </section>
  <section aria-label="Hardware">
    <HardwarePanel />
  </section>
  <section aria-label="Sorting arm">
    <ArmPanel />
  </section>
</div>

<style>
  .sections {
    display: grid;
    gap: var(--space-8);
    min-width: 0;
  }
</style>
