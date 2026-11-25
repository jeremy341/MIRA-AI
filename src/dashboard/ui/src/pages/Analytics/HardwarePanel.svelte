<script lang="ts">
  import { api, describeError, isRouteMissing } from '../../lib/api';
  import Card from '../../lib/components/Card.svelte';
  import EmptyState from '../../lib/components/EmptyState.svelte';
  import LineChart from '../../lib/components/charts/LineChart.svelte';
  import Notice from '../../lib/components/Notice.svelte';
  import SegmentedControl from '../../lib/components/SegmentedControl.svelte';
  import StatTile from '../../lib/components/StatTile.svelte';
  import { formatMegabytes } from '../../lib/format';
  import { formatTick } from '../../lib/charts/scale';
  import { startPolling } from '../../lib/poll';
  import type { HardwareCurrent, HardwarePoint } from '../../lib/types';
  import { HARDWARE_POINTS, HARDWARE_RANGES, clockLabel, hasTemperature, minutesFor, timeMs } from './analytics-logic';

  let current = $state<HardwareCurrent | null>(null);
  let points = $state<HardwarePoint[]>([]);
  let range = $state('60');
  let error = $state<string | null>(null);
  let unavailable = $state(false);

  const xs = $derived(points.map((point) => timeMs(point.ts)));
  const temperatureKnown = $derived(hasTemperature(points) || (current !== null && current.temperature_c !== null));
  const rangeOptions = HARDWARE_RANGES.map((item) => ({ value: item.value, label: item.label }));
  const percentFormat = (value: number) => `${formatTick(value)}%`;

  function handleFailure(failure: unknown, fallback: string) {
    if (isRouteMissing(failure)) {
      unavailable = true;
      return;
    }
    error = describeError(failure, fallback);
  }

  async function loadCurrent() {
    try {
      current = await api.v1.getHardwareCurrent();
      error = null;
      unavailable = false;
    } catch (failure) {
      handleFailure(failure, 'The current readings could not be loaded.');
    }
  }

  async function loadHistory(minutes: number) {
    try {
      const response = await api.v1.getHardwareHistory(minutes, HARDWARE_POINTS);
      points = response.points;
      error = null;
      unavailable = false;
    } catch (failure) {
      handleFailure(failure, 'The history could not be loaded.');
    }
  }

  // Current readings every 5 seconds, history every 30 seconds. Both pause while the page is hidden.
  $effect(() => startPolling(loadCurrent, { intervalMs: 5000 }));

  // A new range restarts the history poll with the new window.
  $effect(() => {
    const minutes = minutesFor(range);
    return startPolling(() => loadHistory(minutes), { intervalMs: 30_000 });
  });

  const memoryHint = $derived(
    current ? `${formatMegabytes(current.memory_used_mb)} of ${formatMegabytes(current.memory_total_mb)}` : undefined,
  );
</script>

<Card title="Hardware" description="The machine that runs the detector: processor, memory and temperature.">
  {#if unavailable}
    <EmptyState compact icon="analytics" title="Hardware readings are not available yet" description="This server does not have the hardware API." />
  {:else}
    {#if current?.is_raspberry_pi}
      <Notice tone="info">
        <p>This is a Raspberry Pi. Temperature comes from the board's thermal zone or from vcgencmd. If no temperature shows, the board may not expose its sensor to this process.</p>
      </Notice>
    {/if}

    {#if error}
      <Notice tone="danger"><p>{error}</p></Notice>
    {/if}

    <div class="tiles">
      <StatTile label="Processor" value={current ? current.cpu_percent.toFixed(1) : '-'} unit={current ? '%' : undefined} hint={current ? `${current.cpu_count} cores` : undefined} />
      <StatTile label="Memory" value={current ? current.memory_percent.toFixed(1) : '-'} unit={current ? '%' : undefined} hint={memoryHint} />
      <StatTile
        label="Temperature"
        value={current?.temperature_c !== null && current?.temperature_c !== undefined ? current.temperature_c.toFixed(1) : '-'}
        unit={current?.temperature_c !== null && current?.temperature_c !== undefined ? '°C' : undefined}
        hint={current && current.temperature_c === null ? 'No temperature sensor' : undefined}
      />
      <StatTile label="Load, 1 minute" value={current?.load_1m !== null && current?.load_1m !== undefined ? current.load_1m.toFixed(2) : '-'} />
    </div>

    <div class="range">
      <SegmentedControl label="History window" value={range} options={rangeOptions} onchange={(value) => (range = value)} />
    </div>

    {#if points.length === 0}
      <p class="note" role="status">Loading the history</p>
    {:else}
      <div class="charts">
        <LineChart
          title="Processor and memory"
          description="Average processor and memory use in each part of the selected window. Gaps mean no sample was taken."
          x={xs}
          series={[
            { label: 'Processor', color: 'var(--accent)', values: points.map((p) => p.cpu_percent) },
            { label: 'Memory', color: '#7a5200', values: points.map((p) => p.memory_percent) },
          ]}
          yDomain={[0, 100]}
          xFormat={clockLabel}
          yFormat={percentFormat}
          xHeading="Time"
        />
        {#if temperatureKnown}
          <LineChart
            title="Temperature"
            description="Average temperature in degrees Celsius in each part of the selected window."
            x={xs}
            series={[{ label: 'Temperature', color: 'var(--ink)', values: points.map((p) => p.temperature_c) }]}
            xFormat={clockLabel}
            yFormat={(value) => `${formatTick(value)} °C`}
            xHeading="Time"
          />
        {:else}
          <div class="no-sensor">
            <EmptyState compact icon="dot" title="No temperature sensor" description="This device did not report a temperature, so there is no temperature history to chart." />
          </div>
        {/if}
      </div>
    {/if}
    <p class="note">Showing about {HARDWARE_POINTS} points over the window. Last update {current ? clockLabel(timeMs(current.ts)) : 'not yet'}.</p>
  {/if}
</Card>

<style>
  .tiles {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(10.5rem, 1fr));
    gap: var(--space-3);
    margin: var(--space-4) 0;
  }
  .range {
    margin-bottom: var(--space-5);
    max-width: 100%;
    overflow-x: auto;
  }
  .charts {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(min(100%, 22rem), 1fr));
    gap: var(--space-6);
    align-items: start;
  }
  .no-sensor {
    display: grid;
    align-content: center;
    min-height: 12rem;
    border-radius: var(--radius-control);
    background: var(--app);
  }
  .note {
    margin-top: var(--space-3);
    font-size: var(--text-micro);
    color: var(--ink-soft);
  }
</style>
