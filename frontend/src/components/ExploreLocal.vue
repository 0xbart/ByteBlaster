<template>
  <div>
    <div class="explore-actions mb-3">
      <b-input
        v-model="q"
        placeholder="Filter local sounds…"
        icon="magnify"
        clearable
        class="search-input"
      />
      <b-button icon-left="refresh" :loading="explore.localLoading" @click="reload">
        Refresh
      </b-button>
    </div>
    <p class="has-text-grey is-size-7 mb-2">
      Sounds from the local <code>sounds/</code> folder. Subfolders are
      categories — click a header to collapse it. Clicking a sound plays it only
      in this tab.
    </p>
    <p v-if="filtered.length" class="has-text-grey is-size-7 mb-3">
      <a class="collapse-link" @click="expandAll">Expand all</a>
      <span class="has-text-grey-light"> · </span>
      <a class="collapse-link" @click="collapseAll">Collapse all</a>
    </p>
    <p v-if="explore.localError" class="has-text-danger">{{ explore.localError }}</p>

    <div v-if="explore.localLoading && !explore.localLoaded" class="has-text-centered py-5">
      <b-loading :is-full-page="false" :model-value="true" />
    </div>
    <div
      v-else-if="!filtered.length"
      class="has-text-centered has-text-grey py-5"
    >
      <template v-if="explore.localLoaded && !explore.localCategories.length">
        No local sounds found. Drop mp3/wav files into the <code>sounds/</code>
        folder.
      </template>
      <template v-else>No matches.</template>
    </div>
    <div v-else class="sound-groups">
      <section v-for="cat in filtered" :key="cat.name" class="sound-group">
        <h3 class="sound-group__title" role="button" @click="toggleGroup(cat.name)">
          <b-icon
            :icon="isCollapsed(cat.name) ? 'circle-chevron-up' : 'circle-chevron-down'"
            pack="fas"
            size="is-small"
            class="mr-2"
          />
          <span>{{ cat.name }}</span>
          <span class="sound-group__count">{{ cat.sounds.length }}</span>
        </h3>
        <div v-show="!isCollapsed(cat.name)" class="sound-grid">
          <div
            v-for="s in cat.sounds"
            :key="s.rel"
            class="explore-card"
            :title="s.title"
            @click="onPlay(s)"
          >
            <span class="explore-name">{{ s.title }}</span>
            <button
              class="button is-small is-warning add-btn editor-btn"
              title="Send to editor"
              tabindex="-1"
              @click.stop="onSendToEditor(s)"
            >
              <i class="fas fa-sliders" aria-hidden="true" />
            </button>
            <button
              class="button is-small is-info add-btn"
              title="Add to soundboard"
              tabindex="-1"
              @click.stop="onAdd(s)"
            >
              <i class="fas fa-plus" aria-hidden="true" />
            </button>
          </div>
        </div>
      </section>
    </div>

    <LocalImportDialog
      v-if="addDialog"
      :rel="addDialog.rel"
      :initial-name="addDialog.title"
      @close="addDialog = null"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import LocalImportDialog from "./LocalImportDialog.vue";
import { useExploreStore } from "@/stores/explore";
import { useEditorStore } from "@/stores/editor";
import { useAudioPlayer } from "@/composables/useAudioPlayer";
import type { LocalSound } from "@/api";

const explore = useExploreStore();
const editorStore = useEditorStore();
const audio = useAudioPlayer();

const q = ref("");
const addDialog = ref<LocalSound | null>(null);
const collapsed = ref<Set<string>>(new Set());

onMounted(() => {
  if (!explore.localLoaded) void explore.loadLocal();
});

function reload(): void {
  void explore.loadLocal();
}

// Client-side filter: the list is local, so filtering by title needs no
// round-trip. Drops categories that end up empty.
const filtered = computed(() => {
  const needle = q.value.trim().toLowerCase();
  if (!needle) return explore.localCategories;
  return explore.localCategories
    .map((c) => ({
      ...c,
      sounds: c.sounds.filter((s) => s.title.toLowerCase().includes(needle)),
    }))
    .filter((c) => c.sounds.length > 0);
});

function isCollapsed(key: string): boolean {
  return collapsed.value.has(key);
}
function toggleGroup(key: string): void {
  const next = new Set(collapsed.value);
  if (next.has(key)) next.delete(key);
  else next.add(key);
  collapsed.value = next;
}
function expandAll(): void {
  collapsed.value = new Set();
}
function collapseAll(): void {
  collapsed.value = new Set(filtered.value.map((c) => c.name));
}

function onPlay(s: LocalSound): void {
  audio.play(s.url);
}
function onSendToEditor(s: LocalSound): void {
  editorStore.queueLocal(s.url, s.title);
}
function onAdd(s: LocalSound): void {
  addDialog.value = s;
}
</script>

<style scoped>
.explore-actions {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  flex-wrap: wrap;
}
.search-input {
  flex: 1 1 240px;
  min-width: 200px;
}
.collapse-link {
  cursor: pointer;
}
.sound-groups {
  margin-top: 1rem;
}
.sound-group + .sound-group {
  margin-top: 1.25rem;
}
.sound-group__title {
  display: flex;
  align-items: center;
  font-size: 0.85rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #555;
  margin-bottom: 0.5rem;
  padding-bottom: 0.35rem;
  border-bottom: 1px solid var(--bulma-border-weak, rgba(128, 128, 128, 0.22));
  cursor: pointer;
  user-select: none;
}
.sound-group__count {
  margin-left: 0.5rem;
  background: var(--bulma-scheme-main-ter, rgba(0, 0, 0, 0.1));
  color: inherit;
  border-radius: 999px;
  padding: 0 0.5rem;
  font-size: 0.75rem;
}
.sound-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 0.75rem;
}
.explore-card {
  position: relative;
  background: var(--bulma-scheme-main-ter, #f4f4f6);
  border: 1px solid var(--bulma-border-weak, rgba(128, 128, 128, 0.22));
  border-radius: 6px;
  padding: 0.6rem 4.25rem 0.6rem 0.75rem;
  min-height: 2.5em;
  cursor: pointer;
  user-select: none;
  display: flex;
  align-items: center;
  transition: background 0.12s ease-in-out;
}
.explore-card:hover {
  background: var(--bulma-scheme-main, #fff);
}
.explore-name {
  font-size: 0.85rem;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1 1 auto;
  min-width: 0;
}
.add-btn {
  position: absolute;
  top: 50%;
  right: 6px;
  transform: translateY(-50%);
  border-radius: 50%;
  width: 28px;
  height: 28px;
  padding: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.12s ease-in-out;
}
.explore-card:hover .add-btn,
.explore-card:focus-within .add-btn {
  opacity: 1;
  pointer-events: auto;
}
.editor-btn {
  right: 42px;
}
</style>
