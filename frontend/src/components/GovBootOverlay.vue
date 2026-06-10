<template>
  <transition name="boot-fade">
    <div v-if="visible" class="boot-overlay" aria-hidden="true">
      <div class="form-head">DEPARTMENT OF SOUND — REQUEST INTAKE</div>
      <pre class="boot-log">{{ shown }}</pre>
      <div v-if="granted" class="stamp">REQUEST APPROVED</div>
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
  "> Submitting Form 27B/6...",
  "> Validating credentials [PENDING]",
  "> Forwarding to Department of Sound...",
  "> Queue position: 4,712",
  "> Please remain seated. Do not refresh.",
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

  // Deliberately sluggish — bureaucracy takes its time.
  let delay = 0;
  LINES.forEach((line) => {
    delay += 480;
    timers.push(
      setTimeout(() => {
        shown.value += (shown.value ? "\n" : "") + line;
      }, delay),
    );
  });
  timers.push(setTimeout(() => (granted.value = true), delay + 500));
  timers.push(setTimeout(() => (visible.value = false), delay + 2200));
}

watch(
  () => theme.skin,
  (s, prev) => {
    if (s === "government" && prev !== "government") runBoot();
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
  gap: 1.25rem;
  background: rgba(216, 201, 163, 0.97);
  pointer-events: none;
}
.form-head {
  font-family: "Georgia", serif;
  font-weight: 700;
  font-size: 0.9rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #7a1f1f;
  border-bottom: 2px double #111;
  padding-bottom: 0.4rem;
}
.boot-log {
  color: #1a1a1a;
  font-family: "Georgia", serif;
  font-size: 1rem;
  line-height: 1.7;
  background: transparent;
  margin: 0;
  min-width: 24rem;
}
.stamp {
  color: #a01818;
  font-family: "Georgia", serif;
  font-weight: 700;
  font-size: 2.4rem;
  letter-spacing: 0.18rem;
  text-transform: uppercase;
  border: 4px solid #a01818;
  padding: 0.3rem 1rem;
  transform: rotate(-8deg);
  opacity: 0.85;
  animation: stamp-slam 0.4s ease-out;
}
@keyframes stamp-slam {
  0% {
    opacity: 0;
    transform: rotate(-8deg) scale(2.4);
  }
  70% {
    opacity: 0.85;
    transform: rotate(-8deg) scale(0.92);
  }
  100% {
    opacity: 0.85;
    transform: rotate(-8deg) scale(1);
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
