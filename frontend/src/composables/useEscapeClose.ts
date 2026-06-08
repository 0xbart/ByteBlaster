import { onBeforeUnmount, onMounted } from "vue";

export function useEscapeClose(callback: () => void): void {
  function onKey(ev: KeyboardEvent): void {
    if (ev.key !== "Escape") return;
    ev.stopPropagation();
    callback();
  }
  onMounted(() => window.addEventListener("keydown", onKey));
  onBeforeUnmount(() => window.removeEventListener("keydown", onKey));
}
