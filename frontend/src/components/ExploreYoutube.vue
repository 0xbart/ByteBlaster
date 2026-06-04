<template>
  <div>
    <div class="explore-actions mb-3">
      <b-input
        v-model="url"
        placeholder="https://www.youtube.com/watch?v=…"
        icon="link"
        type="url"
        clearable
        class="search-input"
        @keyup.enter="onFetch"
      />
      <b-button
        type="is-primary"
        icon-left="download"
        :loading="explore.youtubeLoading"
        @click="onFetch"
      >
        Fetch
      </b-button>
    </div>
    <p class="has-text-grey is-size-7 mb-3">
      Paste a YouTube URL. Audio max 20 seconds. Longer videos are rejected
      before download.
    </p>
    <p v-if="explore.youtubeError" class="has-text-danger">
      {{ explore.youtubeError }}
    </p>

    <div v-if="explore.youtubeResult" class="sound-grid">
      <div
        class="explore-card"
        :title="explore.youtubeResult.title"
        @click="onLocalPlay(explore.youtubeResult.preview_url)"
      >
        <span class="explore-name">{{ explore.youtubeResult.title }}</span>
        <span class="explore-duration has-text-grey is-size-7">
          {{ formatSec(explore.youtubeResult.duration_ms) }}
        </span>
        <button
          class="button is-small is-info add-btn"
          title="Add to soundboard"
          tabindex="-1"
          @click.stop="onAdd"
        >
          <i class="fas fa-plus" aria-hidden="true" />
        </button>
      </div>
    </div>

    <UploadDialog
      v-if="addDialog"
      :initial-url="addDialog.preview_url"
      :initial-name="addDialog.title"
      @close="onDialogClose"
    />
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import UploadDialog from "./UploadDialog.vue";
import { useExploreStore } from "@/stores/explore";
import { useAudioPlayer } from "@/composables/useAudioPlayer";
import type { YoutubeFetchOut } from "@/api";

const explore = useExploreStore();
const audio = useAudioPlayer();
const url = ref(explore.youtubeUrl);
const addDialog = ref<YoutubeFetchOut | null>(null);

function onFetch(): void {
  const v = url.value.trim();
  if (!v) {
    explore.resetYoutube();
    return;
  }
  void explore.fetchYoutube(v);
}
function onLocalPlay(u: string): void {
  audio.play(u);
}
function onAdd(): void {
  addDialog.value = explore.youtubeResult;
}
function onDialogClose(): void {
  addDialog.value = null;
}
function formatSec(ms: number): string {
  return `${Math.round(ms / 1000)}s`;
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
.sound-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 0.75rem;
}
.explore-card {
  position: relative;
  background: var(--bulma-scheme-main-ter, #f4f4f6);
  border: 1px solid var(--bulma-border-weak, rgba(128, 128, 128, 0.22));
  border-radius: 6px;
  padding: 0.6rem 2.5rem 0.6rem 0.75rem;
  min-height: 2.5em;
  cursor: pointer;
  user-select: none;
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
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
</style>
