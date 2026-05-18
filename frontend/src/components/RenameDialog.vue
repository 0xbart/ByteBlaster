<template>
  <div class="modal is-active">
    <div class="modal-background" @click="emit('close')" />
    <div class="modal-card rename-card">
      <header class="modal-card-head">
        <p class="modal-card-title">{{ title }}</p>
        <button class="delete" aria-label="close" @click="emit('close')" />
      </header>
      <section class="modal-card-body">
        <b-field :label="label">
          <b-input
            v-model="value"
            :maxlength="maxlength"
            :placeholder="placeholder"
            autofocus
            @keyup.enter="onConfirm"
          />
        </b-field>
        <p v-if="error" class="has-text-danger is-size-7">{{ error }}</p>
      </section>
      <footer class="modal-card-foot is-justify-content-flex-end">
        <div class="buttons rename-buttons mb-0">
          <b-button @click="emit('close')">Cancel</b-button>
          <b-button
            type="is-primary"
            icon-left="content-save"
            :disabled="!canSubmit"
            :loading="loading"
            @click="onConfirm"
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

const props = withDefaults(
  defineProps<{
    title: string;
    label?: string;
    initial: string;
    maxlength?: number;
    placeholder?: string;
    error?: string | null;
    loading?: boolean;
  }>(),
  {
    label: "Name",
    maxlength: 64,
    placeholder: "",
    error: null,
    loading: false,
  },
);

const emit = defineEmits<{
  (e: "confirm", value: string): void;
  (e: "close"): void;
}>();

const value = ref(props.initial);

const canSubmit = computed(() => {
  const v = value.value.trim();
  return v.length > 0 && v !== props.initial;
});

function onConfirm(): void {
  if (!canSubmit.value) return;
  emit("confirm", value.value.trim());
}
</script>

<style scoped>
.rename-card {
  max-width: 420px;
  width: 100%;
}
.rename-buttons {
  gap: 1rem;
}
</style>
