<template>
  <transition name="ban-lock-fade">
    <div
      v-if="ban.banned"
      class="ban-lock"
      role="alertdialog"
      aria-modal="true"
      aria-label="You are banned"
    >
      <div class="ban-lock__card">
        <i class="fas fa-ban ban-lock__icon" aria-hidden="true" />
        <h2 class="ban-lock__title">You are banned</h2>
        <p class="ban-lock__sub">Playing and voting are disabled.</p>
        <p v-if="ban.by" class="ban-lock__meta">by {{ ban.by }}</p>
        <p v-if="remaining" class="ban-lock__countdown">{{ remaining }} remaining</p>
        <p v-else-if="ban.expiresAt" class="ban-lock__countdown">expiring…</p>
        <p v-else class="ban-lock__countdown ban-lock__countdown--perm">permanent</p>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from "vue";
import { useBanStore } from "@/stores/ban";

const ban = useBanStore();
const now = ref(Date.now());
let ticker: number | null = null;

const remaining = computed(() => {
  if (!ban.expiresAt) return "";
  const ms = new Date(ban.expiresAt).getTime() - now.value;
  if (ms <= 0) return "";
  const totalSec = Math.ceil(ms / 1000);
  const min = Math.floor(totalSec / 60);
  const sec = totalSec % 60;
  if (min >= 60) {
    const h = Math.floor(min / 60);
    return `${h}h ${min % 60}m`;
  }
  if (min > 0) return `${min}m ${sec}s`;
  return `${sec}s`;
});

// Tick only while the lock is visible.
watch(
  () => ban.banned,
  (locked) => {
    if (locked && ticker === null) {
      ticker = window.setInterval(() => (now.value = Date.now()), 1000);
    } else if (!locked && ticker !== null) {
      window.clearInterval(ticker);
      ticker = null;
    }
  },
  { immediate: true },
);

onBeforeUnmount(() => {
  if (ticker !== null) window.clearInterval(ticker);
});
</script>

<style scoped>
.ban-lock {
  position: fixed;
  inset: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  /* Frosted glass: blur + dim the app behind, readable-but-locked. */
  background: rgba(0, 0, 0, 0.35);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
}
.ban-lock__card {
  text-align: center;
  max-width: 420px;
  padding: 2rem 2.25rem;
  border-radius: 14px;
  background: var(--bulma-scheme-main, #fff);
  border: 1px solid var(--bulma-border-weak, rgba(128, 128, 128, 0.25));
  box-shadow: 0 12px 48px rgba(0, 0, 0, 0.4);
}
.ban-lock__icon {
  font-size: 2.5rem;
  color: #d14;
  margin-bottom: 0.75rem;
}
.ban-lock__title {
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0 0 0.35rem;
}
.ban-lock__sub {
  color: var(--bulma-text-weak, #777);
  margin: 0 0 0.25rem;
}
.ban-lock__meta {
  font-size: 0.85rem;
  color: var(--bulma-text-weak, #999);
  margin: 0 0 0.5rem;
}
.ban-lock__countdown {
  font-size: 1.1rem;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  margin: 0.5rem 0 0;
}
.ban-lock__countdown--perm {
  color: #d14;
}
.ban-lock-fade-enter-active,
.ban-lock-fade-leave-active {
  transition: opacity 0.25s;
}
.ban-lock-fade-enter-from,
.ban-lock-fade-leave-to {
  opacity: 0;
}
</style>
