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
          <a
            v-if="isMutemaster || isSuperadmin"
            class="gavel-inline ml-3"
            :class="globalMute.active ? 'has-text-danger' : 'has-text-white'"
            :title="globalMute.active ? 'Lift global mute' : 'Mute everyone'"
            @click="onGavelToggle"
          >
            <b-icon icon="gavel" pack="fas" size="is-small" />
          </a>
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
      Click to stop playing sound
    </div>
    <div v-if="soundsStore.rateLimited" class="audio-rate-banner">
      <b-icon icon="bell-slash" pack="fas" size="is-small" class="mr-2" />
      {{ soundsStore.rateLimited }}
    </div>
    <div v-if="globalMute.active" class="audio-global-mute-banner">
      <b-icon icon="gavel" pack="fas" size="is-small" class="mr-2" />
      Sounds globally muted{{ globalMute.by ? ` by ${globalMute.by}` : "" }}
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
import { onMounted, ref, watch } from "vue";
import { storeToRefs } from "pinia";

import ClaimUsernameDialog from "./components/ClaimUsernameDialog.vue";
import SoundBoard from "./components/SoundBoard.vue";
import PlayHistoryPanel from "./components/PlayHistoryPanel.vue";
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

function onGavelToggle(): void {
  void globalMute.setActive(!globalMute.active);
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
.gavel-inline {
  cursor: pointer;
  display: inline-flex;
  align-items: center;
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
