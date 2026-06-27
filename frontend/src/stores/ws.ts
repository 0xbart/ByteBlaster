import { defineStore } from "pinia";
import { ref } from "vue";

import type { ThemeMode, Skin } from "@/stores/theme";

// Bridges components to the single WebSocket owned by useWebSocket(). The
// composable registers its send function on mount; components send through here
// instead of opening their own socket.
export const useWsStore = defineStore("ws", () => {
  const sender = ref<((payload: unknown) => boolean) | null>(null);

  function register(fn: ((payload: unknown) => boolean) | null): void {
    sender.value = fn;
  }

  // Superadmin-only on the backend; pushes a theme override to one user.
  function setUserTheme(
    targetUserId: number,
    mode: ThemeMode,
    skin: Skin,
  ): boolean {
    return (
      sender.value?.({
        type: "set_theme",
        target_user_id: targetUserId,
        mode,
        skin,
      }) ?? false
    );
  }

  // React to a recent play; backend ignores it outside the voting window.
  function sendVote(playId: number, direction: "up" | "down"): boolean {
    return sender.value?.({ type: "vote", play_id: playId, direction }) ?? false;
  }

  return { register, setUserTheme, sendVote };
});
