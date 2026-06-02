<template>
  <div class="stats-view">
    <div class="stats-overview" v-if="stats.tabOverview">
      <div class="overview-card">
        <span class="overview-label">Sounds</span>
        <span class="overview-value">{{ stats.tabOverview.total_sounds }}</span>
      </div>
      <div class="overview-card">
        <span class="overview-label">Users</span>
        <span class="overview-value">{{ stats.tabOverview.total_users }}</span>
      </div>
      <div class="overview-card">
        <span class="overview-label">Total plays</span>
        <span class="overview-value">{{ stats.tabOverview.total_plays }}</span>
      </div>
      <div class="overview-card overview-card--mini">
        <span class="overview-label">Today</span>
        <span class="overview-value">{{ stats.tabOverview.plays_day }}</span>
      </div>
      <div class="overview-card overview-card--mini">
        <span class="overview-label">This week</span>
        <span class="overview-value">{{ stats.tabOverview.plays_week }}</span>
      </div>
      <div class="overview-card overview-card--mini">
        <span class="overview-label">This month</span>
        <span class="overview-value">{{ stats.tabOverview.plays_month }}</span>
      </div>
    </div>

    <div class="window-selector mb-4">
      <div class="buttons has-addons">
        <b-button
          v-for="w in windows"
          :key="w.value"
          :type="stats.tabWindow === w.value ? 'is-primary' : ''"
          @click="stats.setTabWindow(w.value)"
        >
          {{ w.label }}
        </b-button>
      </div>
      <b-button
        icon-left="rotate"
        :loading="stats.tabLoading"
        @click="stats.refreshTab()"
      >
        Refresh
      </b-button>
    </div>

    <div class="stats-grid">
      <section class="history-panel">
        <h2 class="title is-5">Top sounds</h2>
        <ul v-if="stats.tabSounds.length" class="history-list">
          <li v-for="s in stats.tabSounds" :key="s.sound_id">
            <strong class="stat-name">{{ s.display_name }}</strong>
            <span v-if="s.category_name" class="tag is-info is-light is-small stat-tag">
              {{ s.category_name }}
            </span>
            <span class="stat-count has-text-grey is-size-7">{{ s.play_count }} plays</span>
          </li>
        </ul>
        <p v-else class="has-text-grey">No plays yet.</p>
      </section>

      <section class="history-panel">
        <h2 class="title is-5">Most active users</h2>
        <ul v-if="stats.tabUsers.length" class="history-list">
          <li v-for="u in stats.tabUsers" :key="u.user_id">
            <strong class="stat-name">{{ u.username }}</strong>
            <span class="stat-count has-text-grey is-size-7">{{ u.play_count }} plays</span>
          </li>
        </ul>
        <p v-else class="has-text-grey">No users yet.</p>
      </section>

      <section class="history-panel">
        <h2 class="title is-5">Plays per category</h2>
        <ul v-if="stats.tabCategories.length" class="history-list">
          <li v-for="(c, i) in stats.tabCategories" :key="c.category_id ?? `unc-${i}`">
            <strong class="stat-name">
              {{ c.category_name ?? "Uncategorized" }}
            </strong>
            <span class="stat-count has-text-grey is-size-7">{{ c.play_count }} plays</span>
          </li>
        </ul>
        <p v-else class="has-text-grey">No categories yet.</p>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from "vue";
import { useStatsStore, type StatsWindow } from "@/stores/stats";

const stats = useStatsStore();

const windows: { value: StatsWindow; label: string }[] = [
  { value: "day", label: "Day" },
  { value: "week", label: "Week" },
  { value: "month", label: "Month" },
  { value: "all", label: "All time" },
];

onMounted(() => {
  void stats.refreshTab();
});
</script>

<style scoped>
.stats-view {
  background: var(--bulma-scheme-main-bis, white);
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}
.stats-overview {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 0.75rem;
  margin-bottom: 1.5rem;
}
.overview-card {
  background: var(--bulma-scheme-main-ter, rgba(0, 0, 0, 0.04));
  border-radius: 6px;
  padding: 0.75rem 1rem;
  display: flex;
  flex-direction: column;
}
.overview-label {
  font-size: 0.75rem;
  color: var(--bulma-text-weak, #777);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.overview-value {
  font-size: 1.5rem;
  font-weight: 600;
}
.overview-card--mini .overview-value {
  font-size: 1.15rem;
}
.window-selector {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}
.window-selector .buttons {
  margin-bottom: 0;
}
.stats-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1rem;
}
@media (min-width: 900px) {
  .stats-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}
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
.stat-tag {
  flex: 0 0 auto;
}
.stat-count {
  flex: 0 0 auto;
  white-space: nowrap;
  margin-left: auto;
}
</style>
