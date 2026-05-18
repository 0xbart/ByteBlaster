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
import { useWebSocket } from "./composables/useWebSocket";

const userStore = useUserStore();
const categoriesStore = useCategoriesStore();
const tagsStore = useTagsStore();
const statsStore = useStatsStore();
const presence = usePresenceStore();
const theme = useThemeStore();
const { me, loaded, needsClaim, isAdmin, isSuperadmin } = storeToRefs(userStore);

const view = ref<"board" | "admin">("board");
const presenceOpen = ref(false);

const { connected: wsConnected } = useWebSocket();

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
</style>
