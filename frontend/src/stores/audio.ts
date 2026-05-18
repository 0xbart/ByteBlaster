import { defineStore } from "pinia";
import { ref, watch } from "vue";

const STORAGE_KEY = "byteblaster:muted";

export const useAudioStore = defineStore("audio", () => {
  const muted = ref<boolean>(localStorage.getItem(STORAGE_KEY) === "1");

  function toggle(): void {
    muted.value = !muted.value;
  }

  watch(muted, (v) => {
    localStorage.setItem(STORAGE_KEY, v ? "1" : "0");
  });

  return { muted, toggle };
});
