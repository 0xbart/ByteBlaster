<template>
  <transition name="boot-fade">
    <div v-if="visible" class="boot-overlay" aria-hidden="true">
      <pre class="boot-log">{{ shown }}</pre>
      <div v-if="granted" class="balance">BANK BALANCE: ${{ balance }}</div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";
import { useThemeStore } from "@/stores/theme";

const theme = useThemeStore();

const visible = ref(false);
const shown = ref("");
const granted = ref(false);
const balance = ref("");

const LINES = [
  "> connecting to offshore account...",
  "> verifying liquidity [OK]",
  "> counting assets...",
  "> laundering... just kidding [OK]",
  "> loading money...",
];

let timers: ReturnType<typeof setTimeout>[] = [];

function clearTimers(): void {
  timers.forEach(clearTimeout);
  timers = [];
}

function runBoot(): void {
  clearTimers();
  shown.value = "";
  granted.value = false;
  balance.value = (10_000_000 + Math.floor(Math.random() * 89_999_999)).toLocaleString(
    "en-US",
  );
  visible.value = true;

  let delay = 0;
  LINES.forEach((line) => {
    delay += 240;
    timers.push(
      setTimeout(() => {
        shown.value += (shown.value ? "\n" : "") + line;
      }, delay),
    );
  });
  timers.push(setTimeout(() => (granted.value = true), delay + 250));
  timers.push(setTimeout(() => (visible.value = false), delay + 1900));
}

watch(
  () => theme.skin,
  (s, prev) => {
    if (s === "money" && prev !== "money") runBoot();
  },
);
</script>

<style scoped>
.boot-overlay {
  position: fixed;
  inset: 0;
  z-index: 10000;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1.5rem;
  background: rgba(6, 36, 24, 0.94);
  pointer-events: none;
}
.boot-log {
  color: #ffd700;
  font-family: "Georgia", serif;
  font-size: 1rem;
  line-height: 1.6;
  text-shadow: 0 0 6px rgba(255, 215, 0, 0.6);
  background: transparent;
  margin: 0;
  min-width: 22rem;
}
.balance {
  color: #fff7cc;
  font-family: "Georgia", serif;
  font-weight: 700;
  font-size: 2.2rem;
  letter-spacing: 0.08rem;
  text-shadow: 0 0 18px rgba(255, 215, 0, 0.9);
  animation: cash-pop 0.5s ease-out;
}
@keyframes cash-pop {
  0% {
    opacity: 0;
    transform: scale(0.6);
  }
  60% {
    transform: scale(1.15);
  }
  100% {
    opacity: 1;
    transform: scale(1);
  }
}
.boot-fade-enter-active,
.boot-fade-leave-active {
  transition: opacity 0.4s ease;
}
.boot-fade-enter-from,
.boot-fade-leave-to {
  opacity: 0;
}
</style>
