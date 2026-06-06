import { defineStore } from "pinia";
import { ref, watch } from "vue";

const STORAGE_KEY = "byteblaster:party";

export const usePartyStore = defineStore("party", () => {
  const active = ref<boolean>(localStorage.getItem(STORAGE_KEY) === "1");

  function toggle(): void {
    active.value = !active.value;
  }

  watch(active, (v) => {
    localStorage.setItem(STORAGE_KEY, v ? "1" : "0");
  });

  return { active, toggle };
});
