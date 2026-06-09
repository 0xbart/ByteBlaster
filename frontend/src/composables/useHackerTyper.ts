// Hackertyper keystroke effect for the cyber skin: typing anywhere outside a
// real input spawns floating green glyphs near the cursor. Active only while
// skin === "cyber"; listeners are attached/detached on skin changes and torn
// down when the owning component unmounts.

import { onScopeDispose, watch } from "vue";
import { storeToRefs } from "pinia";
import { useThemeStore } from "@/stores/theme";

const SNIPPETS = [
  "0x1F",
  "sudo",
  "rm -rf",
  "01001",
  "ACCESS",
  "ping",
  "root@",
  "0xDEAD",
  "::1",
  "grep -r",
  "exec()",
  "<script>",
  "0b1010",
  "ssh",
  "kernel",
];

function isEditable(el: EventTarget | null): boolean {
  if (!(el instanceof HTMLElement)) return false;
  const tag = el.tagName;
  return (
    tag === "INPUT" ||
    tag === "TEXTAREA" ||
    tag === "SELECT" ||
    el.isContentEditable
  );
}

export function useHackerTyper(): void {
  const theme = useThemeStore();
  const { skin } = storeToRefs(theme);

  let mouseX = window.innerWidth / 2;
  let mouseY = window.innerHeight / 2;

  function onMove(e: MouseEvent): void {
    mouseX = e.clientX;
    mouseY = e.clientY;
  }

  function onKey(e: KeyboardEvent): void {
    // Don't interfere with typing into real fields or shortcut combos.
    if (isEditable(e.target) || e.metaKey || e.ctrlKey || e.altKey) return;
    if (e.key.length !== 1) return; // ignore Shift, Arrow, etc.

    const span = document.createElement("span");
    span.textContent =
      SNIPPETS[Math.floor(Math.random() * SNIPPETS.length)];
    span.className = "hacker-glyph";
    span.style.left = `${mouseX + (Math.random() * 40 - 20)}px`;
    span.style.top = `${mouseY + (Math.random() * 20 - 10)}px`;
    document.body.appendChild(span);
    setTimeout(() => span.remove(), 1000);
  }

  function attach(): void {
    window.addEventListener("keydown", onKey);
    window.addEventListener("mousemove", onMove);
  }
  function detach(): void {
    window.removeEventListener("keydown", onKey);
    window.removeEventListener("mousemove", onMove);
  }

  watch(
    skin,
    (s) => {
      detach();
      if (s === "cyber") attach();
    },
    { immediate: true },
  );

  onScopeDispose(detach);
}
