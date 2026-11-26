<!--
  The MIRA logo at hero size: the same paths as static/mira.svg, without the dark tile. On load the four viewfinder
  corners close in and the M draws itself once. Decorative, so it is hidden from assistive technology.
-->
<svg class="mark" viewBox="3 3 26 26" aria-hidden="true" focusable="false">
  <g class="corners" fill="none" stroke="#fff" stroke-opacity=".42" stroke-width="1.8" stroke-linecap="round">
    <path class="tl" d="M6.5 11.5v-3a2 2 0 0 1 2-2h3" />
    <path class="tr" d="M20.5 6.5h3a2 2 0 0 1 2 2v3" />
    <path class="br" d="M25.5 20.5v3a2 2 0 0 1-2 2h-3" />
    <path class="bl" d="M11.5 25.5h-3a2 2 0 0 1-2-2v-3" />
  </g>
  <path
    class="letter"
    d="M10.5 20.5v-9l5.5 6.2 5.5-6.2v9"
    pathLength="1"
    fill="none"
    stroke="#fff"
    stroke-width="2.6"
    stroke-linecap="round"
    stroke-linejoin="round"
  />
  <circle class="dot" cx="16" cy="22.4" r="1.9" fill="#b9c9ff" />
</svg>

<style>
  .mark {
    display: block;
    width: 100%;
    height: auto;
  }
  .corners path {
    animation: close-in 0.8s var(--ease-out) both;
  }
  .tl {
    --from: translate(-1.6px, -1.6px);
  }
  .tr {
    --from: translate(1.6px, -1.6px);
  }
  .br {
    --from: translate(1.6px, 1.6px);
  }
  .bl {
    --from: translate(-1.6px, 1.6px);
  }
  .letter {
    stroke-dasharray: 1 1;
    animation: draw 0.9s 0.25s var(--ease-out) both;
  }
  .dot {
    transform-origin: 16px 22.4px;
    animation: pop 0.45s 0.95s var(--ease-out) both;
  }
  @keyframes close-in {
    from {
      opacity: 0;
      transform: var(--from);
    }
  }
  @keyframes draw {
    from {
      stroke-dashoffset: 1;
      opacity: 0;
    }
    8% {
      opacity: 1;
    }
  }
  @keyframes pop {
    from {
      opacity: 0;
      transform: scale(0.2);
    }
  }
</style>
