import { defineStore } from "pinia";
import { computed, ref, watch } from "vue";

const STORAGE_KEY = "byteblaster:volume";
const DEFAULT_VOLUME = 100;

function loadInitial(): number {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (raw === null) return DEFAULT_VOLUME;
  const n = parseInt(raw, 10);
  if (Number.isNaN(n)) return DEFAULT_VOLUME;
  return Math.max(0, Math.min(100, n));
}

export const useAudioStore = defineStore("audio", () => {
  const volume = ref<number>(loadInitial());
  const muted = computed(() => volume.value === 0);

  const volumeIcon = computed(() => {
    const v = volume.value;
    if (v === 0) return "volume-xmark";
    if (v <= 33) return "volume-low";
    if (v <= 66) return "volume";
    return "volume-high";
  });

  function setVolume(n: number): void {
    volume.value = Math.max(0, Math.min(100, Math.round(n)));
  }

  // Toggle = mute when audible, restore to 100% when muted.
  function toggle(): void {
    volume.value = volume.value === 0 ? DEFAULT_VOLUME : 0;
  }

  watch(volume, (v) => {
    localStorage.setItem(STORAGE_KEY, String(v));
  });

  return { volume, muted, volumeIcon, setVolume, toggle };
});
