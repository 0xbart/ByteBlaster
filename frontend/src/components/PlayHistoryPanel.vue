<template>
  <aside class="history-panel">
    <h2 class="title is-5">Recently played</h2>
    <div class="scroll-area">
      <ul v-if="history.plays.length" class="history-list">
        <li v-for="(p, i) in history.plays" :key="`${p.id}-${i}`">
          <strong>{{ p.played_by_username }}</strong>
          played <em>{{ p.sound_display_name }}</em>
          <span class="has-text-grey is-size-7"> · {{ relativeTime(p.played_at) }}</span>
        </li>
      </ul>
      <p v-else class="has-text-grey">No plays yet.</p>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { onMounted } from "vue";
import { useHistoryStore } from "@/stores/history";

const history = useHistoryStore();

onMounted(() => {
  void history.refresh();
});

function relativeTime(iso: string): string {
  const t = new Date(iso).getTime();
  const s = Math.max(0, Math.floor((Date.now() - t) / 1000));
  if (s < 60) return `${s}s ago`;
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  if (s < 86400) return `${Math.floor(s / 3600)}h ago`;
  return new Date(iso).toLocaleString();
}
</script>

<style scoped>
.history-panel {
  background: var(--bulma-scheme-main-bis, #fafafa);
  border-radius: 6px;
  padding: 1rem;
}
.scroll-area {
  max-height: 500px;
  overflow-y: auto;
}
.history-list {
  list-style: none;
  margin: 0;
  padding: 0;
}
.history-list li {
  padding: 0.25rem 0;
  border-bottom: 1px solid #eee;
}
.history-list li:last-child {
  border-bottom: none;
}
</style>
