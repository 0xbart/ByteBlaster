<template>
  <div class="explore-view">
    <div class="explore-actions mb-3">
      <b-input
        ref="searchInput"
        v-model="q"
        placeholder="Search myinstants…"
        icon="magnify"
        clearable
        autofocus
        class="search-input"
        @keyup.enter="onSearch"
      />
      <b-button
        type="is-primary"
        icon-left="magnify"
        :loading="explore.loading"
        @click="onSearch"
      >
        Search
      </b-button>
    </div>
    <p class="has-text-grey is-size-7 mb-3">
      Preview sounds locally before adding them. Clicking a result plays it
      only in this tab.
    </p>
    <p v-if="explore.error" class="has-text-danger">{{ explore.error }}</p>

    <div v-if="explore.loading && !explore.results.length" class="has-text-centered py-5">
      <b-loading :is-full-page="false" :model-value="true" />
    </div>
    <div v-else-if="explore.results.length" class="sound-grid">
      <div
        v-for="(r, i) in explore.results"
        :key="`${explore.page}-${i}-${r.mp3_url}`"
        class="explore-card"
        :title="r.title"
        @click="onLocalPlay(r.mp3_url)"
      >
        <span class="explore-name">{{ r.title }}</span>
        <button
          class="button is-small is-primary add-btn"
          title="Add to soundboard"
          tabindex="-1"
          @click.stop="onAdd(r)"
        >
          <i class="fas fa-plus" aria-hidden="true" />
        </button>
      </div>
    </div>
    <div
      v-else-if="!explore.loading && explore.query"
      class="has-text-centered has-text-grey py-5"
    >
      No results.
    </div>

    <div v-if="explore.results.length" class="pagination-footer mt-4">
      <b-button
        icon-left="chevron-left"
        :disabled="explore.page <= 1 || explore.loading"
        @click="explore.prevPage"
      >
        Previous
      </b-button>
      <span class="has-text-grey">Page {{ explore.page }}</span>
      <b-button
        icon-right="chevron-right"
        :disabled="!explore.hasMore || explore.loading"
        @click="explore.nextPage"
      >
        Next
      </b-button>
    </div>

    <UploadDialog
      v-if="addDialog"
      :initial-url="addDialog.mp3_url"
      :initial-name="addDialog.title"
      @close="addDialog = null"
    />
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import UploadDialog from "./UploadDialog.vue";
import { useExploreStore } from "@/stores/explore";
import { useAudioPlayer } from "@/composables/useAudioPlayer";
import type { ExploreResult } from "@/api";

const explore = useExploreStore();
const audio = useAudioPlayer();
const q = ref(explore.query);
const addDialog = ref<ExploreResult | null>(null);

function onSearch(): void {
  const v = q.value.trim();
  if (!v) {
    q.value = "";
    explore.reset();
    return;
  }
  void explore.search(v, 1);
}
function onLocalPlay(url: string): void {
  audio.play(url);
}
function onAdd(r: ExploreResult): void {
  addDialog.value = r;
}
</script>

<style scoped>
.explore-view {
  background: var(--bulma-scheme-main-bis, white);
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}
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
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 0.75rem;
}
.explore-card {
  position: relative;
  background: var(--bulma-scheme-main-ter, #f4f4f6);
  border: 1px solid var(--bulma-border-weak, rgba(128, 128, 128, 0.22));
  border-radius: 6px;
  padding: 0.6rem 2.25rem 0.6rem 0.75rem;
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
}
.pagination-footer {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
}
</style>
