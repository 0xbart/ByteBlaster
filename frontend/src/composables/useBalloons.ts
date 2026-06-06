const COLORS = ["#ff6b6b", "#ffd93d", "#6bcb77", "#4d96ff", "#c780ff", "#ff9ed8"];
const STAGE_ID = "party-balloon-stage";

function ensureStage(): HTMLElement {
  let el = document.getElementById(STAGE_ID);
  if (el) return el;
  el = document.createElement("div");
  el.id = STAGE_ID;
  el.className = "balloon-stage";
  document.body.appendChild(el);
  return el;
}

export function releaseBalloons(count = 8): void {
  if (typeof window === "undefined") return;
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  const stage = ensureStage();
  for (let i = 0; i < count; i++) {
    const b = document.createElement("div");
    b.className = "balloon";
    b.style.left = `${5 + Math.random() * 90}%`;
    b.style.background = COLORS[Math.floor(Math.random() * COLORS.length)];
    b.style.animationDuration = `${5 + Math.random() * 3}s`;
    b.style.animationDelay = `${Math.random() * 0.5}s`;
    stage.appendChild(b);
    window.setTimeout(() => b.remove(), 9000);
  }
}
