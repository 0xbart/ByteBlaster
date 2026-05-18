// Plays audio URLs concurrently using a small pool of HTMLAudioElement objects.
// New plays don't interrupt sounds already playing.

const POOL_SIZE = 8;
const pool: HTMLAudioElement[] = [];
let cursor = 0;

function getElement(): HTMLAudioElement {
  if (pool.length < POOL_SIZE) {
    const el = new Audio();
    pool.push(el);
    return el;
  }
  // Prefer an idle (ended/paused) element; otherwise round-robin.
  const idle = pool.find((el) => el.paused || el.ended);
  if (idle) return idle;
  const el = pool[cursor % POOL_SIZE];
  cursor = (cursor + 1) % POOL_SIZE;
  return el;
}

export function useAudioPlayer() {
  function play(url: string): void {
    const el = getElement();
    el.src = url;
    el.currentTime = 0;
    // Browser autoplay policy: the first user gesture unlocks playback.
    // After ClaimUsernameDialog confirm or any button click, this works.
    void el.play().catch((err) => {
      // eslint-disable-next-line no-console
      console.warn("Audio play blocked or failed:", err);
    });
  }

  return { play };
}
