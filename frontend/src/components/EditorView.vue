<template>
  <div class="editor-view">
    <h2 class="title is-4">Audio editor</h2>

    <div class="source-picker mb-4">
      <b-field grouped>
        <b-field label="Pick existing sound" expanded>
          <b-autocomplete
            v-model="pickQuery"
            :data="filteredSounds"
            field="display_name"
            placeholder="Type a sound name…"
            clearable
            @select="onPickSound"
          />
        </b-field>
        <b-field label="…or load by URL" expanded>
          <b-input v-model="urlInput" placeholder="https://… .mp3" @keyup.enter="onLoadUrl" />
        </b-field>
        <b-field label="&nbsp;">
          <b-button type="is-info" icon-left="download" @click="onLoadUrl">
            Load URL
          </b-button>
        </b-field>
      </b-field>
      <p v-if="editor.sourceTitle" class="has-text-grey is-size-7">
        Loaded: <strong>{{ editor.sourceTitle }}</strong>
      </p>
    </div>

    <div v-if="editor.sourceAudioUrl" class="waveform-area mb-3">
      <div ref="containerEl" class="wave" />
      <div class="transport mt-2">
        <b-button icon-left="play" @click="togglePlay">
          {{ playing ? "Pause" : "Play" }}
        </b-button>
        <b-button
          :icon-left="regionPlaying ? 'stop' : 'content-cut'"
          @click="playRegion"
        >
          {{ regionPlaying ? "Stop" : "Play region" }}
        </b-button>
        <b-button icon-left="restore" @click="resetRegion">Reset</b-button>
        <span class="region-readout ml-3 has-text-grey is-size-7">
          Start {{ editor.startSec.toFixed(2) }}s · End {{ editor.endSec.toFixed(2) }}s ·
          Length {{ (editor.endSec - editor.startSec).toFixed(2) }}s · Source
          {{ editor.durationSec.toFixed(2) }}s
        </span>
      </div>
    </div>
    <p v-else class="has-text-grey">
      Load a sound or paste a URL to start editing.
    </p>

    <div v-if="editor.sourceAudioUrl" class="save-panel">
      <h3 class="title is-5 mt-4">Save trimmed</h3>
      <b-field label="Display name">
        <b-input v-model="displayName" maxlength="120" placeholder="e.g. Airhorn short" />
      </b-field>
      <b-field label="Tags (optional)">
        <b-taginput
          v-model="tags"
          :data="tagSuggestions"
          autocomplete
          open-on-focus
          allow-new
          :maxtags="10"
          placeholder="Type and press enter"
        />
      </b-field>
      <b-field label="Category (optional)">
        <b-select v-model="categoryId" expanded placeholder="No category">
          <option :value="null">— None —</option>
          <option v-for="c in categories.categories" :key="c.id" :value="c.id">
            {{ c.name }}
          </option>
        </b-select>
      </b-field>
      <p v-if="error" class="has-text-danger">{{ error }}</p>
      <div class="buttons mt-3">
        <b-button
          type="is-primary"
          icon-left="content-save"
          :loading="saving"
          :disabled="!canSave"
          @click="onSave"
        >
          Save trimmed
        </b-button>
        <b-button @click="onClearAll">Clear</b-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import WaveSurfer from "wavesurfer.js";
import RegionsPlugin from "wavesurfer.js/dist/plugins/regions.esm.js";
import { useEditorStore } from "@/stores/editor";
import { useSoundsStore } from "@/stores/sounds";
import { useCategoriesStore } from "@/stores/categories";
import { useTagsStore } from "@/stores/tags";
import { api } from "@/api";
import { celebrate } from "@/composables/useConfetti";
import type { SoundOut } from "@/api";

const editor = useEditorStore();
const sounds = useSoundsStore();
const categories = useCategoriesStore();
const tagsStore = useTagsStore();

const containerEl = ref<HTMLDivElement | null>(null);
let ws: WaveSurfer | null = null;
let regionsPlugin: ReturnType<typeof RegionsPlugin.create> | null = null;
const playing = ref(false);
const regionPlaying = ref(false);

const pickQuery = ref("");
const urlInput = ref("");
const displayName = ref("");
const categoryId = ref<number | null>(null);
const tags = ref<string[]>([]);
const error = ref<string | null>(null);
const saving = ref(false);

const filteredSounds = computed(() =>
  sounds.sortedByName.filter((s) =>
    s.display_name.toLowerCase().includes(pickQuery.value.toLowerCase()),
  ),
);
const tagSuggestions = computed(() =>
  tagsStore.tags.map((t) => t.name).filter((n) => !tags.value.includes(n)),
);
const canSave = computed(
  () =>
    !saving.value &&
    !!editor.sourceAudioUrl &&
    displayName.value.trim().length > 0 &&
    editor.endSec > editor.startSec &&
    editor.endSec - editor.startSec <= 60,
);

function onPickSound(s: SoundOut | null): void {
  if (!s) return;
  editor.loadSound(s.id, s.display_name, s.url);
  displayName.value = `${s.display_name} (cut)`;
}
function onLoadUrl(): void {
  const v = urlInput.value.trim();
  if (!v) return;
  editor.loadUrl(v, v.split("/").pop() ?? "Audio");
  displayName.value = editor.sourceTitle;
}
function onClearAll(): void {
  editor.clear();
  destroySurfer();
  pickQuery.value = "";
  urlInput.value = "";
  displayName.value = "";
  categoryId.value = null;
  tags.value = [];
  error.value = null;
}

function destroySurfer(): void {
  if (ws) {
    try {
      ws.destroy();
    } catch {
      // ignore
    }
    ws = null;
    regionsPlugin = null;
  }
  playing.value = false;
  regionPlaying.value = false;
}

function resetSurfer(): void {
  destroySurfer();
  if (!editor.sourceAudioUrl || !containerEl.value) return;
  regionsPlugin = RegionsPlugin.create();
  ws = WaveSurfer.create({
    container: containerEl.value,
    height: 120,
    waveColor: "hsl(204, 86%, 53%)",
    progressColor: "hsl(204, 86%, 35%)",
    cursorColor: "hsl(28, 95%, 50%)",
    url: editor.sourceAudioUrl,
    plugins: [regionsPlugin],
  });
  ws.on("decode", (duration: number) => {
    editor.setDuration(duration);
    const initEnd = Math.min(Math.max(duration, 1), 5);
    const r = regionsPlugin!.addRegion({
      start: 0,
      end: initEnd,
      color: "rgba(75, 150, 255, 0.18)",
      drag: true,
      resize: true,
    });
    editor.setRegion(r.start, r.end);
    r.on("update", () => editor.setRegion(r.start, r.end));
  });
  ws.on("play", () => (playing.value = true));
  ws.on("pause", () => {
    playing.value = false;
    regionPlaying.value = false;
  });
  ws.on("finish", () => {
    playing.value = false;
    regionPlaying.value = false;
  });
}

function togglePlay(): void {
  ws?.playPause();
}
function playRegion(): void {
  if (!ws) return;
  if (regionPlaying.value) {
    ws.pause();
    return;
  }
  const list = regionsPlugin?.getRegions() ?? [];
  if (list.length === 0) return;
  list[0].play(true); // stopAtEnd → wavesurfer.play(start, end)
  regionPlaying.value = true;
}
function resetRegion(): void {
  if (!regionsPlugin || !editor.durationSec) return;
  for (const r of regionsPlugin.getRegions()) r.remove();
  const initEnd = Math.min(Math.max(editor.durationSec, 1), 5);
  const r = regionsPlugin.addRegion({
    start: 0,
    end: initEnd,
    color: "rgba(75, 150, 255, 0.18)",
    drag: true,
    resize: true,
  });
  editor.setRegion(r.start, r.end);
  r.on("update", () => editor.setRegion(r.start, r.end));
}

async function onSave(): Promise<void> {
  if (!canSave.value) return;
  saving.value = true;
  error.value = null;
  const body = {
    sound_id: editor.soundId,
    source_url: editor.sourceUrl,
    start_s: editor.startSec,
    end_s: editor.endSec,
    display_name: displayName.value.trim(),
    category_id: categoryId.value,
    tags: tags.value,
  };
  const { data, response } = await api.POST("/api/editor/trim", { body });
  saving.value = false;
  if (data) {
    celebrate();
    tagsStore.upsertNames(tags.value);
    onClearAll();
  } else {
    let msg = "Save failed.";
    try {
      const b = (await response.clone().json()) as { detail?: string };
      if (b.detail) msg = b.detail;
    } catch {
      // ignore
    }
    error.value = msg;
  }
}

onMounted(() => {
  const pending = editor.consumePending();
  if (pending) {
    if (pending.soundId !== undefined) {
      editor.loadSound(pending.soundId, pending.title, pending.audioUrl);
    } else if (pending.url) {
      editor.loadUrl(pending.url, pending.title);
    }
    displayName.value = pending.title;
  }
});

onBeforeUnmount(() => {
  destroySurfer();
});

// flush:"post" → the v-if waveform container is in the DOM before we
// create WaveSurfer; otherwise containerEl is null and ws is never built.
watch(
  () => editor.sourceAudioUrl,
  (url) => {
    if (url) resetSurfer();
    else destroySurfer();
  },
  { flush: "post" },
);
</script>

<style scoped>
.editor-view {
  background: var(--bulma-scheme-main-bis, white);
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}
.wave {
  background: var(--bulma-scheme-main-ter, rgba(0, 0, 0, 0.04));
  border-radius: 6px;
  padding: 0.5rem;
}
.transport {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  align-items: center;
}
.region-readout {
  font-variant-numeric: tabular-nums;
}
</style>
