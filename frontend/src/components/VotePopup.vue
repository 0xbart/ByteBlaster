<template>
  <transition name="vote-pop">
    <div v-if="votes.popup" class="vote-popup" role="dialog" aria-label="Rate this sound">
      <div class="vote-popup__head">
        <span class="vote-popup__name" :title="votes.popup.name">
          <i class="fas fa-music mr-1" aria-hidden="true" />{{ votes.popup.name }}
        </span>
        <button class="vote-popup__close" aria-label="Dismiss" @click="votes.close()">
          <i class="fas fa-xmark" aria-hidden="true" />
        </button>
      </div>
      <div class="vote-popup__actions">
        <span class="vote-popup__label">rate it?</span>
        <button
          class="vote-btn"
          :class="{ 'is-up': votes.popup.myVote === 'up' }"
          title="Thumbs up (press U)"
          @click="votes.vote('up')"
        >
          👍<span v-if="tally && tally.up" class="vote-count">{{ tally.up }}</span>
        </button>
        <button
          class="vote-btn"
          :class="{ 'is-down': votes.popup.myVote === 'down' }"
          title="Thumbs down (press D)"
          @click="votes.vote('down')"
        >
          👎<span v-if="tally && tally.down" class="vote-count">{{ tally.down }}</span>
        </button>
      </div>
      <div class="vote-popup__bar">
        <div class="vote-popup__bar-fill" :style="{ width: `${pct}%` }" />
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from "vue";
import { useVotesStore } from "@/stores/votes";

const votes = useVotesStore();
const now = ref(Date.now());
let ticker: number | null = null;

const POPUP_MS = 20_000;

const pct = computed(() => {
  if (!votes.popup) return 0;
  const remaining = votes.popup.expiresAt - now.value;
  return Math.max(0, Math.min(100, (remaining / POPUP_MS) * 100));
});

const tally = computed(() =>
  votes.popup ? votes.tally(votes.popup.playId) : null,
);

watch(
  () => votes.popup !== null,
  (open) => {
    if (open && ticker === null) {
      ticker = window.setInterval(() => (now.value = Date.now()), 250);
    } else if (!open && ticker !== null) {
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
.vote-popup {
  position: fixed;
  right: 1rem;
  bottom: 1rem;
  z-index: 28;
  width: 230px;
  padding: 0.6rem 0.75rem 0.5rem;
  border-radius: 10px;
  background: var(--bulma-scheme-main, #fff);
  border: 1px solid var(--bulma-border-weak, rgba(128, 128, 128, 0.25));
  box-shadow: 0 4px 18px rgba(0, 0, 0, 0.18);
  opacity: 0.97;
}
.vote-popup__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  margin-bottom: 0.4rem;
}
.vote-popup__name {
  font-size: 0.85rem;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.vote-popup__close {
  border: none;
  background: none;
  cursor: pointer;
  color: var(--bulma-text-weak, #999);
  font-size: 0.8rem;
  line-height: 1;
  padding: 0.1rem;
}
.vote-popup__actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.vote-popup__label {
  font-size: 0.78rem;
  color: var(--bulma-text-weak, #888);
  margin-right: auto;
}
.vote-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.2rem;
  border: 1px solid transparent;
  border-radius: 8px;
  background: var(--bulma-scheme-main-ter, #f1f1f3);
  cursor: pointer;
  font-size: 1rem;
  line-height: 1;
  padding: 0.25rem 0.45rem;
  transition: background 0.12s, border-color 0.12s, transform 0.08s;
}
.vote-btn:hover {
  transform: translateY(-1px);
}
.vote-btn.is-up {
  border-color: #2e9e5b;
  background: rgba(46, 158, 91, 0.14);
}
.vote-btn.is-down {
  border-color: #d14;
  background: rgba(221, 17, 68, 0.12);
}
.vote-count {
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--bulma-text-weak, #777);
}
.vote-popup__bar {
  margin-top: 0.5rem;
  height: 3px;
  border-radius: 3px;
  background: var(--bulma-scheme-main-ter, rgba(128, 128, 128, 0.18));
  overflow: hidden;
}
.vote-popup__bar-fill {
  height: 100%;
  background: var(--bulma-link, #4a7bd0);
  transition: width 0.25s linear;
}
.vote-pop-enter-active,
.vote-pop-leave-active {
  transition: opacity 0.2s, transform 0.2s;
}
.vote-pop-enter-from,
.vote-pop-leave-to {
  opacity: 0;
  transform: translateY(8px);
}
</style>
