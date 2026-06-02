<template>
  <div class="modal is-active">
    <div class="modal-background" @click="emit('close')" />
    <div class="modal-card">
      <header class="modal-card-head">
        <p class="modal-card-title">Edit sound</p>
        <button class="delete" aria-label="close" @click="emit('close')" />
      </header>
      <section class="modal-card-body">
        <b-field label="Display name">
          <b-input v-model="displayName" maxlength="120" />
        </b-field>
        <b-field label="Category">
          <b-select v-model="categoryId" expanded>
            <option :value="null">— None —</option>
            <option v-for="c in categories.categories" :key="c.id" :value="c.id">
              {{ c.name }}
            </option>
          </b-select>
        </b-field>
        <b-field label="Tags">
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
        <p v-if="sounds.error" class="has-text-danger">{{ sounds.error }}</p>
      </section>
      <footer class="modal-card-foot is-justify-content-flex-end">
        <div class="buttons dialog-buttons mb-0">
          <b-button @click="emit('close')">Cancel</b-button>
          <b-button
            type="is-primary"
            icon-left="floppy-disk"
            :loading="submitting"
            :disabled="!canSubmit"
            @click="submit"
          >
            Save
          </b-button>
        </div>
      </footer>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { useSoundsStore } from "@/stores/sounds";
import { useCategoriesStore } from "@/stores/categories";
import { useTagsStore } from "@/stores/tags";
import type { SoundOut } from "@/api";

const props = defineProps<{ sound: SoundOut }>();
const emit = defineEmits<(e: "close") => void>();

const sounds = useSoundsStore();
const categories = useCategoriesStore();
const tagsStore = useTagsStore();
const displayName = ref(props.sound.display_name);
const categoryId = ref<number | null>(props.sound.category_id);
const tags = ref<string[]>([...props.sound.tags]);
const submitting = ref(false);

const tagSuggestions = computed(() =>
  tagsStore.tags.map((t) => t.name).filter((n) => !tags.value.includes(n))
);

const canSubmit = computed(
  () => displayName.value.trim().length > 0 && !submitting.value
);

function tagsChanged(): boolean {
  const before = [...props.sound.tags].sort();
  const after = [...tags.value].sort();
  if (before.length !== after.length) return true;
  return before.some((t, i) => t !== after[i]);
}

async function submit(): Promise<void> {
  submitting.value = true;
  const patch: { display_name?: string; category_id?: number | null; tags?: string[] } = {};
  const newName = displayName.value.trim();
  if (newName !== props.sound.display_name) patch.display_name = newName;
  if (categoryId.value !== props.sound.category_id) patch.category_id = categoryId.value;
  if (tagsChanged()) patch.tags = tags.value;
  if (Object.keys(patch).length === 0) {
    submitting.value = false;
    emit("close");
    return;
  }
  const ok = await sounds.update(props.sound.id, patch);
  submitting.value = false;
  if (ok) {
    tagsStore.upsertNames(tags.value);
    emit("close");
  }
}
</script>

<style scoped>
.dialog-buttons {
  gap: 1rem;
}
</style>
