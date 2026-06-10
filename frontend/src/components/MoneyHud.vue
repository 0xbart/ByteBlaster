<template>
  <div class="money-hud" aria-hidden="true">
    <span class="money-hud__label">Bank balance</span>
    <span class="money-hud__value">${{ formatted }}</span>
    <span class="money-hud__delta">▲ +${{ lastGain.toLocaleString("en-US") }}</span>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";

// Random starting fortune (8 digits) that keeps ticking up while the money skin
// is active. Pure cosmetic theatre — not persisted or sent anywhere.
const balance = ref(10_000_000 + Math.floor(Math.random() * 89_999_999));
const lastGain = ref(0);

const formatted = computed(() => balance.value.toLocaleString("en-US"));

let timer: number | null = null;

onMounted(() => {
  timer = window.setInterval(() => {
    lastGain.value = 100 + Math.floor(Math.random() * 9900);
    balance.value += lastGain.value;
  }, 800);
});

onBeforeUnmount(() => {
  if (timer !== null) window.clearInterval(timer);
});
</script>

<style scoped>
.money-hud {
  position: fixed;
  top: 4rem;
  right: 1rem;
  z-index: 9997;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.1rem;
  padding: 0.5rem 0.9rem;
  background: rgba(8, 48, 31, 0.92);
  border: 1px solid #ffd700;
  border-radius: 6px;
  box-shadow: 0 0 16px rgba(255, 215, 0, 0.35);
  font-family: "Georgia", serif;
  pointer-events: none;
  user-select: none;
}
.money-hud__label {
  font-size: 0.65rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #c9b873;
}
.money-hud__value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #ffd700;
  text-shadow: 0 0 10px rgba(255, 215, 0, 0.6);
  font-variant-numeric: tabular-nums;
}
.money-hud__delta {
  font-size: 0.75rem;
  color: #4ade80;
  font-variant-numeric: tabular-nums;
}
</style>
