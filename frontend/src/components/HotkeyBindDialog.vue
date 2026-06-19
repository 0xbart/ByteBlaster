<template>
  <div class="modal is-active">
    <div class="modal-background" @click="emit('close')" />
    <div class="modal-card bind-card">
      <header class="modal-card-head">
        <p class="modal-card-title">Bind to a number key</p>
        <button class="delete" aria-label="close" @click="emit('close')" />
      </header>
      <section class="modal-card-body">
        <p class="mb-3">
          Bind <strong>{{ sound.display_name }}</strong> to a number key (1-0).
          Press that key to play it instantly.
        </p>
        <div class="digit-grid">
          <div v-for="d in DIGITS" :key="d" class="digit-cell">
            <button
              class="button is-medium digit-btn"
              :class="{ 'is-link': boundHere(d), 'is-primary is-light': isOccupied(d) && !boundHere(d) }"
              @click="assign(d)"
            >
              <span class="digit-num">{{ d }}</span>
              <span v-if="boundName(d)" class="digit-name">{{ boundName(d) }}</span>
              <span v-else class="digit-name has-text-grey">empty</span>
            </button>
            <button
              v-if="isOccupied(d)"
              class="button is-small is-danger is-light digit-clear"
              title="Clear"
              @click.stop="hotkeys.clearSlot(d)"
            >
              <i class="fas fa-times" aria-hidden="true" />
            </button>
          </div>
        </div>
      </section>
      <footer class="modal-card-foot is-justify-content-flex-end">
        <b-button @click="emit('close')">Close</b-button>
      </footer>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted } from "vue";
import { useEscapeClose } from "@/composables/useEscapeClose";
import { useHotkeysStore, DIGITS } from "@/stores/hotkeys";
import { useSoundsStore } from "@/stores/sounds";
import type { SoundOut } from "@/api";

const props = defineProps<{ sound: SoundOut }>();
const emit = defineEmits<{ (e: "close"): void }>();

const hotkeys = useHotkeysStore();
const sounds = useSoundsStore();

useEscapeClose(() => emit("close"));

// While the dialog is open, a digit key binds the slot instead of playing the
// sound currently bound there. Capture phase runs before App's global keydown
// (bubble), and stopImmediatePropagation prevents it from playing the old slot.
function onDigitKey(ev: KeyboardEvent): void {
  if (ev.ctrlKey || ev.metaKey || ev.altKey) return;
  const k = ev.key;
  if (!(DIGITS as readonly string[]).includes(k)) return;
  ev.preventDefault();
  ev.stopImmediatePropagation();
  assign(k);
}
onMounted(() => window.addEventListener("keydown", onDigitKey, { capture: true }));
onBeforeUnmount(() => window.removeEventListener("keydown", onDigitKey, { capture: true }));

function isOccupied(d: string): boolean {
  return hotkeys.getSlot(d) != null;
}

function boundHere(d: string): boolean {
  return hotkeys.getSlot(d) === props.sound.id;
}

function boundName(d: string): string | null {
  const id = hotkeys.getSlot(d);
  if (id == null) return null;
  return sounds.sounds.find((s) => s.id === id)?.display_name ?? "(deleted)";
}

function assign(d: string): void {
  hotkeys.setSlot(d, props.sound.id);
  emit("close");
}
</script>

<style scoped>
.bind-card {
  max-width: 440px;
  width: 100%;
}
/* 2 columns x 5 rows: 1,2 / 3,4 / 5,6 / 7,8 / 9,0. */
.digit-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.4rem;
}
.digit-cell {
  position: relative;
}
.digit-btn {
  width: 100%;
  max-width: 100%;
  height: auto;
  min-height: 3.4em;
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
  padding: 0.5em 0.3em;
  overflow: hidden;
}
.digit-num {
  font-weight: 700;
  font-size: 1.1rem;
}
.digit-name {
  display: block;
  width: 100%;
  min-width: 0;
  font-size: 0.7rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.digit-clear {
  position: absolute;
  top: -6px;
  right: -6px;
  border-radius: 50%;
  width: 22px;
  height: 22px;
  padding: 0;
}
</style>
