import { defineStore } from "pinia";
import { computed, ref } from "vue";

import { useSoundsStore } from "./sounds";

export const SCHEDULER_MAX_MINUTES = 120;
export const SCHEDULER_MAX_ITEMS = 5;

const MAX_DELAY_MS = SCHEDULER_MAX_MINUTES * 60 * 1000;

export interface ScheduleItem {
  id: string;
  soundId: number;
  displayName: string;
  runAt: number; // epoch ms
}

let nextId = 0;
const timers = new Map<string, number>();

export const useSchedulerStore = defineStore("scheduler", () => {
  const items = ref<ScheduleItem[]>([]);
  const now = ref(Date.now());
  let ticker: number | null = null;

  const isFull = computed(() => items.value.length >= SCHEDULER_MAX_ITEMS);
  const sorted = computed(() =>
    [...items.value].sort((a, b) => a.runAt - b.runAt),
  );

  function startTicker(): void {
    if (ticker !== null) return;
    ticker = window.setInterval(() => {
      now.value = Date.now();
    }, 250);
  }

  function stopTicker(): void {
    if (ticker !== null) {
      window.clearInterval(ticker);
      ticker = null;
    }
  }

  function fire(itemId: string): void {
    const item = items.value.find((it) => it.id === itemId);
    if (!item) return;
    const soundId = item.soundId;
    cancel(itemId);
    const sounds = useSoundsStore();
    void sounds.play(soundId);
  }

  function schedule(soundId: number, displayName: string, delayMs: number): boolean {
    if (delayMs <= 0 || delayMs > MAX_DELAY_MS) return false;
    if (items.value.length >= SCHEDULER_MAX_ITEMS) return false;
    const id = `s-${++nextId}`;
    const runAt = Date.now() + delayMs;
    items.value = [...items.value, { id, soundId, displayName, runAt }];
    now.value = Date.now();
    startTicker();
    const handle = window.setTimeout(() => fire(id), delayMs);
    timers.set(id, handle);
    return true;
  }

  function cancel(itemId: string): void {
    const handle = timers.get(itemId);
    if (handle !== undefined) {
      window.clearTimeout(handle);
      timers.delete(itemId);
    }
    items.value = items.value.filter((it) => it.id !== itemId);
    if (items.value.length === 0) stopTicker();
  }

  function cancelAll(): void {
    for (const [, h] of timers) window.clearTimeout(h);
    timers.clear();
    items.value = [];
    stopTicker();
  }

  function remainingMs(item: ScheduleItem): number {
    return Math.max(0, item.runAt - now.value);
  }

  return {
    items,
    sorted,
    now,
    isFull,
    schedule,
    cancel,
    cancelAll,
    remainingMs,
  };
});
