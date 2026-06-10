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

// One short tone helper shared by the effects below.
function blip(
  ac: AudioContext,
  type: OscillatorType,
  freqStart: number,
  freqEnd: number,
  at: number,
  dur: number,
  peak = 0.12,
): void {
  const osc = ac.createOscillator();
  const gain = ac.createGain();
  osc.type = type;
  osc.frequency.setValueAtTime(freqStart, at);
  osc.frequency.exponentialRampToValueAtTime(freqEnd, at + dur);
  gain.gain.setValueAtTime(0.0001, at);
  gain.gain.exponentialRampToValueAtTime(peak, at + 0.01);
  gain.gain.exponentialRampToValueAtTime(0.0001, at + dur);
  osc.connect(gain).connect(ac.destination);
  osc.start(at);
  osc.stop(at + dur + 0.02);
}

export function useSkinSfx(): {
  glitch: () => void;
  cashRegister: () => void;
  stamp: () => void;
} {
  function glitch(): void {
    const ac = getCtx();
    if (!ac) return;
    void ac.resume?.();
    const now = ac.currentTime;
    // Downward sweep — short, retro "boop".
    blip(ac, "square", 880, 140, now, 0.18);
  }

  function cashRegister(): void {
    const ac = getCtx();
    if (!ac) return;
    void ac.resume?.();
    const now = ac.currentTime;
    // "Ka-ching": two bright bell-like notes + sparkle tail.
    blip(ac, "triangle", 1320, 1300, now, 0.1, 0.14);
    blip(ac, "triangle", 1760, 1740, now + 0.09, 0.18, 0.14);
    blip(ac, "sine", 2640, 3200, now + 0.16, 0.12, 0.06);
  }

  function stamp(): void {
    const ac = getCtx();
    if (!ac) return;
    void ac.resume?.();
    const now = ac.currentTime;
    // Low dull "thud" of a rubber stamp hitting paper.
    blip(ac, "sine", 220, 60, now, 0.12, 0.2);
  }

  return { glitch, cashRegister, stamp };
}
