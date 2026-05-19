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
            class="tag ml-3 presence-tag"
            :class="wsConnected ? 'is-success' : 'is-warning'"
            :title="wsConnected ? 'Show who is connected' : 'Reconnecting…'"
            @click="onLiveClick"
          >
            {{ wsConnected ? `live · ${presence.count}` : "offline" }}
          </a>
        </div>
        <a
          class="navbar-item theme-toggle"
          :title="audio.muted ? 'Unmute sounds' : 'Mute sounds'"
          @click="audio.toggle"
        >
          <b-icon
            :icon="audio.muted ? 'volume-mute' : 'volume-high'"
            pack="fas"
            size="is-small"
          />
        </a>
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

    <main class="section">
      <div class="container">
        <div v-if="!loaded" class="has-text-centered">
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
import TrendingPanel from "./components/TrendingPanel.vue";
import ActiveUsersPanel from "./components/ActiveUsersPanel.vue";
import AdminPanel from "./components/AdminPanel.vue";
import PresenceDialog from "./components/PresenceDialog.vue";
import { useUserStore } from "./stores/user";
import { useCategoriesStore } from "./stores/categories";
import { useTagsStore } from "./stores/tags";
import { useStatsStore } from "./stores/stats";
import { usePresenceStore } from "./stores/presence";
import { useThemeStore } from "./stores/theme";
import { useAudioStore } from "./stores/audio";
import { useWebSocket } from "./composables/useWebSocket";
import { useAudioPlayer } from "./composables/useAudioPlayer";

const userStore = useUserStore();
const categoriesStore = useCategoriesStore();
const tagsStore = useTagsStore();
const statsStore = useStatsStore();
const presence = usePresenceStore();
const theme = useThemeStore();
const audio = useAudioStore();
const { me, loaded, needsClaim, isAdmin, isSuperadmin } = storeToRefs(userStore);

const view = ref<"board" | "admin">("board");
const presenceOpen = ref(false);

const { connected: wsConnected } = useWebSocket();
const { unlocked: audioUnlocked, playing: audioPlaying, stopAll: audioStop } = useAudioPlayer();

watch(
  () => audio.muted,
  (m) => {
    if (m) audioStop();
  },
);

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
.theme-toggle {
  cursor: pointer;
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
</style>
