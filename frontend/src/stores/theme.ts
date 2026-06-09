import { defineStore } from "pinia";
import { computed, ref, watch } from "vue";

export type ThemeMode = "light" | "dark";
// Skins layer ON TOP of light/dark. "default" keeps the light/dark toggle and
// the untouched Bulma look; "cyber"/"pink" are full standalone looks scoped to
// [data-skin="..."] (see styles/cyber.css, styles/pink.css).
export type Skin = "default" | "cyber" | "pink";

const STORAGE_KEY = "byteblaster:theme";
const SKIN_KEY = "byteblaster:skin";

function detectInitial(): ThemeMode {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored === "light" || stored === "dark") return stored;
  // Honor the OS preference on first visit.
  return window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function detectInitialSkin(): Skin {
  const stored = localStorage.getItem(SKIN_KEY);
  if (stored === "cyber" || stored === "pink" || stored === "default") return stored;
  return "default";
}

function apply(mode: ThemeMode): void {
  // Bulma 1.x reads data-theme on <html>; setting it flips all CSS vars.
  document.documentElement.setAttribute("data-theme", mode);
}

function applySkin(skin: Skin): void {
  document.documentElement.setAttribute("data-skin", skin);
}

export const useThemeStore = defineStore("theme", () => {
  const mode = ref<ThemeMode>(detectInitial());
  apply(mode.value);

  const skin = ref<Skin>(detectInitialSkin());
  applySkin(skin.value);

  watch(mode, (m) => {
    localStorage.setItem(STORAGE_KEY, m);
    apply(m);
  });

  watch(skin, (s) => {
    localStorage.setItem(SKIN_KEY, s);
    applySkin(s);
  });

  const isDark = computed(() => mode.value === "dark");
  const isCyber = computed(() => skin.value === "cyber");

  function toggle(): void {
    mode.value = mode.value === "dark" ? "light" : "dark";
  }

  function setMode(m: ThemeMode): void {
    mode.value = m;
  }

  function setSkin(s: Skin): void {
    skin.value = s;
  }

  return { mode, skin, isDark, isCyber, toggle, setMode, setSkin };
});
