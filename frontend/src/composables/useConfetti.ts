import confetti from "canvas-confetti";

export function celebrate(): void {
  void confetti({
    particleCount: 80,
    spread: 70,
    origin: { y: 0.7 },
    zIndex: 30,
    disableForReducedMotion: true,
  });
}
