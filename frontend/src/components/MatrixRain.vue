<template>
  <canvas ref="canvasEl" class="matrix-rain" aria-hidden="true" />
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from "vue";

const canvasEl = ref<HTMLCanvasElement | null>(null);
let raf = 0;
let ctx: CanvasRenderingContext2D | null = null;
let columns = 0;
let drops: number[] = [];
let lastFrame = 0;

const GLYPHS = "01ｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃ0101ﾄﾅﾆﾇﾈ01ｦｧｨｩ01";
const FONT_SIZE = 16;
const FRAME_MS = 55; // ~18fps, easy on the CPU

function resize(): void {
  const c = canvasEl.value;
  if (!c) return;
  c.width = window.innerWidth;
  c.height = window.innerHeight;
  columns = Math.floor(c.width / FONT_SIZE);
  drops = Array.from({ length: columns }, () =>
    Math.floor((Math.random() * c.height) / FONT_SIZE),
  );
}

function draw(ts: number): void {
  raf = requestAnimationFrame(draw);
  if (ts - lastFrame < FRAME_MS) return;
  lastFrame = ts;

  const c = canvasEl.value;
  if (!c || !ctx) return;

  // Translucent black fade → trailing tails.
  ctx.fillStyle = "rgba(0, 6, 0, 0.08)";
  ctx.fillRect(0, 0, c.width, c.height);

  ctx.font = `${FONT_SIZE}px monospace`;
  for (let i = 0; i < columns; i++) {
    const ch = GLYPHS.charAt(Math.floor(Math.random() * GLYPHS.length));
    const x = i * FONT_SIZE;
    const y = drops[i] * FONT_SIZE;
    // Bright leading char, dimmer trail.
    ctx.fillStyle = Math.random() > 0.975 ? "#d6ffe6" : "#00ff66";
    ctx.fillText(ch, x, y);
    if (y > c.height && Math.random() > 0.975) drops[i] = 0;
    drops[i]++;
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
.matrix-rain {
  position: fixed;
  inset: 0;
  width: 100vw;
  height: 100vh;
  z-index: 0;
  pointer-events: none;
  background: #000600;
}
</style>
