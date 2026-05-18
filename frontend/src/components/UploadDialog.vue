<template>
  <div class="modal is-active">
    <div class="modal-background" @click="emit('close')" />
    <div class="modal-card">
      <header class="modal-card-head">
        <p class="modal-card-title">Upload sound</p>
        <button class="delete" aria-label="close" @click="emit('close')" />
      </header>
      <section class="modal-card-body">
        <b-field label="File (mp3 or wav, max 10 MB)">
          <b-upload
            v-model="file"
            accept=".mp3,.wav,audio/mpeg,audio/wav,audio/x-wav"
            drag-drop
            expanded
            :disabled="!!url.trim()"
          >
            <section class="upload-droparea has-text-centered p-4">
              <p v-if="!file" class="has-text-grey">Drop a file here or click to choose.</p>
              <p v-else>{{ file.name }} — {{ (file.size / 1024).toFixed(0) }} KB</p>
            </section>
          </b-upload>
        </b-field>
        <p class="has-text-grey has-text-centered is-size-7 my-2">— or —</p>
        <b-field label="URL (direct link to mp3/wav)">
          <b-input
            v-model="url"
            placeholder="https://example.com/sound.mp3"
            type="url"
            :disabled="!!file"
          />
        </b-field>
        <b-field label="Display name">
          <b-input v-model="displayName" maxlength="120" placeholder="e.g. Airhorn" />
        </b-field>
        <b-field label="Tags (optional)">
          <b-taginput
            v-model="tags"
            :data="tagSuggestions"
            autocomplete
            open-on-focus
            allow-new
            maxtags="10"
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

const emit = defineEmits<(e: "close") => void>();

const sounds = useSoundsStore();
const categories = useCategoriesStore();
const tagsStore = useTagsStore();
const file = ref<File | null>(null);
const url = ref("");
const displayName = ref("");
const categoryId = ref<number | null>(null);
const tags = ref<string[]>([]);
const submitting = ref(false);

const tagSuggestions = computed(() =>
  tagsStore.tags.map((t) => t.name).filter((n) => !tags.value.includes(n))
);

function basenameFromUrl(raw: string): string {
  try {
    const u = new URL(raw);
    const last = u.pathname.split("/").filter(Boolean).pop() ?? "";
    return decodeURIComponent(last).replace(/\.[^.]+$/, "");
  } catch {
    return "";
  }
}

watch(file, (f) => {
  if (f && !displayName.value) {
    displayName.value = f.name.replace(/\.[^.]+$/, "");
  }
});

watch(url, (u) => {
  if (u && !displayName.value) {
    const guess = basenameFromUrl(u);
    if (guess) displayName.value = guess;
  }
});

const canSubmit = computed(() => {
  const hasSource = !!file.value || url.value.trim().length > 0;
  return hasSource && displayName.value.trim().length > 0 && !submitting.value;
});

async function submit(): Promise<void> {
  const source: File | string | null = file.value
    ? file.value
    : url.value.trim() || null;
  if (!source) return;
  submitting.value = true;
  const ok = await sounds.upload(
    source,
    displayName.value.trim(),
    categoryId.value,
    tags.value,
  );
  submitting.value = false;
  if (ok) {
    tagsStore.upsertNames(tags.value);
    emit("close");
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
