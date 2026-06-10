<template>
  <canvas ref="canvasEl" class="money-rain" aria-hidden="true" />
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from "vue";

const canvasEl = ref<HTMLCanvasElement | null>(null);
let raf = 0;
let ctx: CanvasRenderingContext2D | null = null;
let lastFrame = 0;

// Falling money symbols. Emoji render per-OS; the plain $/€/¢ are the reliable
// fallback and keep the column readable everywhere.
const GLYPHS = ["$", "€", "£", "¢", "💵", "🪙", "💰"];
const FONT_SIZE = 22;
const COL_W = 34;
const FRAME_MS = 55; // ~18fps, easy on the CPU

type Bill = { x: number; y: number; speed: number; ch: string };
let bills: Bill[] = [];

function rnd(arr: string[]): string {
  return arr[Math.floor(Math.random() * arr.length)];
}

function resize(): void {
  const c = canvasEl.value;
  if (!c) return;
  c.width = window.innerWidth;
  c.height = window.innerHeight;
  const cols = Math.floor(c.width / COL_W);
  bills = Array.from({ length: cols }, (_, i) => ({
    x: i * COL_W + COL_W / 2,
    y: Math.random() * c.height,
    speed: 1.5 + Math.random() * 2.5,
    ch: rnd(GLYPHS),
  }));
}

function draw(ts: number): void {
  raf = requestAnimationFrame(draw);
  if (ts - lastFrame < FRAME_MS) return;
  lastFrame = ts;

  const c = canvasEl.value;
  if (!c || !ctx) return;

  // Translucent dark-green fade → soft trails.
  ctx.fillStyle = "rgba(8, 48, 31, 0.18)";
  ctx.fillRect(0, 0, c.width, c.height);

  ctx.font = `${FONT_SIZE}px Georgia, serif`;
  ctx.textAlign = "center";
  for (const b of bills) {
    ctx.fillStyle = Math.random() > 0.9 ? "#fff7cc" : "#ffd700";
    ctx.fillText(b.ch, b.x, b.y);
    b.y += b.speed;
    if (b.y > c.height + FONT_SIZE) {
      b.y = -FONT_SIZE;
      b.speed = 1.5 + Math.random() * 2.5;
      b.ch = rnd(GLYPHS);
    }
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
.money-rain {
  position: fixed;
  inset: 0;
  width: 100vw;
  height: 100vh;
  z-index: 0;
  pointer-events: none;
  background: #08301f;
}
</style>
