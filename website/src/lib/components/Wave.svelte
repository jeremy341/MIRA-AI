<script lang="ts">
  /**
   * The wave edge between two bands. Put it as the last child of the upper band and give it the colour of the band
   * below. Two layers of our own 240px wave tile drift sideways at different speeds. The tile is used as a CSS mask
   * so the fill can be any colour token, and only `transform` is animated. Reduced motion stops the drift.
   */
  let { fill = 'var(--app)', class: className = '' }: { fill?: string; class?: string } = $props();
</script>

<div aria-hidden="true" class="wave {className}" style:--wave-fill={fill}>
  <span class="wave-layer wave-back"></span>
  <span class="wave-layer wave-front"></span>
</div>

<style>
  .wave {
    --tile: 240px;
    position: relative;
    height: 40px;
    overflow: hidden;
    /* Overlap the next band by a pixel so no hairline shows between them at fractional zoom levels. */
    margin-bottom: -1px;
    pointer-events: none;
  }
  .wave-layer {
    position: absolute;
    top: 0;
    bottom: 0;
    left: 0;
    width: calc(100% + var(--tile));
    background: var(--wave-fill);
    -webkit-mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='240' height='40' viewBox='0 0 240 40'%3E%3Cpath d='M0 22C40 6 80 6 120 22S200 38 240 22V40H0Z'/%3E%3C/svg%3E")
      repeat-x 0 100% / var(--tile) 40px;
    mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='240' height='40' viewBox='0 0 240 40'%3E%3Cpath d='M0 22C40 6 80 6 120 22S200 38 240 22V40H0Z'/%3E%3C/svg%3E")
      repeat-x 0 100% / var(--tile) 40px;
    will-change: transform;
  }
  .wave-front {
    animation: wave-drift 11s linear infinite;
  }
  .wave-back {
    opacity: 0.38;
    top: -7px;
    animation: wave-drift-back 17s linear infinite;
  }
  @keyframes wave-drift {
    to {
      transform: translateX(calc(var(--tile) * -1));
    }
  }
  @keyframes wave-drift-back {
    from {
      transform: translateX(calc(var(--tile) * -1));
    }
    to {
      transform: translateX(0);
    }
  }
  @media (max-width: 40rem) {
    .wave {
      height: 28px;
    }
    .wave-layer {
      mask-size: 168px 28px;
      -webkit-mask-size: 168px 28px;
    }
    .wave {
      --tile: 168px;
    }
  }
  @media (prefers-reduced-motion: reduce) {
    .wave-layer {
      animation: none;
    }
  }
</style>
