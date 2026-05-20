<template>
  <aside class="history-panel">
    <h2 class="title is-5">Most active users</h2>
    <ul v-if="stats.users.length" class="history-list">
      <li v-for="u in stats.users" :key="u.username">
        <strong class="stat-name">{{ u.username }}</strong>
        <span class="stat-count has-text-grey is-size-7">{{ u.play_count }} plays</span>
      </li>
    </ul>
    <p v-else class="has-text-grey">No plays yet.</p>
  </aside>
</template>

<script setup lang="ts">
import { useStatsStore } from "@/stores/stats";

const stats = useStatsStore();
</script>

<style scoped>
.history-panel {
  background: var(--bulma-scheme-main-bis, #fafafa);
  border-radius: 6px;
  padding: 1rem;
}
.history-list {
  list-style: none;
  margin: 0;
  padding: 0;
}
.history-list li {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.25rem 0;
  border-bottom: 1px solid #eee;
}
.history-list li:last-child {
  border-bottom: none;
}
.stat-name {
  flex: 1 1 auto;
  min-width: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.stat-count {
  flex: 0 0 auto;
  white-space: nowrap;
  margin-left: auto;
}
</style>
