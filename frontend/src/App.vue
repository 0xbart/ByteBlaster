<template>
  <div class="app-shell">
    <nav class="navbar is-dark">
      <div class="navbar-brand">
        <a
          class="navbar-item brand-link"
          :class="{ 'is-active': view === 'board' }"
          @click="view = 'board'"
        >
          <b-icon icon="drum" pack="fas" size="is-medium" class="has-text-white mr-1" />
          <span class="title is-5 has-text-white mb-0">ByteBlaster</span>
        </a>
        <a
          class="navbar-item has-text-white"
          :class="{ 'is-active': view === 'explore' }"
          @click="view = 'explore'"
        >
          Explore
        </a>
        <a
          class="navbar-item has-text-white"
          :class="{ 'is-active': view === 'stats' }"
          @click="view = 'stats'"
        >
          Stats
        </a>
        <a
          v-if="isAdmin"
          class="navbar-item has-text-white"
          :class="{ 'is-active': view === 'admin' }"
          @click="view = 'admin'"
        >
          Admin
        </a>
      </div>
      <div class="navbar-end">
        <div v-if="me" class="navbar-item has-text-white">
          <span class="mr-2">Signed in as</span>
          <strong class="has-text-white">{{ me.username }}</strong>
          <span v-if="isSuperadmin" class="tag is-warning is-light ml-2">superadmin</span>
          <span v-else-if="isAdmin" class="tag is-success ml-2">admin</span>
          <span v-if="isMutemaster || isSuperadmin" class="gavel-control ml-3">
            <a
              class="gavel-inline"
              :class="globalMute.active ? 'has-text-danger' : 'has-text-white'"
              :title="globalMute.active ? 'Lift global mute' : 'Mute everyone (hover for options)'"
              @click="onGavelClick"
            >
              <b-icon icon="gavel" pack="fas" size="is-small" />
            </a>
            <div v-if="!globalMute.active" class="gavel-popover">
              <span class="gavel-popover__title">Mute for…</span>
              <label
                v-for="opt in muteDurations"
                :key="opt.label"
                class="mute-radio"
              >
                <input
                  type="radio"
                  name="mute-duration"
                  :value="opt.minutes ?? 'inf'"
                  v-model="selectedMuteDuration"
                  @change="onSetMute(opt.minutes)"
                />
                <span>{{ opt.label }}</span>
              </label>
            </div>
          </span>
          <a
            class="tag ml-3 presence-tag"
            :class="wsConnected ? 'is-success' : 'is-warning'"
            :title="wsConnected ? 'Show who is connected' : 'Reconnecting…'"
            @click="onLiveClick"
          >
            {{ wsConnected ? `live · ${presence.count}` : "offline" }}
          </a>
        </div>
        <div class="navbar-item volume-control">
          <a
            class="volume-icon has-text-white"
            :title="audio.muted ? 'Unmute (restore volume)' : 'Mute sounds'"
            @click="audio.toggle"
          >
            <b-icon :icon="audio.volumeIcon" pack="fas" size="is-small" />
          </a>
          <div class="volume-popover">
            <input
              type="range"
              min="0"
              max="100"
              step="1"
              :value="audio.volume"
              class="volume-slider"
              :title="`Volume: ${audio.volume}%`"
              @input="onVolumeInput"
            />
            <span class="volume-value">{{ audio.volume }}%</span>
          </div>
        </div>
        <a
          class="navbar-item theme-toggle"
          :title="theme.isDark ? 'Switch to light mode' : 'Switch to dark mode'"
          @click="theme.toggle"
        >
          <b-icon
            :icon="theme.isDark ? 'sun' : 'moon'"
            pack="fas"
            size="is-small"
          />
        </a>
      </div>
    </nav>

    <div v-if="!audioUnlocked" class="audio-locked-banner">
      <b-icon icon="volume-mute" pack="fas" size="is-small" class="mr-2" />
      Click anywhere to enable sounds from other users
    </div>
    <div
      v-else-if="audioPlaying"
      class="audio-playing-banner"
      role="button"
      @click="audioStop"
    >
      <b-icon icon="stop" pack="fas" size="is-small" class="mr-2" />
      Click to stop playing sound (or press M)
    </div>
    <div v-if="soundsStore.rateLimited" class="audio-rate-banner">
      <b-icon icon="bell-slash" pack="fas" size="is-small" class="mr-2" />
      {{ soundsStore.rateLimited }}
    </div>
    <div v-if="globalMute.active" class="audio-global-mute-banner">
      <b-icon icon="gavel" pack="fas" size="is-small" class="mr-2" />
      Sounds globally muted{{ globalMute.by ? ` by ${globalMute.by}` : "" }}
      <span v-if="muteCountdown" class="ml-2 mute-countdown">· {{ muteCountdown }}</span>
    </div>

    <main class="section">
      <div class="container">
        <div v-if="serverDown" class="server-down has-text-centered py-6">
          <b-icon icon="server" pack="fas" size="is-large" class="has-text-warning" />
          <h1 class="title is-3 mt-3">Backend not reachable</h1>
          <p class="has-text-grey">
            Cannot reach the ByteBlaster server. Check the connection or try again.
          </p>
          <b-button type="is-primary" icon-left="refresh" class="mt-4" @click="retryConnect">
            Retry
          </b-button>
        </div>
        <div v-else-if="!loaded" class="has-text-centered">
          <b-loading :is-full-page="false" :model-value="true" />
        </div>
        <ClaimUsernameDialog v-else-if="needsClaim" />
        <template v-else>
          <div v-show="view === 'board'" class="board-layout">
            <SoundBoard class="board" />
            <div class="sidebar">
              <SchedulerPanel />
              <PlayHistoryPanel />
              <MostPlayedPanel />
              <TrendingPanel />
              <ActiveUsersPanel />
            </div>
          </div>
          <ExploreView v-if="view === 'explore'" />
          <StatsView v-if="view === 'stats'" />
          <AdminPanel v-if="view === 'admin' && isAdmin" />
        </template>
      </div>
    </main>

    <PresenceDialog v-if="presenceOpen" @close="presenceOpen = false" />
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { api } from "@/api";
import { storeToRefs } from "pinia";

import ClaimUsernameDialog from "./components/ClaimUsernameDialog.vue";
import SoundBoard from "./components/SoundBoard.vue";
import PlayHistoryPanel from "./components/PlayHistoryPanel.vue";
import SchedulerPanel from "./components/SchedulerPanel.vue";
import MostPlayedPanel from "./components/MostPlayedPanel.vue";
import StatsView from "./components/StatsView.vue";
import ExploreView from "./components/ExploreView.vue";
import TrendingPanel from "./components/TrendingPanel.vue";
import ActiveUsersPanel from "./components/ActiveUsersPanel.vue";
import AdminPanel from "./components/AdminPanel.vue";
import PresenceDialog from "./components/PresenceDialog.vue";
import { useUserStore } from "./stores/user";
import { useCategoriesStore } from "./stores/categories";
import { useTagsStore } from "./stores/tags";
import { useStatsStore } from "./stores/stats";
import { useGlobalMuteStore } from "./stores/globalMute";
import { usePresenceStore } from "./stores/presence";
import { useThemeStore } from "./stores/theme";
import { useAudioStore } from "./stores/audio";
import { useSoundsStore } from "./stores/sounds";
import { useWebSocket } from "./composables/useWebSocket";
import { useAudioPlayer } from "./composables/useAudioPlayer";

const userStore = useUserStore();
const categoriesStore = useCategoriesStore();
const tagsStore = useTagsStore();
const statsStore = useStatsStore();
const globalMute = useGlobalMuteStore();
const presence = usePresenceStore();
const theme = useThemeStore();
const audio = useAudioStore();
const soundsStore = useSoundsStore();
const { me, loaded, needsClaim, isAdmin, isSuperadmin, isMutemaster, serverDown } = storeToRefs(userStore);

function retryConnect(): void {
  void userStore.fetchMe();
}

const view = ref<"board" | "stats" | "admin" | "explore">("board");
const presenceOpen = ref(false);

const { connected: wsConnected } = useWebSocket();
const { unlocked: audioUnlocked, playing: audioPlaying, stopAll: audioStop } = useAudioPlayer();

watch(
  () => audio.muted,
  (m) => {
    if (m) audioStop();
  },
);

function onVolumeInput(ev: Event): void {
  const target = ev.target as HTMLInputElement;
  audio.setVolume(Number(target.value));
}

const selectedMuteDuration = ref<number | "inf">(2);
const muteDurations: { label: string; minutes: number | null }[] = [
  { label: "1 min", minutes: 1 },
  { label: "2 min", minutes: 2 },
  { label: "5 min", minutes: 5 },
  { label: "10 min", minutes: 10 },
  { label: "30 min", minutes: 30 },
  { label: "60 min", minutes: 60 },
  { label: "∞", minutes: null },
];

const nowTick = ref(Date.now());
let muteTicker: number | null = null;

const muteCountdown = computed(() => {
  if (!globalMute.active || !globalMute.expiresAt) return "";
  const remaining = Math.max(0, new Date(globalMute.expiresAt).getTime() - nowTick.value);
  if (remaining <= 0) return "0s";
  const totalSec = Math.floor(remaining / 1000);
  const m = Math.floor(totalSec / 60);
  const s = totalSec % 60;
  return m > 0 ? `${m}m${s.toString().padStart(2, "0")}s left` : `${s}s left`;
});

watch(
  () => globalMute.active,
  (active) => {
    if (active && muteTicker === null) {
      muteTicker = window.setInterval(() => {
        nowTick.value = Date.now();
      }, 1000);
    } else if (!active && muteTicker !== null) {
      window.clearInterval(muteTicker);
      muteTicker = null;
    }
  },
);

onBeforeUnmount(() => {
  if (muteTicker !== null) window.clearInterval(muteTicker);
  window.removeEventListener("keydown", onGlobalKey);
});

function onGlobalKey(ev: KeyboardEvent): void {
  const k = ev.key.toLowerCase();
  if (k !== "m" && k !== "k") return;
  if (ev.ctrlKey || ev.metaKey || ev.altKey) return;
  const t = ev.target as HTMLElement | null;
  if (t) {
    const tag = t.tagName;
    if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || t.isContentEditable) return;
  }
  ev.preventDefault();
  if (k === "m") {
    audioStop();
  } else {
    audioStop();
    void api.POST("/api/stop-all", {});
  }
}

onMounted(() => {
  window.addEventListener("keydown", onGlobalKey);
});

function onGavelClick(): void {
  if (globalMute.active) {
    void globalMute.setActive(false);
  } else {
    void globalMute.setActive(true, 2);
  }
}
function onSetMute(minutes: number | null): void {
  void globalMute.setActive(true, minutes);
}

function onLiveClick(): void {
  if (wsConnected.value) presenceOpen.value = true;
}

onMounted(() => {
  void userStore.fetchMe();
});

// Only load categories + tags once the user is authenticated (otherwise 401 spam).
watch(
  () => userStore.isReady,
  (ready) => {
    if (ready) {
      void categoriesStore.refresh();
      void tagsStore.refresh();
      void statsStore.refresh();
      void globalMute.refresh();
    }
  },
  { immediate: true },
);
</script>

<style scoped>
.app-shell {
  position: relative;
  min-height: 100vh;
  /* Bulma's scheme-main flips automatically with [data-theme="dark"]. */
  background: var(--bulma-scheme-main, #f5f5f7);
}
.navbar-item.is-active {
  background-color: rgba(255, 255, 255, 0.1);
}
.brand-link {
  display: flex;
  align-items: center;
}
.presence-tag {
  cursor: pointer;
  user-select: none;
}
.gavel-control {
  position: relative;
  display: inline-flex;
  align-items: center;
}
.gavel-inline {
  cursor: pointer;
  display: inline-flex;
  align-items: center;
}
.gavel-popover {
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translate(-50%, 23px);
  background: hsl(0, 0%, 17%);
  border: 1px solid hsl(0, 0%, 28%);
  border-radius: 6px;
  padding: 0.6rem 0.6rem 0.5rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.35);
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.12s ease-in-out;
  z-index: 1200;
  min-width: 140px;
}
.gavel-popover::before {
  content: "";
  position: absolute;
  top: -23px;
  left: 0;
  right: 0;
  height: 23px;
}
.gavel-popover__title {
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: hsl(0, 0%, 70%);
  margin-bottom: 0.25rem;
}
.mute-radio {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.35rem 0.6rem;
  border-radius: 4px;
  cursor: pointer;
  color: hsl(0, 0%, 92%);
  font-size: 0.8rem;
  font-weight: 500;
  transition: background 0.1s ease-in-out;
  user-select: none;
}
.mute-radio:hover {
  background: hsl(0, 0%, 24%);
}
.mute-radio input[type="radio"] {
  appearance: none;
  -webkit-appearance: none;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 2px solid hsl(0, 0%, 55%);
  background: transparent;
  margin: 0;
  cursor: pointer;
  flex: 0 0 auto;
  position: relative;
}
.mute-radio input[type="radio"]:checked {
  border-color: hsl(204, 86%, 53%);
}
.mute-radio input[type="radio"]:checked::after {
  content: "";
  position: absolute;
  inset: 2px;
  border-radius: 50%;
  background: hsl(204, 86%, 53%);
}
.gavel-control:hover .gavel-popover,
.gavel-control:focus-within .gavel-popover {
  opacity: 1;
  pointer-events: auto;
}
.mute-countdown {
  font-variant-numeric: tabular-nums;
}
.theme-toggle {
  cursor: pointer;
}
.app-shell :deep(.navbar) {
  position: relative;
  z-index: 1500;
}
.volume-control {
  position: relative;
  display: flex;
  align-items: center;
}
.volume-icon {
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  color: #fff;
}
.volume-popover {
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translate(-50%, 4px);
  background: hsl(0, 0%, 17%);
  border: 1px solid hsl(0, 0%, 28%);
  border-radius: 6px;
  padding: 0.5rem 0;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.35);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.12s ease-in-out;
  z-index: 1100;
  white-space: nowrap;
  min-width: 56px;
}
.volume-control:hover .volume-popover,
.volume-control:focus-within .volume-popover {
  opacity: 1;
  pointer-events: auto;
}
.volume-slider {
  appearance: slider-vertical;
  -webkit-appearance: slider-vertical;
  writing-mode: vertical-lr;
  direction: rtl;
  width: 32px;
  height: 120px;
  margin: 0;
  padding: 0;
  accent-color: hsl(204, 86%, 53%);
  cursor: pointer;
}
.volume-value {
  display: inline-block;
  min-width: 40px;
  text-align: center;
  font-size: 0.75rem;
  color: hsl(0, 0%, 85%);
  font-weight: 600;
  margin: 0;
}
.board-layout {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1.5rem;
}
@media (min-width: 1024px) {
  .board-layout {
    grid-template-columns: 1fr 320px;
  }
}
.sidebar {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.audio-locked-banner,
.audio-playing-banner {
  position: absolute;
  top: 3.25rem;
  left: 0;
  right: 0;
  z-index: 1000;
  background: hsl(44, 100%, 50%);
  color: #1a1a1a;
  text-align: center;
  padding: 0.4rem 1rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
}
.audio-playing-banner {
  background: hsl(348, 80%, 55%);
  color: #fff;
  cursor: pointer;
  user-select: none;
}
.audio-rate-banner {
  position: absolute;
  top: 3.25rem;
  left: 0;
  right: 0;
  z-index: 1001;
  background: hsl(28, 95%, 50%);
  color: #1a1a1a;
  text-align: center;
  padding: 0.4rem 1rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
}
.audio-global-mute-banner {
  position: absolute;
  top: 3.25rem;
  left: 0;
  right: 0;
  z-index: 1100;
  background: hsl(348, 75%, 38%);
  color: #fff;
  text-align: center;
  padding: 0.4rem 1rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.25);
  user-select: none;
}
</style>
