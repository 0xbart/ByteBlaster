<template>
  <aside v-if="scheduler.items.length" class="history-panel scheduler-panel">
    <h2 class="title is-5">
      <b-icon icon="clock" pack="fas" size="is-small" class="mr-2" />
      Scheduled
      <span class="has-text-grey is-size-7 ml-2">
        {{ scheduler.items.length }} / 5
      </span>
    </h2>
    <ul class="scheduler-list">
      <li v-for="it in scheduler.sorted" :key="it.id" class="scheduler-row">
        <em class="scheduler-name">{{ it.displayName }}</em>
        <span class="scheduler-time">{{ formatRemaining(scheduler.remainingMs(it)) }}</span>
        <button
          class="button is-small is-danger is-light scheduler-cancel"
          title="Cancel"
          @click="scheduler.cancel(it.id)"
        >
          <i class="fas fa-xmark" aria-hidden="true" />
        </button>
      </li>
    </ul>
  </aside>
</template>

<script setup lang="ts">
import { useSchedulerStore } from "@/stores/scheduler";

const scheduler = useSchedulerStore();

function formatRemaining(ms: number): string {
  const total = Math.ceil(ms / 1000);
  const m = Math.floor(total / 60);
  const s = total % 60;
  return m > 0 ? `${m}m${s.toString().padStart(2, "0")}s` : `${s}s`;
}
</script>

<style scoped>
.history-panel {
  background: var(--bulma-scheme-main-bis, #fafafa);
  border-radius: 6px;
  padding: 1rem;
}
.scheduler-list {
  list-style: none;
  margin: 0;
  padding: 0;
}
.scheduler-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.25rem 0;
  border-bottom: 1px solid #eee;
}
.scheduler-row:last-child {
  border-bottom: none;
}
.scheduler-name {
  flex: 1 1 auto;
  min-width: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.scheduler-time {
  flex: 0 0 auto;
  font-variant-numeric: tabular-nums;
  font-weight: 600;
  white-space: nowrap;
}
.scheduler-cancel {
  flex: 0 0 auto;
  border-radius: 50%;
  padding: 0;
  width: 24px;
  height: 24px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
</style>
