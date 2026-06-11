// Ephemeral "someone voted" feedback: a thumbs glyph + username drifts up and
// fades, then removes itself. Uses the Web Animations API so no global CSS is
// needed (mirrors the spirit of useFloatingTyper / useBalloons).

import type { VoteDirection } from "@/stores/votes";

export function floatVote(direction: VoteDirection, username: string): void {
  if (typeof document === "undefined") return;

  const el = document.createElement("div");
  el.textContent = `${direction === "up" ? "👍" : "👎"} ${username}`;
  Object.assign(el.style, {
    position: "fixed",
    left: `${30 + Math.random() * 40}%`,
    bottom: "5.5rem",
    zIndex: "25",
    pointerEvents: "none",
    fontSize: "0.95rem",
    fontWeight: "600",
    whiteSpace: "nowrap",
    color: direction === "up" ? "#2e9e5b" : "#d14",
    textShadow: "0 1px 2px rgba(0,0,0,0.25)",
  } satisfies Partial<CSSStyleDeclaration>);
  document.body.appendChild(el);

  const reduce = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
  const anim = el.animate(
    [
      { transform: "translateY(0) scale(0.9)", opacity: 0 },
      { transform: "translateY(-12px) scale(1)", opacity: 1, offset: 0.15 },
      { transform: "translateY(-70px) scale(1)", opacity: 0 },
    ],
    { duration: reduce ? 1200 : 2400, easing: "ease-out" },
  );
  anim.onfinish = () => el.remove();
  anim.oncancel = () => el.remove();
}
