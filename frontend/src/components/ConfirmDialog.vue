<template>
  <div class="modal is-active">
    <div class="modal-background" @click="emit('close')" />
    <div class="modal-card confirm-card">
      <header class="modal-card-head">
        <p class="modal-card-title">{{ title }}</p>
        <button class="delete" aria-label="close" @click="emit('close')" />
      </header>
      <section class="modal-card-body">
        <p>{{ message }}</p>
      </section>
      <footer class="modal-card-foot is-justify-content-flex-end">
        <div class="buttons confirm-buttons mb-0">
          <b-button @click="emit('close')">{{ cancelLabel }}</b-button>
          <b-button :type="confirmType" icon-left="delete" @click="onConfirm">
            {{ confirmLabel }}
          </b-button>
        </div>
      </footer>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useEscapeClose } from "@/composables/useEscapeClose";

withDefaults(
  defineProps<{
    title: string;
    message: string;
    confirmLabel?: string;
    cancelLabel?: string;
    confirmType?: string;
  }>(),
  {
    confirmLabel: "Delete",
    cancelLabel: "Cancel",
    confirmType: "is-danger",
  },
);

const emit = defineEmits<{
  (e: "confirm"): void;
  (e: "close"): void;
}>();

useEscapeClose(() => emit("close"));

function onConfirm(): void {
  emit("confirm");
  emit("close");
}
</script>

<style scoped>
.confirm-card {
  max-width: 420px;
  width: 100%;
}
.confirm-buttons {
  gap: 1rem;
}
</style>
