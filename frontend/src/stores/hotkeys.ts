import { defineStore } from "pinia";
import { ref, watch } from "vue";

import { useSoundsStore } from "@/stores/sounds";

// Personal "quick slots": map a number key (1-0) to a sound id. Stored locally
// like theme/volume/party — these bindings are per-device (IP-auth ties a user
// to a device anyway). The key is the digit char as typed ("1".."9","0").
export const DIGITS = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"] as const;
export type Digit = (typeof DIGITS)[number];

const STORAGE_KEY = "byteblaster:hotkeys";

function detectInitial(): Record<string, number> {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return {};
    const parsed = JSON.parse(raw) as unknown;
    if (!parsed || typeof parsed !== "object") return {};
    const out: Record<string, number> = {};
    for (const d of DIGITS) {
      const v = (parsed as Record<string, unknown>)[d];
      if (typeof v === "number" && Number.isInteger(v)) out[d] = v;
    }
    return out;
  } catch {
    return {};
  }
}

export const useHotkeysStore = defineStore("hotkeys", () => {
  const slots = ref<Record<string, number>>(detectInitial());
  // Quick-bind mode: armed by pressing "f"; next sound click opens the bind dialog.
  const armed = ref(false);

  watch(
    slots,
    (s) => localStorage.setItem(STORAGE_KEY, JSON.stringify(s)),
    { deep: true },
  );

  function getSlot(digit: string): number | null {
    return slots.value[digit] ?? null;
  }

  function setSlot(digit: string, soundId: number): void {
    slots.value = { ...slots.value, [digit]: soundId };
  }

  function clearSlot(digit: string): void {
    const next = { ...slots.value };
    delete next[digit];
    slots.value = next;
  }

  function arm(): void {
    armed.value = true;
  }

  function disarm(): void {
    armed.value = false;
  }

  function toggleArm(): void {
    armed.value = !armed.value;
  }

  function playSlot(digit: string): void {
    const id = slots.value[digit];
    if (id == null) return;
    const sounds = useSoundsStore();
    // Drop dangling bindings (sound deleted since binding).
    if (!sounds.sounds.some((s) => s.id === id)) {
      clearSlot(digit);
      return;
    }
    void sounds.play(id);
  }

  return {
    slots,
    armed,
    getSlot,
    setSlot,
    clearSlot,
    arm,
    disarm,
    toggleArm,
    playSlot,
  };
});
