<script lang="ts">
  import PageHeader from '../../lib/components/PageHeader.svelte';
  import Tabs from '../../lib/components/Tabs.svelte';
  import BenchmarkTab from './BenchmarkTab.svelte';
  import CompareTab from './CompareTab.svelte';

  type Tab = 'compare' | 'benchmark';
  let tab = $state<Tab>('compare');
  const items = [
    { value: 'compare', label: 'Compare' },
    { value: 'benchmark', label: 'Benchmark' },
  ] as const;
</script>

<PageHeader
  title="Models"
  description="Compare the installed models on one image, or benchmark them on a labelled dataset. Both keep their past runs."
/>

<Tabs label="Models" value={tab} {items} idPrefix="models-tab" onchange={(value) => (tab = value)} />

<div id="models-tab-panel" role="tabpanel" aria-labelledby="models-tab-{tab}" class="panel">
  {#if tab === 'compare'}
    <CompareTab />
  {:else}
    <BenchmarkTab />
  {/if}
</div>

<style>
  .panel {
    margin-top: var(--space-6);
    min-width: 0;
  }
</style>
