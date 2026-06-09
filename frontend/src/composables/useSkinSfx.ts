// Tiny WebAudio "glitch" blip played on skin switch — no asset file.
// One shared AudioContext, lazily created on first use (after a user gesture,
// which a click on the skin selector provides).

let ctx: AudioContext | null = null;

function getCtx(): AudioContext | null {
  if (typeof window === "undefined") return null;
  if (!ctx) {
    const Ctor =
      window.AudioContext ??
      (window as unknown as { webkitAudioContext?: typeof AudioContext })
        .webkitAudioContext;
    if (!Ctor) return null;
    ctx = new Ctor();
  }
  return ctx;
}

export function useSkinSfx(): { glitch: () => void } {
  function glitch(): void {
    const ac = getCtx();
    if (!ac) return;
    void ac.resume?.();
    const now = ac.currentTime;

    const osc = ac.createOscillator();
    const gain = ac.createGain();
    osc.type = "square";
    // Downward sweep — short, retro "boop".
    osc.frequency.setValueAtTime(880, now);
    osc.frequency.exponentialRampToValueAtTime(140, now + 0.18);
    gain.gain.setValueAtTime(0.0001, now);
    gain.gain.exponentialRampToValueAtTime(0.12, now + 0.01);
    gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.2);

    osc.connect(gain).connect(ac.destination);
    osc.start(now);
    osc.stop(now + 0.22);
  }

  return { glitch };
}
