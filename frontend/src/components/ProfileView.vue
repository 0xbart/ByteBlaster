<template>
  <div class="profile-view">
    <h2 class="title is-4">{{ me?.username ?? "Profile" }}</h2>
    <p class="has-text-grey mb-4">
      <span v-if="isSuperadmin" class="tag is-warning is-light mr-2">superadmin</span>
      <span v-else-if="isAdmin" class="tag is-success mr-2">admin</span>
      <span v-if="stats">Member since {{ formatDate(stats.member_since) }}</span>
    </p>

    <!-- Personal stats -->
    <div v-if="stats" class="stats-overview mb-5">
      <div class="overview-card">
        <span class="overview-label">My plays</span>
        <span class="overview-value">{{ stats.total_plays }}</span>
      </div>
      <div class="overview-card">
        <span class="overview-label">Favorites</span>
        <span class="overview-value">{{ stats.favorites_count }}</span>
      </div>
      <div class="overview-card">
        <span class="overview-label">Uploads</span>
        <span class="overview-value">{{ stats.sounds_uploaded }}</span>
      </div>
      <div class="overview-card overview-card--mini">
        <span class="overview-label">Today</span>
        <span class="overview-value">{{ stats.plays_day }}</span>
      </div>
      <div class="overview-card overview-card--mini">
        <span class="overview-label">This week</span>
        <span class="overview-value">{{ stats.plays_week }}</span>
      </div>
      <div class="overview-card overview-card--mini">
        <span class="overview-label">This month</span>
        <span class="overview-value">{{ stats.plays_month }}</span>
      </div>
    </div>
    <p v-else-if="loading" class="has-text-grey">Loading stats…</p>

    <!-- Top sounds -->
    <div v-if="stats && stats.top_sounds.length" class="box mb-5">
      <h3 class="title is-6">Your most-played sounds</h3>
      <ol class="top-list">
        <li v-for="s in stats.top_sounds" :key="s.sound_id">
          <span class="top-name">{{ s.display_name }}</span>
          <span v-if="s.category_name" class="tag is-light ml-2">{{ s.category_name }}</span>
          <span class="top-count">{{ s.play_count }}×</span>
        </li>
      </ol>
    </div>

    <!-- Skin selector -->
    <div class="box">
      <h3 class="title is-6">Theme</h3>
      <div class="skin-grid">
        <button
          v-for="opt in skins"
          :key="opt.value"
          class="skin-card"
          :class="[opt.value, { 'is-active': theme.skin === opt.value }]"
          @click="pick(opt.value)"
        >
          <span class="skin-name">{{ opt.label }}</span>
          <span class="skin-desc">{{ opt.desc }}</span>
        </button>
      </div>
      <p class="has-text-grey is-size-7 mt-2">
        Saved locally. Light/dark toggle (top bar) still applies under Default.
      </p>
    </div>

    <!-- Quick hotkeys -->
    <div class="box">
      <h3 class="title is-6">Quick hotkeys</h3>
      <p class="has-text-grey is-size-7 mb-3">
        Bind a sound to a number key (1-0). Press the key anywhere to play it.
        Saved locally. Tip: press <strong>f</strong> then click a sound to bind it fast.
      </p>
      <div class="hotkey-rows">
        <div v-for="d in DIGITS" :key="d" class="hotkey-row">
          <span class="hotkey-key">{{ d }}</span>
          <b-autocomplete
            v-model="queries[d]"
            class="hotkey-select"
            :data="filtered(d)"
            field="display_name"
            placeholder="Search sound…"
            size="is-small"
            clearable
            open-on-focus
            @select="(opt: SoundOut | null) => onSelect(d, opt)"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { storeToRefs } from "pinia";
import { api } from "@/api";
import type { MeStatsOut, SoundOut } from "@/api";
import { useUserStore } from "@/stores/user";
import { useThemeStore, type Skin } from "@/stores/theme";
import { useSkinSfx } from "@/composables/useSkinSfx";
import { useHotkeysStore, DIGITS } from "@/stores/hotkeys";
import { useSoundsStore } from "@/stores/sounds";

const userStore = useUserStore();
const { me, isAdmin, isSuperadmin } = storeToRefs(userStore);
const theme = useThemeStore();
const sfx = useSkinSfx();
const hotkeys = useHotkeysStore();
const sounds = useSoundsStore();

// Per-digit autocomplete query text. Seeded from existing bindings once sounds load.
const queries = reactive<Record<string, string>>({});

function filtered(digit: string): SoundOut[] {
  const q = (queries[digit] ?? "").trim().toLowerCase();
  const list = sounds.sortedByName;
  if (!q) return list;
  return list.filter((s) => s.display_name.toLowerCase().includes(q));
}

function onSelect(digit: string, opt: SoundOut | null): void {
  if (opt == null) hotkeys.clearSlot(digit);
  else {
    hotkeys.setSlot(digit, opt.id);
    queries[digit] = opt.display_name;
  }
}

function seedQueries(): void {
  for (const d of DIGITS) {
    const id = hotkeys.getSlot(d);
    queries[d] = id == null ? "" : sounds.sounds.find((s) => s.id === id)?.display_name ?? "";
  }
}

const stats = ref<MeStatsOut | null>(null);
const loading = ref(false);

const skins: { value: Skin; label: string; desc: string }[] = [
  { value: "default", label: "Default", desc: "Clean light / dark" },
  { value: "cyber", label: "Cyber", desc: "Matrix hacker mode" },
  { value: "pink", label: "Pink", desc: "Bubblegum dream" },
  { value: "money", label: "Money", desc: "Cash mode — make it rain" },
  { value: "government", label: "Government", desc: "Bureaucracy / classified" },
];

function pick(s: Skin): void {
  theme.setSkin(s);
  if (s === "money") sfx.cashRegister();
  else if (s === "government") sfx.stamp();
  else sfx.glitch();
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString();
}

onMounted(async () => {
  loading.value = true;
  const { data } = await api.GET("/api/me/stats");
  if (data) stats.value = data;
  loading.value = false;
  // Need the sound list to populate the hotkey autocompletes.
  if (!sounds.sounds.length) await sounds.refresh();
  seedQueries();
});
</script>

<style scoped>
.profile-view {
  background: var(--bulma-scheme-main-bis, white);
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}
.stats-overview {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}
.overview-card {
  display: flex;
  flex-direction: column;
  min-width: 7rem;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  background: var(--bulma-scheme-main-ter, rgba(0, 0, 0, 0.05));
}
.overview-card--mini {
  min-width: 5.5rem;
}
.overview-label {
  font-size: 0.75rem;
  opacity: 0.7;
}
.overview-value {
  font-size: 1.5rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}
.top-list {
  margin: 0;
  padding-left: 1.25rem;
}
.top-list li {
  display: flex;
  align-items: center;
  padding: 0.2rem 0;
}
.top-name {
  font-weight: 600;
}
.top-count {
  margin-left: auto;
  font-variant-numeric: tabular-nums;
  opacity: 0.8;
}
.skin-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(9rem, 1fr));
  gap: 0.75rem;
}
.skin-card {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  padding: 1rem;
  border-radius: 10px;
  border: 2px solid transparent;
  cursor: pointer;
  text-align: left;
  color: #fff;
}
.skin-card.is-active {
  border-color: #fff;
  box-shadow: 0 0 0 2px rgba(0, 0, 0, 0.25);
}
.skin-card.default {
  background: linear-gradient(135deg, #4a4a4a, #8a8a8a);
}
.skin-card.cyber {
  background: linear-gradient(135deg, #001a08, #00ff66);
  color: #001a08;
  font-family: "Courier New", monospace;
}
.skin-card.pink {
  background: linear-gradient(135deg, #ff5fa2, #c86bff);
}
.skin-card.money {
  background: linear-gradient(135deg, #0b3d2e, #ffd700);
  color: #08301f;
  font-family: "Georgia", serif;
}
.skin-card.government {
  background: linear-gradient(135deg, #d8c9a3, #1a1a1a);
  color: #f0e8d2;
  font-family: "Georgia", serif;
}
.hotkey-rows {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(15rem, 1fr));
  gap: 0.5rem;
}
.hotkey-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.hotkey-key {
  flex: 0 0 1.8rem;
  height: 1.8rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  border-radius: 6px;
  background: var(--bulma-scheme-main-ter, rgba(0, 0, 0, 0.08));
}
.hotkey-select {
  flex: 1 1 auto;
}
.hotkey-select select {
  width: 100%;
}
.skin-name {
  font-weight: 700;
  font-size: 1.1rem;
}
.skin-desc {
  font-size: 0.8rem;
  opacity: 0.85;
}
</style>
