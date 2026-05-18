import { defineStore } from "pinia";
import { computed, ref, watch } from "vue";

export type ThemeMode = "light" | "dark";

const STORAGE_KEY = "byteblaster:theme";

function detectInitial(): ThemeMode {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored === "light" || stored === "dark") return stored;
  // Honor the OS preference on first visit.
  return window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function apply(mode: ThemeMode): void {
  // Bulma 1.x reads data-theme on <html>; setting it flips all CSS vars.
  document.documentElement.setAttribute("data-theme", mode);
}

export const useThemeStore = defineStore("theme", () => {
  const mode = ref<ThemeMode>(detectInitial());
  apply(mode.value);

  watch(mode, (m) => {
    localStorage.setItem(STORAGE_KEY, m);
    apply(m);
  });

  const isDark = computed(() => mode.value === "dark");

  function toggle(): void {
    mode.value = mode.value === "dark" ? "light" : "dark";
  }

  return { mode, isDark, toggle };
});
