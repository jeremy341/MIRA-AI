<script lang="ts">
  import { classBorderVar } from '$lib/class-colors';
  import { CLASS_BY_ID, type ClassId } from '$lib/site';

  /**
   * Class chip: a small square of the class colour and the class name in ink. The name is always printed,
   * so colour is never the only signal. Class colours appear only on detections, chips and charts.
   */
  let { cls, label, class: className = '' }: { cls: ClassId; label: string; class?: string } = $props();
</script>

<span class="inline-flex items-center gap-2 whitespace-nowrap text-ink {className}">
  <span
    aria-hidden="true"
    class="size-3 shrink-0 border"
    style:background-color={CLASS_BY_ID[cls].cssVar}
    style:border-color={classBorderVar(cls)}
  ></span>
  {label}
</span>
