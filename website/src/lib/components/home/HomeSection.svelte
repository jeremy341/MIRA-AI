<script lang="ts">
  import type { Snippet } from 'svelte';

  /**
   * A homepage band: a heading (always an h2, it names the landmark), an optional lede, then the content.
   * `tone` sets the ground. `align` centres the heading, or `split` leaves the heading to the content.
   */
  let {
    id,
    title,
    lede,
    tone = 'white',
    align = 'center',
    class: className = '',
    children
  }: {
    id: string;
    title: string;
    lede?: string;
    tone?: 'white' | 'tint' | 'brand';
    align?: 'center' | 'start';
    class?: string;
    children: Snippet;
  } = $props();

  const GROUND = { white: 'bg-app', tint: 'bg-tint', brand: 'on-brand' } as const;
  const TITLE = { white: 'text-ink', tint: 'text-brand-ink', brand: 'text-white' } as const;
  const centred = $derived(align === 'center');
</script>

<section {id} aria-labelledby="{id}-title" class="scroll-mt-20 py-16 sm:py-24 {GROUND[tone]} {className}">
  <div class="shell">
    <div class={centred ? 'text-center' : ''}>
      <h2 id="{id}-title" class="section-title {TITLE[tone]} {centred ? 'mx-auto max-w-[24ch]' : 'max-w-[20ch]'}">{title}</h2>
      {#if lede}<p class="section-lead {centred ? 'mx-auto' : ''} max-w-[56ch]">{lede}</p>{/if}
    </div>
    <div class="mt-10 sm:mt-14">
      {@render children()}
    </div>
  </div>
</section>
