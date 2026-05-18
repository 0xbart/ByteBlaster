<template>
  <aside class="history-panel">
    <h2 class="title is-5">Most played</h2>
    <div class="scroll-area">
      <ul v-if="stats.allTime.length" class="history-list">
        <li v-for="s in stats.allTime" :key="s.sound_id">
          <strong>{{ s.display_name }}</strong>
          <span v-if="s.category_name" class="tag is-info is-light is-small ml-2">
            {{ s.category_name }}
          </span>
          <span class="has-text-grey is-size-7"> · {{ s.play_count }} plays</span>
        </li>
      </ul>
      <p v-else class="has-text-grey">No plays yet.</p>
    </div>
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
