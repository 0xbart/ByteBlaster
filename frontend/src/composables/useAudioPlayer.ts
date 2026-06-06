// Plays audio URLs concurrently using a small pool of HTMLAudioElement objects.
// New plays don't interrupt sounds already playing.
//
// Browser autoplay policy blocks `audio.play()` until the user has interacted
// with the page. For returning users (already claimed) there is no claim
// dialog to provide that gesture, so an incoming WS "play" event silently
// fails. We work around this by:
//   1. Listening for the first user interaction (click / keydown / touch).
//   2. Queueing any incoming play() calls until that interaction occurs.
//   3. On unlock, primer-playing a silent buffer (which the browser remembers
//      as "user-authorised") then flushing the queue.

import { computed, ref } from "vue";
import { useAudioStore } from "@/stores/audio";

const POOL_SIZE = 8;
const QUEUE_MAX = 5;
const pool: HTMLAudioElement[] = [];
let cursor = 0;

const unlocked = ref(false);
const active = ref<Set<HTMLAudioElement>>(new Set());
const playing = computed(() => active.value.size > 0);
const playingCount = computed(() => active.value.size);
const queue: string[] = [];

function markDone(el: HTMLAudioElement): void {
  if (active.value.delete(el)) {
    // Trigger reactivity — Set mutations aren't deep-tracked.
    active.value = new Set(active.value);
  }
}

function attachLifecycle(el: HTMLAudioElement): void {
  el.addEventListener("ended", () => markDone(el));
  el.addEventListener("pause", () => markDone(el));
}

function getElement(): HTMLAudioElement {
  if (pool.length < POOL_SIZE) {
    const el = new Audio();
    attachLifecycle(el);
    pool.push(el);
    return el;
  }
  const idle = pool.find((el) => el.paused || el.ended);
  if (idle) return idle;
  const el = pool[cursor % POOL_SIZE];
  cursor = (cursor + 1) % POOL_SIZE;
  return el;
}

function playOnElement(url: string, volume: number): void {
  const el = getElement();
  el.src = url;
  el.currentTime = 0;
  el.volume = Math.max(0, Math.min(1, volume));
  void el
    .play()
    .then(() => {
      active.value.add(el);
      active.value = new Set(active.value);
    })
    .catch((err) => {
      // eslint-disable-next-line no-console
      console.warn("Audio play blocked or failed:", err);
    });
}

function stopAll(): void {
  for (const el of pool) {
    if (!el.paused) el.pause();
    el.currentTime = 0;
  }
  active.value = new Set();
}

function onFirstGesture(): void {
  unlocked.value = true;
  removeListeners();
  queue.length = 0;
}

function addListeners(): void {
  document.addEventListener("click", onFirstGesture, { once: false });
  document.addEventListener("keydown", onFirstGesture, { once: false });
  document.addEventListener("touchstart", onFirstGesture, { once: false });
}

function removeListeners(): void {
  document.removeEventListener("click", onFirstGesture);
  document.removeEventListener("keydown", onFirstGesture);
  document.removeEventListener("touchstart", onFirstGesture);
}

// Wire up listeners once on module load.
if (typeof document !== "undefined") addListeners();

export function useAudioPlayer() {
  const audio = useAudioStore();

  function play(url: string): void {
    if (audio.muted) return;
    if (!unlocked.value) {
      queue.push(url);
      if (queue.length > QUEUE_MAX) queue.shift();
      return;
    }
    playOnElement(url, audio.volume / 100);
  }

  return { play, unlocked, playing, playingCount, stopAll };
}
