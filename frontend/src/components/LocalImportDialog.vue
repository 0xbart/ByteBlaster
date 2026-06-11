<template>
  <div class="modal is-active">
    <div class="modal-background" @click="emit('close')" />
    <div class="modal-card">
      <header class="modal-card-head">
        <p class="modal-card-title">Add to soundboard</p>
        <button class="delete" aria-label="close" @click="emit('close')" />
      </header>
      <section class="modal-card-body">
        <p class="has-text-grey is-size-7 mb-3">
          Copies <strong>{{ rel }}</strong> from the local library into the
          soundboard. The original file is left untouched.
        </p>
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
        <p v-if="error" class="has-text-danger">{{ error }}</p>
      </section>
      <footer class="modal-card-foot is-justify-content-flex-end">
        <div class="buttons dialog-buttons mb-0">
          <b-button @click="emit('close')">Cancel</b-button>
          <b-button
            type="is-primary"
            icon-left="plus"
            :loading="submitting"
            :disabled="!canSubmit"
            @click="submit"
          >
            Add
          </b-button>
        </div>
      </footer>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { useExploreStore } from "@/stores/explore";
import { useEscapeClose } from "@/composables/useEscapeClose";
import { useCategoriesStore } from "@/stores/categories";
import { useTagsStore } from "@/stores/tags";
import { celebrate } from "@/composables/useConfetti";

const props = defineProps<{
  rel: string;
  initialName?: string;
}>();

const emit = defineEmits<(e: "close") => void>();
useEscapeClose(() => emit("close"));

const explore = useExploreStore();
const categories = useCategoriesStore();
const tagsStore = useTagsStore();

const displayName = ref(props.initialName ?? "");
const categoryId = ref<number | null>(null);
const tags = ref<string[]>([]);
const submitting = ref(false);
const error = ref<string | null>(null);

const tagSuggestions = computed(() =>
  tagsStore.tags.map((t) => t.name).filter((n) => !tags.value.includes(n)),
);

const canSubmit = computed(
  () => !submitting.value && displayName.value.trim().length > 0,
);

async function submit(): Promise<void> {
  submitting.value = true;
  error.value = null;
  try {
    const ok = await explore.importLocal(
      props.rel,
      displayName.value.trim(),
      categoryId.value,
      tags.value,
    );
    if (ok) {
      tagsStore.upsertNames(tags.value);
      celebrate();
      emit("close");
    } else {
      error.value = "Import failed.";
    }
  } finally {
    submitting.value = false;
  }
}
</script>

<style scoped>
.dialog-buttons {
  gap: 1rem;
}
</style>
