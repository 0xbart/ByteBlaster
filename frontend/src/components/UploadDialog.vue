<template>
  <div class="modal is-active">
    <div class="modal-background" @click="emit('close')" />
    <div class="modal-card">
      <header class="modal-card-head">
        <p class="modal-card-title">Upload sound</p>
        <button class="delete" aria-label="close" @click="emit('close')" />
      </header>
      <section class="modal-card-body">
        <b-field label="Files (mp3 or wav, max 10 MB each)">
          <b-upload
            v-model="files"
            accept=".mp3,.wav,audio/mpeg,audio/wav,audio/x-wav"
            drag-drop
            expanded
            multiple
            :disabled="!!url.trim()"
          >
            <section class="upload-droparea has-text-centered p-4">
              <p v-if="!files.length" class="has-text-grey">
                Drop one or more files here or click to choose.
              </p>
              <p v-else-if="files.length === 1">
                {{ files[0].name }} — {{ (files[0].size / 1024).toFixed(0) }} KB
              </p>
              <p v-else>{{ files.length }} files selected</p>
            </section>
          </b-upload>
        </b-field>
        <p v-if="isBatch" class="has-text-grey is-size-7 mb-3">
          Batch upload: display names are taken from each file name. Tags and
          category below apply to all.
        </p>
        <template v-if="!isBatch">
          <p class="has-text-grey has-text-centered is-size-7 my-2">— or —</p>
          <b-field label="URL (direct link to mp3/wav)">
            <b-input
              v-model="url"
              placeholder="https://example.com/sound.mp3"
              type="url"
              :disabled="!!files.length"
            />
          </b-field>
          <b-field label="Display name">
            <b-input v-model="displayName" maxlength="120" placeholder="e.g. Airhorn" />
          </b-field>
        </template>
        <b-field label="Tags (optional)">
          <b-taginput
            v-model="tags"
            :data="tagSuggestions"
            autocomplete
            open-on-focus
            allow-new
            :maxtags="10"
            placeholder="Type and press enter (e.g. computer, fun)"
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
        <p v-if="sounds.error" class="has-text-danger">{{ sounds.error }}</p>
      </section>
      <footer class="modal-card-foot is-justify-content-flex-end">
        <div class="buttons dialog-buttons mb-0">
          <b-button @click="emit('close')">Cancel</b-button>
          <b-button
            type="is-primary"
            icon-left="upload"
            :loading="submitting"
            :disabled="!canSubmit"
            @click="submit"
          >
            Upload
          </b-button>
        </div>
      </footer>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useSoundsStore } from "@/stores/sounds";
import { useCategoriesStore } from "@/stores/categories";
import { useTagsStore } from "@/stores/tags";
import { celebrate } from "@/composables/useConfetti";

const props = defineProps<{
  initialUrl?: string;
  initialName?: string;
}>();

const emit = defineEmits<(e: "close") => void>();

const sounds = useSoundsStore();
const categories = useCategoriesStore();
const tagsStore = useTagsStore();
const files = ref<File[]>([]);
const url = ref(props.initialUrl ?? "");
const displayName = ref(props.initialName ?? "");
const categoryId = ref<number | null>(null);
const tags = ref<string[]>([]);
const submitting = ref(false);

const isBatch = computed(() => files.value.length > 1);

const tagSuggestions = computed(() =>
  tagsStore.tags.map((t) => t.name).filter((n) => !tags.value.includes(n))
);

function stripExt(name: string): string {
  return name.replace(/\.[^.]+$/, "");
}

function basenameFromUrl(raw: string): string {
  try {
    const u = new URL(raw);
    const last = u.pathname.split("/").filter(Boolean).pop() ?? "";
    return decodeURIComponent(last).replace(/\.[^.]+$/, "");
  } catch {
    return "";
  }
}

watch(files, (f) => {
  if (f.length === 1 && !displayName.value) {
    displayName.value = stripExt(f[0].name);
  }
});

watch(url, (u) => {
  if (u && !displayName.value) {
    const guess = basenameFromUrl(u);
    if (guess) displayName.value = guess;
  }
});

const canSubmit = computed(() => {
  if (submitting.value) return false;
  if (isBatch.value) return true;
  const hasSource = files.value.length === 1 || url.value.trim().length > 0;
  return hasSource && displayName.value.trim().length > 0;
});

async function submit(): Promise<void> {
  submitting.value = true;
  try {
    if (isBatch.value) {
      let allOk = true;
      for (const f of files.value) {
        const ok = await sounds.upload(f, stripExt(f.name), categoryId.value, tags.value);
        if (!ok) allOk = false;
      }
      if (allOk) {
        tagsStore.upsertNames(tags.value);
        celebrate();
        emit("close");
      }
      return;
    }
    const source: File | string | null = files.value[0] ?? url.value.trim() ?? null;
    if (!source) return;
    const ok = await sounds.upload(source, displayName.value.trim(), categoryId.value, tags.value);
    if (ok) {
      tagsStore.upsertNames(tags.value);
      celebrate();
      emit("close");
    }
  } finally {
    submitting.value = false;
  }
}
</script>

<style scoped>
.upload-droparea {
  border: 2px dashed var(--bulma-border, #ccc);
  border-radius: 6px;
}
.dialog-buttons {
  gap: 1rem;
}
</style>
