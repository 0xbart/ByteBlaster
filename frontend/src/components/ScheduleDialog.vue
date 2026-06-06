<template>
  <div class="modal is-active">
    <div class="modal-background" @click="emit('close')" />
    <div class="modal-card schedule-card">
      <header class="modal-card-head">
        <p class="modal-card-title">Schedule sound</p>
        <button class="delete" aria-label="close" @click="emit('close')" />
      </header>
      <section class="modal-card-body">
        <p class="mb-3">
          Play <strong>{{ soundName }}</strong> after:
        </p>
        <b-field grouped>
          <b-field label="Minutes">
            <b-numberinput
              v-model="minutes"
              :min="0"
              :max="SCHEDULER_MAX_MINUTES"
              :step="1"
              controls-position="compact"
            />
          </b-field>
          <b-field label="Seconds">
            <b-numberinput
              v-model="seconds"
              :min="0"
              :max="59"
              :step="1"
              controls-position="compact"
            />
          </b-field>
        </b-field>
        <p class="has-text-grey is-size-7">
          Max 120 min. Timer runs locally — closes on tab refresh.
          {{ schedulerStore.items.length }} / 5 scheduled.
        </p>
        <p v-if="schedulerStore.isFull" class="has-text-danger mt-2">
          Scheduler is full (max 5). Cancel one before adding another.
        </p>
      </section>
      <footer class="modal-card-foot is-justify-content-flex-end">
        <div class="buttons dialog-buttons mb-0">
          <b-button @click="emit('close')">Cancel</b-button>
          <b-button
            type="is-primary"
            icon-left="clock"
            :disabled="!canSubmit"
            @click="onSchedule"
          >
            Schedule
          </b-button>
        </div>
      </footer>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { useSchedulerStore, SCHEDULER_MAX_MINUTES } from "@/stores/scheduler";

const props = defineProps<{ soundId: number; soundName: string }>();
const emit = defineEmits<(e: "close") => void>();

const schedulerStore = useSchedulerStore();
const minutes = ref(1);
const seconds = ref(0);

const totalMs = computed(() => minutes.value * 60_000 + seconds.value * 1000);
const canSubmit = computed(
  () =>
    !schedulerStore.isFull &&
    totalMs.value > 0 &&
    minutes.value * 60 + seconds.value <= SCHEDULER_MAX_MINUTES * 60,
);

function onSchedule(): void {
  if (!canSubmit.value) return;
  if (schedulerStore.schedule(props.soundId, props.soundName, totalMs.value)) {
    emit("close");
  }
}
</script>

<style scoped>
.schedule-card {
  max-width: 420px;
  width: 100%;
}
.dialog-buttons {
  gap: 1rem;
}
</style>
