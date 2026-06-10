<template>
  <canvas ref="canvasEl" class="stamp-rain" aria-hidden="true" />
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from "vue";

// Government skin background: faded red rubber stamps tumbling down a manilla
// backdrop. Lower density + alpha than MatrixRain so the paper UI stays legible.
const canvasEl = ref<HTMLCanvasElement | null>(null);
let raf = 0;
let ctx: CanvasRenderingContext2D | null = null;
let lastFrame = 0;

const STAMPS = ["APPROVED", "DENIED", "TOP SECRET", "CLASSIFIED", "VOID", "FILE 27B/6"];
const FRAME_MS = 55;
const COUNT = 22;

type Stamp = { x: number; y: number; speed: number; rot: number; text: string };
let stamps: Stamp[] = [];

function make(c: HTMLCanvasElement, atTop = false): Stamp {
  return {
    x: Math.random() * c.width,
    y: atTop ? -40 : Math.random() * c.height,
    speed: 0.6 + Math.random() * 1.2,
    rot: (Math.random() - 0.5) * 0.9,
    text: STAMPS[Math.floor(Math.random() * STAMPS.length)],
  };
}

function resize(): void {
  const c = canvasEl.value;
  if (!c) return;
  c.width = window.innerWidth;
  c.height = window.innerHeight;
  stamps = Array.from({ length: COUNT }, () => make(c));
}

function draw(ts: number): void {
  raf = requestAnimationFrame(draw);
  if (ts - lastFrame < FRAME_MS) return;
  lastFrame = ts;

  const c = canvasEl.value;
  if (!c || !ctx) return;

  // Repaint the manilla backdrop each frame (no trails — stamps, not rain).
  ctx.fillStyle = "#d8c9a3";
  ctx.fillRect(0, 0, c.width, c.height);

  ctx.font = "bold 24px Georgia, serif";
  ctx.textAlign = "center";
  for (const s of stamps) {
    ctx.save();
    ctx.translate(s.x, s.y);
    ctx.rotate(s.rot);
    ctx.globalAlpha = 0.18;
    ctx.strokeStyle = "#a01818";
    ctx.fillStyle = "#a01818";
    ctx.lineWidth = 2;
    const w = ctx.measureText(s.text).width + 18;
    ctx.strokeRect(-w / 2, -20, w, 32);
    ctx.fillText(s.text, 0, 2);
    ctx.restore();

    s.y += s.speed;
    if (s.y > c.height + 40) Object.assign(s, make(c, true));
  }
}

onMounted(() => {
  const c = canvasEl.value;
  if (!c) return;
  ctx = c.getContext("2d");
  resize();
  window.addEventListener("resize", resize);
  raf = requestAnimationFrame(draw);
});

onBeforeUnmount(() => {
  cancelAnimationFrame(raf);
  window.removeEventListener("resize", resize);
});
</script>

<style scoped>
.stamp-rain {
  position: fixed;
  inset: 0;
  width: 100vw;
  height: 100vh;
  z-index: 0;
  pointer-events: none;
  background: #d8c9a3;
}
</style>
