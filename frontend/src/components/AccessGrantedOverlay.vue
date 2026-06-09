<template>
  <transition name="boot-fade">
    <div v-if="visible" class="boot-overlay" aria-hidden="true">
      <pre class="boot-log">{{ shown }}</pre>
      <div v-if="granted" class="granted">ACCESS GRANTED</div>
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

const LINES = [
  "> initializing breach sequence...",
  "> bypassing firewall [OK]",
  "> injecting payload 0x4F2A...",
  "> decrypting mainframe...",
  "> root@byteblaster:~# access --grant",
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
  visible.value = true;

  let delay = 0;
  LINES.forEach((line) => {
    delay += 220;
    timers.push(
      setTimeout(() => {
        shown.value += (shown.value ? "\n" : "") + line;
      }, delay),
    );
  });
  timers.push(setTimeout(() => (granted.value = true), delay + 250));
  timers.push(setTimeout(() => (visible.value = false), delay + 1600));
}

// Fire only when transitioning INTO cyber.
watch(
  () => theme.skin,
  (s, prev) => {
    if (s === "cyber" && prev !== "cyber") runBoot();
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
  background: rgba(0, 4, 0, 0.92);
  pointer-events: none;
}
.boot-log {
  color: #00ff66;
  font-family: "Courier New", monospace;
  font-size: 1rem;
  line-height: 1.6;
  text-shadow: 0 0 6px rgba(0, 255, 102, 0.6);
  background: transparent;
  margin: 0;
  min-width: 22rem;
}
.granted {
  color: #d6ffe6;
  font-family: "Courier New", monospace;
  font-weight: 700;
  font-size: 2.6rem;
  letter-spacing: 0.3rem;
  text-shadow: 0 0 16px rgba(0, 255, 102, 0.9);
  animation: flicker 0.5s steps(2) 3;
}
@keyframes flicker {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.3;
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
