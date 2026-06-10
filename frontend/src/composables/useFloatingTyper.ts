// Generic "type anywhere → floating glyph near the cursor" effect, shared by
// the skin-specific typers (cyber/money/government). Active only while the
// current skin matches `activeSkin`; listeners attach/detach on skin changes
// and tear down when the owning scope is disposed.

import { onScopeDispose, watch } from "vue";
import { storeToRefs } from "pinia";
import { useThemeStore, type Skin } from "@/stores/theme";

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

export function useFloatingTyper(
  activeSkin: Skin,
  snippets: string[],
  className: string,
): void {
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
    span.textContent = snippets[Math.floor(Math.random() * snippets.length)];
    span.className = className;
    span.style.left = `${mouseX + (Math.random() * 40 - 20)}px`;
    span.style.top = `${mouseY + (Math.random() * 20 - 10)}px`;
    document.body.appendChild(span);
    setTimeout(() => span.remove(), 1100);
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
      if (s === activeSkin) attach();
    },
    { immediate: true },
  );

  onScopeDispose(detach);
}
