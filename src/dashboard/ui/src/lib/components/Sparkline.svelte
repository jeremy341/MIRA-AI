<script lang="ts">
  interface Props {
    values: readonly number[];
    label: string;
    width?: number;
    height?: number;
  }

  let { values, label, width = 160, height = 36 }: Props = $props();

  const points = $derived.by(() => {
    const finite = values.filter((v) => Number.isFinite(v));
    if (finite.length < 2) return '';
    const min = Math.min(...finite);
    const max = Math.max(...finite);
    const span = max - min || 1;
    return finite
      .map((v, i) => {
        const x = (i / (finite.length - 1)) * width;
        const y = height - 3 - ((v - min) / span) * (height - 6);
        return `${x.toFixed(1)},${y.toFixed(1)}`;
      })
      .join(' ');
  });
</script>

{#if points}
  <svg class="spark" viewBox="0 0 {width} {height}" role="img" aria-label={label} preserveAspectRatio="none">
    <polyline points={points} fill="none" stroke="var(--accent)" stroke-width="2" stroke-linejoin="round" stroke-linecap="round" vector-effect="non-scaling-stroke" />
  </svg>
{/if}

<style>
  .spark {
    width: 100%;
    height: 2.25rem;
  }
</style>
